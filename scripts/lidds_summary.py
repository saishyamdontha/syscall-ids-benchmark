"""Sanity summary of one LID-DS 2021 scenario zip: counts, sizes, attack timing, vocabulary."""
import sys
import time
from collections import Counter

import numpy as np

from sidsb.lidds import load_scenario

t0 = time.time()
recs, vocab = load_scenario(sys.argv[1])
print(f"loaded {len(recs)} recordings in {time.time() - t0:.1f}s, {len(vocab)} distinct syscalls")
print("per split/family:", dict(Counter((r.split, r.family) for r in recs)))
lens = np.array([len(r.seq) for r in recs])
print(f"syscalls per recording (enter only): median={np.median(lens):.0f} min={lens.min()} max={lens.max()}")
att = [r for r in recs if r.family == "attack"]
if att:
    frac = np.array([r.attack_pos / max(len(r.seq), 1) for r in att])
    secs = np.array([(r.exploit_ns - r.ts[0]) / 1e9 for r in att if len(r.ts)])
    print(f"attacks: {len(att)}, missing exploit time: {sum(r.attack_pos < 0 for r in att)}")
    print(f"exploit starts at median {np.median(frac):.0%} of the recording ({np.median(secs):.1f}s in)")
    print(f"syscalls after exploit start: median={np.median([len(r.seq) - r.attack_pos for r in att]):.0f}")
train_calls = {s for r in recs if r.split == "training" for s in r.seq}
inv = {v: k for k, v in vocab.items()}
unseen = Counter(inv[s] for r in recs if r.split != "training" for s in set(r.seq) if s not in train_calls)
print("syscalls absent from training (recordings containing them):", unseen.most_common(8))
