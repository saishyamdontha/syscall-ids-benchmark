"""Explaining 3-gram streaming alerts.

The 3-gram detector is transparent: its running score at the alarm is exactly
(# unseen 3-grams in the alarm window) / W. So the explanation below is not an
approximation - it reproduces the score exactly (checked in the tests).
"""
from collections import Counter
from pathlib import Path

import numpy as np

from .stream import first_alarm, ngram_items, trajectory


def load_syscall_names(tbl_path):
    """Parse the Linux kernel's syscall_32.tbl (i386 numbering, as used by ADFA-LD)."""
    names = {}
    for line in Path(tbl_path).read_text().splitlines():
        parts = line.split()
        if len(parts) >= 3 and not line.startswith("#") and parts[1] == "i386":
            names[int(parts[0])] = parts[2]
    return names


def gram_name(gram, names):
    return " > ".join(names.get(s, f"sys_{s}") for s in gram)


def explain_alert(model, seq, window, threshold):
    """Return the evidence behind the first alarm on this trace, or None."""
    items, pos = ngram_items(model, seq)
    scores, spos = trajectory(items, pos, window)
    alarm_at = first_alarm(scores, spos, threshold)
    if alarm_at is None:
        return None
    if len(items) >= window:
        in_win = (pos > alarm_at - window) & (pos <= alarm_at)
    else:
        in_win = np.ones(len(items), dtype=bool)
    idx = np.flatnonzero(in_win & (items > 0))
    unseen = [(int(j), tuple(seq[j:j + model.n])) for j in idx]
    return {
        "alarm_at": int(alarm_at),
        "score": float(scores[np.flatnonzero(spos == alarm_at)[0]]),
        "window_items": int(in_win.sum()),
        "unseen": unseen,
        "unseen_counts": Counter(g for _, g in unseen),
    }


def context_line(seq, start, names, n=3, before=4, after=4):
    """Syscall names around one unseen n-gram, with the n-gram in [brackets]."""
    lo, hi = max(0, start - before), min(len(seq), start + n + after)
    parts = [names.get(s, f"sys_{s}") for s in seq[lo:hi]]
    a, b = start - lo, start - lo + n
    return " ".join(parts[:a] + ["["] + parts[a:b] + ["]"] + parts[b:])
