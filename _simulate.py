"""
Simulate 5 participants and write data CSVs identical in format to real experiment output.
Run with: python _simulate.py
"""

import os, csv, random
from datetime import datetime, timedelta
from collections import defaultdict

# ── Mirror of exp.py constants ────────────────────────────────
GRID_SIZE        = 4
EDGE_COUNT_MIN   = 15
EDGE_COUNT_MAX   = 19
PATH_COUNTS      = [1, 2, 3, 4, 5, 6]
STIM_TIMES       = [2, 3.5, 5]
TRIALS_PER_BLOCK = 54
PRACTICE_TRIALS  = 10
PRACTICE_STIM    = 3.5
RESPONSE_WINDOW  = 5.0
OUTPUT_DIR       = 'data'
NODE_PAIRS = [
    ((0, 1), (3, 2)),  # top ↔ bottom, shifted column
    ((0, 2), (3, 1)),  # top ↔ bottom, shifted column
    ((1, 0), (2, 3)),  # left ↔ right, shifted row
    ((2, 0), (1, 3)),  # left ↔ right, shifted row
]

# ── Graph functions (copied from exp.py, no PsychoPy) ────────

def _all_pairs():
    pairs = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if c + 1 < GRID_SIZE:
                pairs.append(((r, c), (r, c + 1)))
            if r + 1 < GRID_SIZE:
                pairs.append(((r, c), (r + 1, c)))
    return pairs

def _pairs_to_edges(pairs):
    edges = []
    for u, v in pairs:
        edges.append((u, v))
        edges.append((v, u))
    return edges

def _has_path(edges, src, dst):
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
    seen, stack = set(), [src]
    while stack:
        n = stack.pop()
        if n == dst:
            return True
        if n not in seen:
            seen.add(n)
            stack.extend(adj[n])
    return False

def _is_connected(edges):
    all_nodes = {(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)}
    adj = defaultdict(set)
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    if not all_nodes.issubset(adj.keys()):
        return False
    visited, stack = set(), [next(iter(all_nodes))]
    while stack:
        n = stack.pop()
        if n not in visited:
            visited.add(n)
            stack.extend(adj[n])
    return visited == all_nodes

def _canonical(a, b):
    return (a, b) if a < b else (b, a)

def cyclomatic_number(edges):
    if not edges:
        return 0
    nodes, undirected = set(), set()
    for u, v in edges:
        nodes.add(u); nodes.add(v)
        undirected.add(_canonical(u, v))
    e, v_count = len(undirected), len(nodes)
    adj = defaultdict(set)
    for a, b in undirected:
        adj[a].add(b); adj[b].add(a)
    visited, c = set(), 0
    for node in nodes:
        if node not in visited:
            c += 1
            stack = [node]
            while stack:
                n = stack.pop()
                if n not in visited:
                    visited.add(n)
                    stack.extend(adj[n])
    return e - v_count + c

def count_trails(edges, start, end, limit=None):
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
    count = [0]
    done  = [False]

    def dfs(n, used):
        if done[0]:
            return
        if n == end:
            count[0] += 1
            if limit is not None and count[0] > limit:
                done[0] = True
            return
        for m in adj[n]:
            if done[0]:
                return
            k = _canonical(n, m)
            if k not in used:
                used.add(k)
                dfs(m, used)
                used.remove(k)

    dfs(start, set())
    return count[0]

def make_trail_graph(target, start, end, max_attempts=8000):
    all_pairs = _all_pairs()
    for _ in range(max_attempts):
        n_edges = random.randint(EDGE_COUNT_MIN, EDGE_COUNT_MAX)
        sampled = random.sample(all_pairs, n_edges)
        edges   = _pairs_to_edges(sampled)
        if not _is_connected(edges):
            continue
        if not _has_path(edges, start, end):
            continue
        if count_trails(edges, start, end, limit=target + 1) == target:
            return edges
    return None

def make_trial_list(n):
    n_per_t = n // len(STIM_TIMES)
    times   = STIM_TIMES * n_per_t + random.choices(STIM_TIMES, k=n % len(STIM_TIMES))
    n_per_p = n // len(PATH_COUNTS)
    paths   = PATH_COUNTS * n_per_p + random.choices(PATH_COUNTS, k=n % len(PATH_COUNTS))
    random.shuffle(times); random.shuffle(paths)
    return list(zip(paths, times))

