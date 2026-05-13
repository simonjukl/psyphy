library(tidyverse)


# standardize ------------------------------------------------------------
# adapted from rethinking::standardize
# stores scaling values as attributes for future unstandardizing

standardize <- function(x) {
  z <- (x - mean(x, na.rm = TRUE)) / sd(x, na.rm = TRUE)
  attr(z, "scaled:center") <- mean(x, na.rm = TRUE)
  attr(z, "scaled:scale") <- sd(x, na.rm = TRUE)
  z
}

unstandardize <- function(x) {
  as.numeric(x * attr(x, "scaled:scale") + attr(x, "scaled:center"))
}


# fit_or_load ------------------------------------------------------------
# if fit already present, load it, otherwise fit the model
# uses qs2 package for more compact saving format
# (qs2 save method should be implemented into cmdstanr in the future)

fit_or_load <- function(model, data, dir, ..., refit = FALSE) {
  if (!dir.exists(dir)) {
    dir.create(dir, recursive = TRUE)
  }

  path <- file.path(dir, "fit.qs2")

  if (file.exists(path) && !refit) {
    return(qs2::qs_read(path))
  }

  fit <- model$sample(data = data, output_dir = dir, ...)
  # copied from fit$save_object()
  fit$draws()
  try(fit$sampler_diagnostics(), silent = TRUE)
  try(fit$init(), silent = TRUE)
  try(fit$profiles(), silent = TRUE)
  qs2::qs_save(fit, path)
  fit
}


# parse_edges ------------------------------------------------------------
# parse edges string from experiment csv into an igraph edge-list matrix
# coordinate format: [((x1,y1),(x2,y2)), ...], 0-indexed (col, row).
# node ids are 1-indexed row-major: id = col + row * width + 1.
parse_edges <- function(edges_str, width = 4L) {
  pairs <- str_extract_all(
    edges_str,
    "\\(\\(\\d+,\\s*\\d+\\),\\s*\\(\\d+,\\s*\\d+\\)\\)"
  )[[1]]
  coords <- str_match(
    pairs,
    "\\((\\d+),\\s*(\\d+)\\),\\s*\\((\\d+),\\s*(\\d+)\\)"
  )
  # csv format is (row, col) from Python — node ID is col + row * width + 1
  node <- function(row, col) as.integer(col) + as.integer(row) * width + 1L
  matrix(
    c(node(coords[, 2], coords[, 3]), node(coords[, 4], coords[, 5])),
    ncol = 2
  )
}


# as_plot_row ------------------------------------------------------------
# prepare a single row for plot_row by adding the columns it needs
# assumes a 4x4 undirected grid
as_plot_row <- function(row) {
  row |>
    mutate(
      edge_list = map(edges, parse_edges),
      dims = list(c(4L, 4L))
    )
}


# plot_row ---------------------------------------------------------------
# plot a single row from sim_results or real data (via as_plot_row)
# show_labels = TRUE shows node numbers
# arrows = TRUE draws arrowheads
plot_row <- function(
  row,
  show_labels = FALSE,
  arrows = TRUE,
  ...
) {
  el <- row$edge_list[[1L]]
  dims <- row$dims[[1L]]
  n_nodes <- dims[1L] * dims[2L]
  g <- igraph::graph_from_edgelist(el, directed = FALSE)

  coords <- matrix(
    c(
      rep(seq_len(dims[1L]) - 1L, times = dims[2L]),
      -rep(seq_len(dims[2L]) - 1L, each = dims[1L])
    ),
    ncol = 2L
  )

  vcol <- rep("grey80", n_nodes)
  vcol[row$start_node] <- "#4CAF50"
  vcol[row$end_node] <- "#F44336"

  ecol <- rep("#444444", igraph::ecount(g))

  igraph::plot.igraph(
    g,
    layout = coords,
    vertex.size = 26,
    vertex.color = vcol,
    vertex.frame.color = "#555555",
    vertex.label = if (show_labels) seq_len(n_nodes) else NA,
    vertex.label.cex = 0.9,
    vertex.label.color = "black",
    edge.color = ecol,
    edge.width = 2,
    edge.curved = 0,
    edge.arrow.size = if (arrows) 0.5 else 0,
    edge.arrow.mode = if (arrows) 3L else 0L,
    ...
  )
}


# kable_apa --------------------------------------------------------------
# nicely formatted kable
kable_apa <- function(x, ...) {
  kableExtra::kbl(
    x,
    align = c("l", rep("c", ncol(x) - 1)),
    booktabs = TRUE,
    digits = 2
  ) |>
    kable_styling(
      position = "left",
      full_width = FALSE,
      latex_options = 'HOLD_position'
    )
}
