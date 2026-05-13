# library(here)
# library(dplyr)
# library(tidyr)
# library(purrr)
# library(futurize)
# library(progressify)
# library(tictoc)
# library(beepr)

# graph generation code
source(here::here("simulation/generate.R"))

# progressify - show progress bar
progressr::handlers(global = TRUE)
# parallel processing
future::plan(multisession, workers = 8)

# Simulation parameters -------------------------------------------------------

dims <- c(4L, 4L)
n_edges_min <- 15L
n_edges_max <- 19L
target_n_paths <- 1:7
n_reps <- 200L
max_attempts <- 5000L
seed <- 42L

# play sound at the end of the simulation
sound <- TRUE

# Run -------------------------------------------------------------------------

set.seed(seed)

conditions <- tidyr::expand_grid(
  target_n_paths = target_n_paths,
  rep = seq_len(n_reps)
)

tictoc::tic()

sim_results <- conditions |>
  dplyr::mutate(
    result = purrr::map(seq_len(n()), \(i) {
      g <- tryCatch(
        generate_graph(
          dims = dims,
          n_edges_min = n_edges_min,
          n_edges_max = n_edges_max,
          target_n_paths = conditions$target_n_paths[[i]],
          pair_type = NULL,
          max_attempts = max_attempts
        ),
        error = \(e) {
          message(
            "generate_graph failed [target=",
            conditions$target_n_paths[[i]],
            " rep=",
            conditions$rep[[i]],
            "]: ",
            conditionMessage(e)
          )
          NULL
        }
      )
      if (is.null(g)) {
        return(tibble(
          pair_type = NA_character_,
          start_node = NA_integer_,
          end_node = NA_integer_,
          n_edges = NA_integer_,
          n_loops = NA_integer_,
          n_paths = NA_integer_,
          edge_list = list(matrix(integer(0), ncol = 2L))
        ))
      }
      tibble::tibble(
        pair_type = g$pair_type,
        start_node = g$start,
        end_node = g$end,
        n_edges = g$n_edges,
        n_loops = g$n_loops,
        n_paths = g$n_paths,
        edge_list = list(g$edge_list)
      )
    }) |>
      futurize::futurize(seed = TRUE) |>
      progressify::progressify()
  ) |>
  tidyr::unnest(result)

tictoc::toc()

if (sound) {
  beepr::beep(2)
}

future::plan(sequential)

sim_results

readr::write_rds(sim_results, here("simulation/sim_results.rds"))
