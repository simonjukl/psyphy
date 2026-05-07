# psyphy — Path Estimation in Directed Graphs

A psychophysical experiment examining how people estimate the number of traversal paths
through briefly presented directed graphs.

---

## Research goal

The experiment investigates perceptual and cognitive processing of graph structure under
brief exposure (tachistoscopic presentation). The central question is whether humans can
accurately estimate the number of distinct trails through a network, and what structural
graph properties drive over- or underestimation.

**Outcome variable (controlled):** the true number of edge-disjoint trails from the
start node to the end node (1–6 per trial), balanced across the experiment.

**Primary predictor:** cyclomatic number of the graph (e − v + c, where e = undirected
edges, v = nodes, c = connected components). Because the graph is always fully connected
(c = 1) and has 16 nodes, this simplifies to e − 15, ranging 0–4. The cyclomatic number
counts the number of independent cycles in the graph and is the structural property
hypothesised to drive estimation difficulty.

**Covariate:** edge count (15–19 undirected pairs), recorded per trial and used as a
continuous covariate in analysis.

---

## What a "path" means in this experiment

A **trail** is a sequence of nodes where:
- consecutive nodes are connected by an edge,
- each undirected edge is used **at most once** across the whole trail,
- **nodes may be revisited** (unlike simple paths).

This definition matches the visual intuition of following the double-headed arrows in the
displayed graph: once you traverse the connection between two nodes, that connection is
"used up" for that traversal.

---

## Stimuli

Graphs are random bidirectional subgraphs of a 4×4 lattice grid (16 nodes, up to 24
possible undirected adjacencies). Properties guaranteed per trial:

- All 16 nodes form **one connected component** (no disconnected subgraphs).
- Every edge is **bidirectional** (displayed as double-headed arrows).
- A valid trail from start to end exists.
- The trail count exactly matches the target for that trial.

Start and end nodes are drawn from four non-corner outer-edge positions on opposite sides
of the grid, with the direction (which end is start vs. end) randomised per trial.

---

## Trial structure

### Practice block (20 trials, 5 s stimulus)

Each trial:
1. **Stimulus** — graph shown for 5 s with the question "How many paths lead from GREEN to RED?"
2. **Response window** — blank screen, 5 s, participant types a number and presses Enter.
3. **Text feedback** — correct answer and participant's answer shown for 5 s (SPACE to skip).
4. **Trail feedback** — each trail displayed one at a time for 2 s each, with inactive edges
   faded and the active trail highlighted (SPACE to advance to the next trail early).

### Main block (54 trials)

Stimulus durations (3 s, 5 s, 7 s) and trail counts (1–6) are independently balanced and
randomly interleaved. No feedback is given. The 54-trial count is a multiple of 18
(6 counts × 3 durations), ensuring exact balance.

---

## Output data

One CSV file per participant, saved to `data/sub-{id}_{timestamp}.csv`. Written
incrementally — data is preserved even if the session is interrupted.

| Column | Description |
|---|---|
| `pid` | Participant ID entered at startup |
| `block` | `practice` or `main` |
| `trial` | Trial number within block |
| `start` | Start node (row, col) |
| `end` | End node (row, col) |
| `edge_count` | Number of undirected edges in this trial's graph |
| `cyclomatic` | Cyclomatic number: e − v + c |
| `stim_time` | Stimulus duration in seconds |
| `edges` | Full directed edge list of the graph |
| `n_paths` | True number of trails (the controlled value) |
| `response` | Participant's typed estimate (None if no response) |
| `rt` | Reaction time from stimulus offset to first keypress (s) |

---

## Setup and running

### Requirements

- Python 3.9 – 3.11 (PsychoPy is not yet stable on 3.12+)
- PsychoPy and its dependencies (see `requirements.txt`)

### First-time setup

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate        # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt
```

### Running the experiment

```powershell
# Activate the environment first (if not already active)
.venv\Scripts\Activate.ps1

# Run
python exp.py
```

A dialog box will appear asking for a **Participant ID**. On Windows the dialog sometimes
opens behind the terminal — press **Alt+Tab** to find it if the script appears to hang
after printing "attempting to measure screen ratio".

Press **Escape** at any time to abort; all trials completed so far are already saved.

### Monitor calibration

The display uses PsychoPy "norm" units (screen coordinates −1 to +1). Before the first
real session, run the experiment on the target machine and check that the graph fits
comfortably on screen. If nodes or arrows are cut off or too small, adjust these
constants at the top of `exp.py`:

| Constant | Default | Effect |
|---|---|---|
| `GRID_SPACING` | 0.28 | Distance between adjacent nodes |
| `NODE_RADIUS` | 0.040 | Circle radius of each node |
| `HEAD_HEIGHT` | 0.016 | Arrowhead length |
| `LINE_WIDTH` | 4.0 px | Edge stroke width |

---

## Key configuration parameters

All tunable parameters are in the `GLOBAL CONFIGURATION` block at the top of `exp.py`
(lines 11–55). Most commonly adjusted:

| Parameter | Default | Meaning |
|---|---|---|
| `TRIALS_PER_BLOCK` | 54 | Main block trials (keep as multiple of 18) |
| `PRACTICE_TRIALS` | 20 | Practice block trials |
| `STIM_TIMES` | [3, 5, 7] s | Tachistoscopic durations (balanced) |
| `RESPONSE_WINDOW` | 5.0 s | Time to type answer after stimulus |
| `FEEDBACK_TEXT_SEC` | 5.0 s | Duration of text feedback per practice trial |
| `FEEDBACK_PATHS_SEC` | 2.0 s | Duration each trail is shown in practice feedback |
| `EDGE_COUNT_MIN` | 15 | Minimum edges (15 = spanning tree, cyclomatic = 0) |
| `EDGE_COUNT_MAX` | 19 | Maximum edges (cyclomatic = 4) |
| `PATH_COUNTS` | [1…6] | Trail counts to present, balanced across trials |
