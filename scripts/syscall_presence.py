"""Which syscalls drive 3-gram alerts, and how common key calls are in normal vs attack test traces."""
from collections import Counter
from pathlib import Path

import numpy as np
import yaml

from sidsb.data import load_adfa, make_dev_splits
from sidsb.explain import explain_alert, load_syscall_names
from sidsb.models.ngram import NgramUnseen
from sidsb.stream import ngram_items, peak, trajectory

cfg = yaml.safe_load(Path("configs/explain.yaml").read_text())
names = load_syscall_names(cfg["syscall_table"])
tr, va, at = load_adfa(cfg["data_root"])
sp = make_dev_splits(tr, va, at, cfg["seed"], cfg["dev_folders_per_family"])
m = NgramUnseen(cfg["n"]).fit([t.seq for t in sp["train"]])
W = cfg["window"]
cal = [peak(trajectory(*ngram_items(m, t.seq), W)[0]) for t in sp["norm"] + sp["thr"]]
thr = np.quantile(cal, 1 - cfg["fpr"])

ev = Counter()
for t in sp["test"]:
    if t.family != "normal":
        e = explain_alert(m, t.seq, W, thr)
        if e:
            for _, g in e["unseen"]:
                ev.update(g)
tot = sum(ev.values())
print("Share of syscalls inside the evidence 3-grams of attack alerts:")
for s, c in ev.most_common(6):
    print(f"  {names.get(s, s):<14} {c / tot:.3f}")

print("Fraction of test traces containing the syscall at least once (attack vs normal):")
att = [t.seq for t in sp["test"] if t.family != "normal"]
nor = [t.seq for t in sp["test"] if t.family == "normal"]
for s in (11, 102, 213):  # execve, socketcall, setuid32
    a, b = np.mean([s in x for x in att]), np.mean([s in x for x in nor])
    print(f"  {names[s]:<14} attack={a:.2f}  normal={b:.2f}")
