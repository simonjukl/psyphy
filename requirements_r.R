packages <- c(
  # check that session is clean before running R scripts
  "sessioncheck",
  # relative file paths
  "here",

  "tidyverse",

  # plots
  "scales",

  # data checks
  "assertthat",

  # graph generation and plots
  "igraph",

  # file compression format
  # (better than .rds for large files like model fits)
  "qs2",

  # parallelization
  "futurize",
  "future",

  # progress bar
  "progressify",
  "progressr",

  # time tracking
  "tictoc",

  # beep
  "beepr",

  # bayesian modeling

  ## also need to run install_cmdstan()
  ## see https://mc-stan.org/cmdstanr/articles/cmdstanr.html
  "cmdstanr",

  "brms",
  "tidybayes",
  "posterior",
  "bayesplot",

  ## prior sensitivity checks
  "priorsense"
)

# package installer
# https://pak.r-lib.org/
# install.packages("pak")

# pak::pak(packages)
