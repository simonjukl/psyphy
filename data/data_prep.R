library(assertthat)

d_raw <-
  here::here("data/raw") |>
  list.files(full.names = TRUE) |>
  purrr::set_names(\(x) stringr::str_extract(basename(x), "^[^_]+")) |>
  purrr::map(\(f) {
    readr::read_csv(f, col_types = "c", show_col_types = FALSE)
  }) |>
  # first participant completed the experiment twice
  purrr::list_rbind(names_to = "id") |>
  dplyr::select(!pid)

d <-
  d_raw |>
  dplyr::rename(
    n_loops = cyclomatic,
    n_edges = edge_count,
    duration = stim_time
  ) |>
  tidyr::separate_wider_regex(
    c(start, end),
    c("\\(", "row" = "\\d", ",\\s", "col" = "\\d", "\\)"),
    names_sep = "_",
    cols_remove = TRUE
  ) |>
  dplyr::mutate(
    dplyr::across(tidyr::ends_with(c("_row", "_col")), as.integer),
    start_node = as.integer(start_col + start_row * 4L + 1L),
    end_node = as.integer(end_col + end_row * 4L + 1L),
    correct = dplyr::if_else(response == n_paths, 1L, 0L)
  ) |>
  dplyr::select(!tidyr::ends_with(c("_row", "_col")))


assert_that(all(d$block %in% c("practice", 1:3)))
assert_that(all(between(d$n_edges, 15, 19)))
# in 4x4 graph with no diagonal edges, no more han 9 simple loops can exist
# based on generation constraints, max 4 loops can exist
assert_that(all(between(d$n_loops, 0, 4)))
assert_that(all(d$duration %in% c(1, 3, 5)))
assert_that(all(d$n_paths %in% 1:7))
assert_that(all(is.numeric(d$response)))
assert_that(all(is.numeric(d$rt)))


readr::write_csv(d, here::here("data/clean/data_clean.csv"))
