# computes coordinates of start and end node for each possible configuration
start_end_pair <- function(dims, type = c("h1", "h2", "v1", "v2")) {
  type <- rlang::arg_match(type)
  x <- dims[1L]
  y <- dims[2L]
  switch(
    type,
    h1 = c(2L, x * y - 1L),
    h2 = c(x - 1L, x * (y - 1L) + 2L),
    v1 = c(x + 1L, x * (y - 1L)),
    v2 = c(x * (y - 2L) + 1L, 2L * x)
  )
}


# creates a edge matrix of all possible pairs of adjacent nodes in a lattice graph
lattice_pairs <- function(dims) {
  x <- dims[1L]
  y <- dims[2L]
  node <- function(r, c) (r - 1L) * x + c
  pairs <- list()
  for (r in seq_len(y)) {
    for (c in seq_len(x)) {
      if (c < x) {
        pairs <- c(pairs, list(c(node(r, c), node(r, c + 1L))))
      }
      if (r < y) pairs <- c(pairs, list(c(node(r, c), node(r + 1L, c))))
    }
  }
  do.call(rbind, pairs)
}


# from an edge matrix created by lattice_pairs, this creates a nested adjacency list
# e.g. adj[[1]]: [{nb=2, eid=1}]          node 1 connects to node 2 via edge 1
build_adj <- function(edge_mat, n_nodes) {
  adj <- vector("list", n_nodes)
  for (i in seq_len(n_nodes)) {
    adj[[i]] <- list()
  }
  for (eid in seq_len(nrow(edge_mat))) {
    u <- edge_mat[eid, 1L]
    v <- edge_mat[eid, 2L]
    adj[[u]] <- c(adj[[u]], list(list(nb = v, eid = eid)))
    adj[[v]] <- c(adj[[v]], list(list(nb = u, eid = eid)))
  }
  adj
}


# counts all paths using DFS
# early_stop used for selecting graphs with more than target n_paths
count_paths <- function(adj, start, end, n_nodes, early_stop = NULL) {
  count <- 0L
  # integer division - each edge appears twice
  used <- logical(sum(lengths(adj)) %/% 2L)
  # depth-first search
  dfs <- function(node) {
    if (node == end) {
      count <<- count + 1L
      if (!is.null(early_stop) && count > early_stop) {
        return(TRUE)
      }
      return(FALSE)
    }
    for (i in seq_along(adj[[node]])) {
      nb <- adj[[node]][[i]]$nb
      eid <- adj[[node]][[i]]$eid
      if (!used[[eid]]) {
        used[[eid]] <<- TRUE
        if (dfs(nb)) {
          return(TRUE)
        }
        used[[eid]] <<- FALSE
      }
    }
    FALSE
  }
  dfs(start)
  count
}


# checks if all nodes can be reached from node 1
is_connected_mat <- function(edge_mat, n_nodes) {
  if (nrow(edge_mat) == 0L) {
    return(n_nodes <= 1L)
  }
  adj <- vector("list", n_nodes)
  for (i in seq_len(nrow(edge_mat))) {
    u <- edge_mat[i, 1L]
    v <- edge_mat[i, 2L]
    adj[[u]] <- c(adj[[u]], v)
    adj[[v]] <- c(adj[[v]], u)
  }
  visited <- logical(n_nodes)
  stack <- 1L
  while (length(stack)) {
    n <- stack[[length(stack)]]
    stack <- stack[-length(stack)]
    if (!visited[[n]]) {
      visited[[n]] <- TRUE
      stack <- c(stack, adj[[n]])
    }
  }
  all(visited)
}


# generates undirected connected graph
generate_graph <- function(
  dims = c(4L, 4L),
  n_edges_min = 15L,
  n_edges_max = 21L,
  target_n_paths = NULL, # NULL = unconstrained
  pair_type = NULL, # NULL = sample each attempt
  max_attempts = 5000L
) {
  all_pairs <- lattice_pairs(dims)
  n_nodes <- dims[1L] * dims[2L]
  coords <- matrix(
    c(
      rep(seq(0, dims[1L] - 1L), times = dims[2L]),
      rep(seq(0, -(dims[2L] - 1L)), each = dims[1L])
    ),
    ncol = 2L,
    dimnames = list(NULL, c("x", "y"))
  )

  if (!is.null(pair_type)) {
    pair_type <- rlang::arg_match(pair_type, c("h1", "h2", "v1", "v2"))
  }

  for (attempt in seq_len(max_attempts)) {
    pt <- if (is.null(pair_type)) {
      sample(c("h1", "h2", "v1", "v2"), 1L)
    } else {
      pair_type
    }
    pair <- start_end_pair(dims, pt)
    start <- pair[1L]
    end <- pair[2L]

    n_e <- sample(n_edges_min:n_edges_max, 1L)
    chosen <- all_pairs[sample(nrow(all_pairs), n_e), , drop = FALSE]

    if (!is_connected_mat(chosen, n_nodes)) {
      next
    }

    adj <- build_adj(chosen, n_nodes)
    n_paths <- count_paths(
      adj,
      start,
      end,
      n_nodes,
      early_stop = target_n_paths
    )

    if (!is.null(target_n_paths) && n_paths != target_n_paths) {
      next
    }

    n_loops <- nrow(chosen) - n_nodes + 1

    return(list(
      edge_list = chosen,
      coords = coords,
      dims = dims,
      pair_type = pt,
      start = start,
      end = end,
      n_nodes = n_nodes,
      n_edges = nrow(chosen),
      n_loops = n_loops,
      n_paths = n_paths
    ))
  }

  stop(
    "Failed after ",
    max_attempts,
    " attempts — adjust n_edges range or target_n_paths."
  )
}