# ── Participant response model ────────────────────────────────

def simulate_response(n_paths, stim_time, cyclomatic, params):
    """
    Realistic response model:
    - Accuracy falls with n_paths and cyclomatic; rises with stim_time.
    - Wrong answers show underestimation bias.
    - RT is 0.3–4.8 s from stimulus offset.
    - ~3 % of trials produce no response.
    """
    if random.random() < 0.03:
        return None, None

    base_acc     = 0.92 - 0.11 * (n_paths - 1)
    time_bonus   = 0.04 * (stim_time - 5.0) / 2.0
    cycle_pen    = 0.06 * cyclomatic
    acc = min(0.93, max(0.06,
              base_acc + time_bonus - cycle_pen + params['skill']))

    rt_base = max(0.3, min(RESPONSE_WINDOW - 0.2,
                           abs(random.gauss(2.0 - 0.4 * acc, 0.7))))

    if random.random() < acc:
        response = n_paths
    else:
        delta    = int(round(random.gauss(-0.6, 1.3)))
        response = max(1, min(10, n_paths + delta))
        if response == n_paths:
            response = max(1, n_paths - 1)

    return response, round(rt_base, 4)


# ── Main simulation ───────────────────────────────────────────

PARTICIPANTS = [
    {'id': 'P01', 'skill':  0.10, 'seed': 42},
    {'id': 'P02', 'skill': -0.12, 'seed': 77},
    {'id': 'P03', 'skill':  0.00, 'seed': 13},
    {'id': 'P04', 'skill':  0.18, 'seed': 99},
    {'id': 'P05', 'skill': -0.08, 'seed': 55},
]

FIELDS = ['pid', 'block', 'trial', 'start', 'end',
          'edge_count', 'cyclomatic', 'stim_time', 'edges',
          'n_paths', 'response', 'rt']

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Spread fake timestamps one day apart so files look like separate sessions
base_time = datetime(2026, 4, 28, 9, 15, 0)

for p_idx, pinfo in enumerate(PARTICIPANTS):
    random.seed(pinfo['seed'])
    ts    = (base_time + timedelta(days=p_idx)).strftime('%Y%m%d_%H%M%S')
    fname = os.path.join(OUTPUT_DIR, f"sub-{pinfo['id']}_{ts}.csv")

    with open(fname, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()

        def write_trial(block, trial_idx, start, end, edges, stim_time):
            undirected  = {_canonical(u, v) for u, v in edges}
            n_paths     = count_trails(edges, start, end)
            cyc         = cyclomatic_number(edges)
            response, rt = simulate_response(n_paths, stim_time, cyc, pinfo)
            writer.writerow({
                'pid':        pinfo['id'],
                'block':      block,
                'trial':      trial_idx + 1,
                'start':      start,
                'end':        end,
                'edge_count': len(undirected),
                'cyclomatic': cyc,
                'stim_time':  stim_time,
                'edges':      edges,
                'n_paths':    n_paths,
                'response':   response,
                'rt':         rt,
            })
            f.flush()

        # Practice block
        print(f"[{pinfo['id']}] practice ...", end=' ', flush=True)
        for i, (target, _) in enumerate(make_trial_list(PRACTICE_TRIALS)):
            start, end = random.choice(NODE_PAIRS)
            if random.random() < 0.5:
                start, end = end, start
            edges = make_trail_graph(target, start, end)
            if edges is None:
                print(f"  skip practice trial {i+1} (gen failed)")
                continue
            write_trial('practice', i, start, end, edges, PRACTICE_STIM)
        print("done")

        # Main block
        print(f"[{pinfo['id']}] main block ...", end=' ', flush=True)
        for i, (target, stim_time) in enumerate(make_trial_list(TRIALS_PER_BLOCK)):
            start, end = random.choice(NODE_PAIRS)
            if random.random() < 0.5:
                start, end = end, start
            edges = make_trail_graph(target, start, end)
            if edges is None:
                print(f"  skip main trial {i+1} (gen failed)")
                continue
            write_trial('main', i, start, end, edges, stim_time)
        print("done")

    print(f"  => {fname}")

print("\nAll participants simulated.")
