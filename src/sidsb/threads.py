"""Per-thread scoring: each syscall is judged in the context of its OWN thread.

A recording is split into one subsequence per thread. Any model's per-syscall items
are computed on those subsequences, then mapped back to global positions, so the
streaming running score, calibration and exploit timing work unchanged.
"""
import numpy as np


def split_threads(seq, tids):
    """[(thread_subsequence, global_indices)] in order of each thread's first syscall."""
    order, groups = [], {}
    for i, t in enumerate(tids):
        if t not in groups:
            groups[t] = []
            order.append(t)
        groups[t].append(i)
    return [([seq[i] for i in groups[t]], np.array(groups[t])) for t in order]


def per_thread_items(recs, items_fn):
    """items_fn(list_of_seqs) -> [(items, positions)] per seq. Returns merged per recording."""
    parts, owner = [], []
    for r_i, r in enumerate(recs):
        for sub, idx in split_threads(r.seq, r.tids):
            parts.append((sub, idx))
            owner.append(r_i)
    results = items_fn([sub for sub, _ in parts])
    merged = [([], []) for _ in recs]
    for (sub, idx), r_i, (items, pos) in zip(parts, owner, results):
        if len(items):
            merged[r_i][0].append(items)
            merged[r_i][1].append(idx[np.asarray(pos) - 1] + 1)
    out = []
    for items, pos in merged:
        if not items:
            out.append((np.zeros(0), np.zeros(0, dtype=int)))
            continue
        items, pos = np.concatenate(items), np.concatenate(pos)
        o = np.argsort(pos, kind="stable")
        out.append((items[o], pos[o]))
    return out


def thread_training_seqs(recs):
    return [sub for r in recs for sub, _ in split_threads(r.seq, r.tids)]
