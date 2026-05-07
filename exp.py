#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Psychophysical experiment: Path estimation in directed graphs.
Participants briefly view a directed graph and estimate the number of
trails (each undirected edge traversed at most once; nodes may repeat)
from the green (start) to the red (end) node.
"""

# ============================================================
# GLOBAL CONFIGURATION — edit freely
# ============================================================
GRID_SIZE         = 4
EDGE_COUNT_MIN    = 15       # minimum undirected edges (spanning tree — ensures full connectivity)
EDGE_COUNT_MAX    = 19       # maximum undirected edges (≈ density 0.8)
PATH_COUNTS       = [1, 2, 3, 4, 5, 6]   # controlled trail counts (outcome variable)
TRIALS_PER_BLOCK  = 54       # main trials — multiple of 18 (6 counts × 3 times)
PRACTICE_TRIALS   = 20       # number of practice trials
PRACTICE_STIM_SEC = 5.0      # stimulus duration during practice (s)
STIM_TIMES        = [3.0, 5.0, 7.0]   # randomly balanced across main trials
RESPONSE_WINDOW   = 5.0      # seconds participant has to type answer
FEEDBACK_TEXT_SEC  = 5.0      # seconds to show correct-answer text only (practice)
FEEDBACK_PATHS_SEC = 2.0      # seconds to show each individual trail (practice)
OUTPUT_DIR        = 'data'   # folder for CSV output

# Valid start↔end pairs — outer-layer non-corner nodes on opposite sides.
# Each trial randomly picks one pair and randomly assigns which is start/end.
# (row, col) 0-indexed in GRID_SIZE×GRID_SIZE grid.
NODE_PAIRS = [
    ((0, 1), (3, 2)),  # top ↔ bottom, shifted column
    ((0, 2), (3, 1)),  # top ↔ bottom, shifted column
    ((1, 0), (2, 3)),  # left ↔ right, shifted row
    ((2, 0), (1, 3)),  # left ↔ right, shifted row
]

# ── Display constants (PsychoPy norm units, screen ±1) ───────
GRID_SPACING = 0.28    # distance between adjacent nodes
NODE_RADIUS  = 0.040
LINE_WIDTH   = 4.0     # pixels
HEAD_HEIGHT  = 0.016   # arrowhead length
HEAD_WIDTH   = 0.010   # arrowhead half-width
TEXT_HEIGHT  = 0.050

BG_COLOR   = '#ffffff'
NODE_DEF   = '#888888'
NODE_START = '#22cc55'   # green
NODE_END   = '#cc2222'   # red
EDGE_COLOR = '#444444'
EDGE_FADED = '#cccccc'   # inactive edges during feedback

PATH_PALETTE = [
     '#f72585',  '#7209b7', '#3a0ca3',  '#4361ee',  '#4cc9f0',  '#4895ef', '#6930c3',  '#5e60ce',
     '#ff006e',  '#fb5607', '#ffbe0b',  '#80ffdb',  '#72efdd',  '#64dfdf', '#56cfe1',  '#48bfe3'
]
# ============================================================

import os
import csv
import random
from datetime import datetime
from collections import defaultdict

import numpy as np
from psychopy import visual, core, event, gui


# ── Graph generation ─────────────────────────────────────────

def _all_pairs():
    """All 24 undirected adjacent pairs in the 4×4 grid."""
    pairs = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if c + 1 < GRID_SIZE:
                pairs.append(((r, c), (r, c + 1)))
            if r + 1 < GRID_SIZE:
                pairs.append(((r, c), (r + 1, c)))
    return pairs   # 24 pairs → 48 directed edges when both directions added


def _pairs_to_edges(pairs):
    """Expand undirected pairs to both directed edges."""
    edges = []
    for u, v in pairs:
        edges.append((u, v))
        edges.append((v, u))
    return edges


def _has_path(edges, src, dst):
    """BFS reachability check."""
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
    """All GRID_SIZE×GRID_SIZE nodes form a single connected component."""
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


def cyclomatic_number(edges):
    """Cyclomatic number of the underlying undirected graph: e − v + c."""
    if not edges:
        return 0
    nodes, undirected = set(), set()
    for u, v in edges:
        nodes.add(u)
        nodes.add(v)
        undirected.add((u, v) if u < v else (v, u))
    e, v_count = len(undirected), len(nodes)
    adj = defaultdict(set)
    for a, b in undirected:
        adj[a].add(b)
        adj[b].add(a)
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


def _canonical_pair(a, b):
    return (a, b) if a < b else (b, a)


def count_trails(edges, start, end, limit=None):
    """
    Count trails from start to end where each undirected edge may be
    traversed at most once (nodes may be revisited).
    If limit is given, counting stops early once count exceeds limit.
    """
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
            k = _canonical_pair(n, m)
            if k not in used:
                used.add(k)
                dfs(m, used)
                used.remove(k)

    dfs(start, set())
    return count[0]


def all_trails(edges, start, end):
    """Enumerate all trails (no undirected edge revisited, nodes may repeat)."""
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
    result = []

    def dfs(n, trail, used):
        if n == end:
            result.append(list(trail))
            return
        for m in adj[n]:
            k = _canonical_pair(n, m)
            if k not in used:
                used.add(k)
                dfs(m, trail + [m], used)
                used.remove(k)

    dfs(start, [start], set())
    return result


def make_trail_graph(target_trails, start, end, max_attempts=5000):
    """
    Generate a random bidirectional subgraph of the 4×4 grid such that
    • every grid node has at least one edge
    • a path exists from start to end
    • exactly target_trails trails exist from start to end
    Edge count is sampled uniformly in [EDGE_COUNT_MIN, EDGE_COUNT_MAX].
    Returns the directed edge list, or None if generation fails.
    """
    all_pairs = _all_pairs()
    for _ in range(max_attempts):
        n_edges = random.randint(EDGE_COUNT_MIN, EDGE_COUNT_MAX)
        sampled = random.sample(all_pairs, n_edges)
        edges   = _pairs_to_edges(sampled)
        if not _is_connected(edges):
            continue
        if not _has_path(edges, start, end):
            continue
        if count_trails(edges, start, end, limit=target_trails + 1) == target_trails:
            return edges
    return None


# ── Screen coordinates ────────────────────────────────────────

def pos(row, col):
    """Grid (row, col) → norm-unit screen position."""
    ox = -(GRID_SIZE - 1) * GRID_SPACING / 2
    oy =  (GRID_SIZE - 1) * GRID_SPACING / 2
    return (ox + col * GRID_SPACING, oy - row * GRID_SPACING)


# ── Drawing ──────────────────────────────────────────────────

def _bidir_arrow(win, p0, p1, color):
    """Single edge with arrowheads pointing toward both endpoints."""
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    L = np.hypot(dx, dy)
    if L == 0:
        return []
    ux, uy = dx / L, dy / L
    px, py = -uy, ux

    # Line runs between the two arrowhead bases (inside both node circles)
    ls = (x0 + ux * (HEAD_HEIGHT + NODE_RADIUS), y0 + uy * (HEAD_HEIGHT + NODE_RADIUS))
    le = (x1 - ux * (HEAD_HEIGHT + NODE_RADIUS), y1 - uy * (HEAD_HEIGHT + NODE_RADIUS))

    line  = visual.Line(win, start=ls, end=le, lineColor=color, lineWidth=LINE_WIDTH)

    tip1  = (x1 - ux * NODE_RADIUS,  y1 - uy * NODE_RADIUS)
    head1 = visual.ShapeStim(win, lineColor=color, fillColor=color,
                              vertices=[tip1,
                                        (le[0] + px * HEAD_WIDTH, le[1] + py * HEAD_WIDTH),
                                        (le[0] - px * HEAD_WIDTH, le[1] - py * HEAD_WIDTH)])

    tip0  = (x0 + ux * NODE_RADIUS,  y0 + uy * NODE_RADIUS)
    head0 = visual.ShapeStim(win, lineColor=color, fillColor=color,
                              vertices=[tip0,
                                        (ls[0] + px * HEAD_WIDTH, ls[1] + py * HEAD_WIDTH),
                                        (ls[0] - px * HEAD_WIDTH, ls[1] - py * HEAD_WIDTH)])

    return [line, head0, head1]


def graph_stims(win, edges, start, end, paths=None):
    """
    Build list of PsychoPy stims for the graph.
    Each undirected pair is drawn once as a double-headed arrow.
    If paths is provided (feedback mode), edges on paths get palette colours.
    """
    stims = []

    # Canonical undirected pair key
    def _key(u, v): return (u, v) if u < v else (v, u)

    # Build colour map keyed on canonical undirected pairs
    ecolor = {}
    if paths is not None:
        for i, path in enumerate(paths[:len(PATH_PALETTE)]):
            c = PATH_PALETTE[i]
            for j in range(len(path) - 1):
                ecolor.setdefault(_key(path[j], path[j + 1]), c)

    # Deduplicate directed edges → canonical undirected pairs
    seen = set()
    for u, v in edges:
        k = _key(u, v)
        if k not in seen:
            seen.add(k)
            c = ecolor.get(k, EDGE_FADED if paths is not None else EDGE_COLOR)
            stims.extend(_bidir_arrow(win, pos(*u), pos(*v), c))

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            nd = (r, c)
            fc = NODE_START if nd == start else (NODE_END if nd == end else NODE_DEF)
            stims.append(visual.Circle(win, radius=NODE_RADIUS, pos=pos(r, c),
                                        fillColor=fc, lineColor='#555555',
                                        lineWidth=1))
    return stims


def _draw(stims):
    for s in stims:
        s.draw()


# ── Stimulus display ──────────────────────────────────────────

def show_graph(win, stims, duration, header=''):
    """Tachistoscopic display: show graph for `duration` seconds then blank."""
    hdr = visual.TextStim(win, text=header, pos=(0, 0.88),
                           height=TEXT_HEIGHT * 0.85, color='#222222')
    clock = core.Clock()
    while clock.getTime() < duration:
        _draw(stims)
        if header:
            hdr.draw()
        win.flip()
        if 'escape' in event.getKeys(['escape']):
            return False
    win.flip()
    return True


# ── Response collection ───────────────────────────────────────

_ESCAPE = object()   # sentinel distinguishing escape from timeout


def get_response(win, time_limit):
    """
    Collect a typed integer within time_limit seconds.
    Returns (value_or_None, rt_or_None).
    Returns (_ESCAPE, None) if participant presses Escape.
    """
    box   = visual.Rect(win, width=0.35, height=0.14, pos=(0, 0),
                         lineColor='#555555', fillColor='#f0f0f0', lineWidth=2)
    prmpt = visual.TextStim(win, text='Number of paths:',
                             pos=(0, 0.22), height=TEXT_HEIGHT, color='#222222')
    disp  = visual.TextStim(win, pos=(0, -0.01),
                             height=TEXT_HEIGHT * 1.5, color='#111111')
    timer = visual.TextStim(win, pos=(0, -0.25),
                             height=TEXT_HEIGHT * 0.7, color='#888888')

    text = ''
    rt   = None
    clock = core.Clock()

    while clock.getTime() < time_limit:
        t = clock.getTime()
        timer.setText(f'{time_limit - t:.1f} s')

        for k in event.getKeys(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                                  'backspace', 'return', 'escape']):
            if k == 'escape':
                return _ESCAPE, None
            if k == 'return':
                if text:
                    return int(text), rt
            elif k == 'backspace':
                text = text[:-1]
            else:
                if rt is None:
                    rt = t
                text += k

        blink = '|' if int(t * 2) % 2 == 0 else ' '
        disp.setText(text + blink)
        prmpt.draw()
        box.draw()
        disp.draw()
        timer.draw()
        win.flip()

    return (int(text) if text else None), rt


# ── Single trial ──────────────────────────────────────────────

def run_trial(win, edges, start, end, stim_time, practice=False):
    """
    Run one trial: display graph, collect response, optionally show feedback.
    Returns dict {response, correct, rt} or None if Escape was pressed.
    """
    correct = count_trails(edges, start, end)
    stims   = graph_stims(win, edges, start, end)

    if not show_graph(win, stims, stim_time,
                      'How many paths lead from GREEN to RED?'):
        return None

    response, rt = get_response(win, RESPONSE_WINDOW)
    if response is _ESCAPE:
        return None

    if practice:
        paths   = all_trails(edges, start, end)
        n_shown = min(len(paths), len(PATH_PALETTE))
        ans_str = str(response) if response is not None else '—'
        mark    = '✓' if response == correct else '✗'

        # Phase 1: text only — correct answer (SPACE to skip)
        txt_lines = (f'Correct answer: {correct}      Your answer: {ans_str}  {mark}\n\n'
                     f'{n_shown} path{"s" if n_shown != 1 else ""} will be shown next.\n\n'
                     f'[SPACE to skip]')
        txt_stim = visual.TextStim(win, text=txt_lines, pos=(0, 0),
                                    height=TEXT_HEIGHT * 1.1, color='#111111',
                                    alignText='center')
        clock = core.Clock()
        while clock.getTime() < FEEDBACK_TEXT_SEC:
            txt_stim.draw()
            win.flip()
            if 'space' in event.getKeys(['space']):
                break

        # Phase 2: one trail at a time, FEEDBACK_PATHS_SEC each (SPACE skips to next)
        for t_idx, trail in enumerate(paths[:n_shown]):
            single_stims = graph_stims(win, edges, start, end, paths=[trail])
            trail_hdr = visual.TextStim(
                win,
                text=(f'Correct: {correct}   Your: {ans_str}  {mark}'
                      f'   Trail {t_idx + 1} / {n_shown}   [SPACE next]'),
                pos=(0, 0.88), height=TEXT_HEIGHT * 0.8, color='#222222')
            clock = core.Clock()
            while clock.getTime() < FEEDBACK_PATHS_SEC:
                _draw(single_stims)
                trail_hdr.draw()
                win.flip()
                if 'space' in event.getKeys(['space']):
                    break

    return {'response': response, 'correct': correct, 'rt': rt}


# ── Trial list ────────────────────────────────────────────────

def make_trial_list(n):
    """
    Return list of (target_trails, stim_time) tuples, length n.
    Both PATH_COUNTS and STIM_TIMES are balanced across trials.
    """
    n_per_t = n // len(STIM_TIMES)
    times   = STIM_TIMES * n_per_t + random.choices(STIM_TIMES,
                                                      k=n % len(STIM_TIMES))

    n_per_p = n // len(PATH_COUNTS)
    paths   = PATH_COUNTS * n_per_p + random.choices(PATH_COUNTS,
                                                      k=n % len(PATH_COUNTS))

    random.shuffle(times)
    random.shuffle(paths)
    return list(zip(paths, times))


# ── Splash screen ─────────────────────────────────────────────

def splash(win, text):
    visual.TextStim(win, text=text, height=TEXT_HEIGHT, color='#222222',
                     wrapWidth=1.7, alignText='center').draw()
    win.flip()
    k = event.waitKeys(keyList=['space', 'escape'])
    if 'escape' in k:
        core.quit()


# ── Main entry point ─────────────────────────────────────────

def run():
    dlg = gui.Dlg(title='Path Estimation Experiment')
    dlg.addField('Participant ID:')
    info = dlg.show()
    if not dlg.OK:
        core.quit()
    pid = str(info[0]).strip() or 'anon'

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts    = datetime.now().strftime('%Y%m%d_%H%M%S')
    fname = os.path.join(OUTPUT_DIR, f'sub-{pid}_{ts}.csv')

    win = visual.Window(fullscr=True, color=BG_COLOR, units='norm',
                         allowGUI=False)

    FIELDS = ['pid', 'block', 'trial', 'start', 'end',
              'edge_count', 'cyclomatic', 'stim_time', 'edges',
              'n_paths', 'response', 'rt']

    with open(fname, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()

        def save(block, i, start, end, edges, stim_time, res):
            undirected = {_canonical_pair(u, v) for u, v in edges}
            writer.writerow({
                'pid':        pid,
                'block':      block,
                'trial':      i + 1,
                'start':      start,
                'end':        end,
                'edge_count': len(undirected),
                'cyclomatic': cyclomatic_number(edges),
                'stim_time':  stim_time,
                'edges':      edges,
                'n_paths':    res['correct'],
                'response':   res['response'],
                'rt':         round(res['rt'], 4) if res['rt'] is not None else None,
            })
            f.flush()

        # ── Practice block ────────────────────────────────────
        splash(win,
               'PRACTICE\n\n'
               'A directed graph will appear briefly.\n'
               'Count the number of paths from the GREEN node to the RED node.\n'
               'Arrows show the allowed direction of travel, no edge cannot be visited twice (nodes may repeat).\n'
               'After each trial the correct answer and all paths will be shown.\n\n'
                'This practice block will take around 5 minutes.\n'
               'Press SPACE to begin.')

        for i, (target_trails, _) in enumerate(make_trial_list(PRACTICE_TRIALS)):
            start, end = random.choice(NODE_PAIRS)
            if random.random() < 0.5:
                start, end = end, start
            edges = make_trail_graph(target_trails, start, end)
            if edges is None:
                continue
            res = run_trial(win, edges, start, end, PRACTICE_STIM_SEC, practice=True)
            if res is None:
                break
            save('practice', i, start, end, edges, PRACTICE_STIM_SEC, res)

        # ── Main block ────────────────────────────────────────
        splash(win,
               'MAIN BLOCK\n\n'
               'The experiment now begins.\n'
               'No feedback will be provided after each trial.\n\n'
               'This block will take around 15-20 minutes.\n'
               'Press SPACE to continue.')

        for i, (target_trails, stim_time) in enumerate(make_trial_list(TRIALS_PER_BLOCK)):
            start, end = random.choice(NODE_PAIRS)
            if random.random() < 0.5:
                start, end = end, start
            edges = make_trail_graph(target_trails, start, end)
            if edges is None:
                continue
            res = run_trial(win, edges, start, end, stim_time, practice=False)
            if res is None:
                break
            save('main', i, start, end, edges, stim_time, res)

        splash(win, 'Experiment complete.\nThank you!\n\nPress SPACE to exit.')

    win.close()
    core.quit()


if __name__ == '__main__':
    run()
