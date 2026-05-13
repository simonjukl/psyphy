# library(here)
library(ggplot2)
# library(igraph)

sim_results <- readr::read_rds(here::here("simulation/sim_results.rds"))

max_lattice_edges <- 24L # 4x4 undirected cardinal

# Plot a sample graph ---------------------------------------------------------

# source(here("utils.R"))

# sim_results |>
#   filter(!is.na(n_paths)) |>
#   slice_sample(n = 1) |>
#   plot_row()

# glimpse(sim_results)

# theme_set(
#   theme_minimal(base_size = 14) +
#     theme(
#       panel.grid.minor = element_blank(),
#       plot.title = element_text(face = "bold")
#     )
# )

# 1. n_paths distribution by target -------------------------------------------

sim_results |>
  dplyr::filter(!is.na(n_paths)) |>
  ggplot(aes(x = factor(target_n_paths), fill = factor(n_paths))) +
  geom_bar(position = "fill") +
  scale_fill_brewer(palette = "Set3", name = "n_paths") +
  labs(
    title = "Path count distribution by target",
    x = "Target n_paths",
    y = "Proportion"
  )


# 2. n_edges distribution by target --------------------------------------------

sim_results |>
  dplyr::filter(!is.na(n_paths)) |>
  ggplot(aes(x = n_edges, fill = factor(target_n_paths))) +
  geom_histogram(binwidth = 1, position = "stack") +
  scale_fill_brewer(palette = "Set3", name = "target") +
  scale_x_continuous(breaks = scales::breaks_width(1)) +
  labs(
    title = "Edge count distribution by target n_paths",
    x = "n_edges",
    y = "Count"
  )


# 3. n_loops vs n_paths -------------------------------------------------------

sim_results |>
  dplyr::filter(!is.na(n_paths)) |>
  ggplot(aes(x = n_loops, y = n_paths, colour = factor(n_edges))) +
  geom_jitter(width = 0.2, height = 0.2, alpha = 0.4, size = 1, shape = 1) +
  stat_summary(
    aes(group = n_loops),
    fun = mean,
    geom = "point",
    size = 3,
    colour = "#C44E52"
  ) +
  scale_x_continuous(breaks = 0:12) +
  labs(
    title = "Paths vs. loops",
    x = "n_loops",
    y = "n_paths",
    colour = "target"
  )


# 4. n_edges vs n_paths (scatter) ---------------------------------------------

sim_results |>
  dplyr::filter(!is.na(n_paths)) |>
  ggplot(aes(x = n_edges, y = n_paths, color = factor(n_loops))) +
  geom_jitter(width = 0.3, height = 0.2, alpha = 0.3, size = 1) +
  stat_summary(fun = mean, geom = "line", linewidth = 1, colour = "#4C72B0") +
  stat_summary(fun = mean, geom = "point", size = 3, colour = "#4C72B0") +
  scale_x_continuous(breaks = scales::breaks_width(1)) +
  labs(title = "Paths vs edge count", x = "n_edges", y = "n_paths")
