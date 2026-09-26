"""Splits and streaming evaluation for LID-DS 2021 (attacks happen inside normal traffic).

Rules: an alarm in an attack recording BEFORE the exploit starts is a false alarm.
Detection = first alarm whose window includes at least one post-exploit syscall.
Time to detect = timestamp of the syscall that triggered the alarm minus exploit time.
"""
import numpy as np


def make_lidds_splits(recs, seed, cal_frac=0.4, dev_frac=0.2, attack_dev_frac=0.3):
    rng = np.random.default_rng(seed)
    by = lambda s: [r for r in recs if r.split == s]
    tn = by("test/normal")
    ta = [r for r in by("test/normal_and_attack") if r.attack_pos >= 0]   # need an exploit time
    tn = [tn[i] for i in rng.permutation(len(tn))]
    ta = [ta[i] for i in rng.permutation(len(ta))]
    a, b = int(len(tn) * cal_frac), int(len(tn) * (cal_frac + dev_frac))
    k = int(len(ta) * attack_dev_frac)
    return {"train": by("training"),
            "cal": by("validation") + tn[:a],
            "dev": tn[a:b] + ta[:k],
            "test": tn[b:] + ta[k:]}


def outcome(rec, scores, positions, threshold):
    """(alarm_before_exploit, detected, syscalls_to_detect, seconds_to_detect)."""
    hit = scores > threshold
    if rec.family != "attack":
        return bool(hit.any()), False, None, None
    pre = positions <= rec.attack_pos
    early = bool((hit & pre).any())
    post = np.flatnonzero(hit & ~pre)
    if not post.size:
        return early, False, None, None
    c = int(positions[post[0]])
    return early, True, c - rec.attack_pos, (int(rec.ts[c - 1]) - rec.exploit_ns) / 1e9


def evaluate_lidds(cal_peaks, recs, trajs, fpr_targets):
    out = {}
    att = np.array([r.family == "attack" for r in recs], dtype=bool)
    for t in fpr_targets:
        thr = float(np.quantile(cal_peaks, 1.0 - t))
        res = [outcome(r, s, p, thr) for r, (s, p) in zip(recs, trajs)]
        early = np.array([x[0] for x in res], dtype=bool)
        det = np.array([x[1] for x in res], dtype=bool)
        secs = [x[3] for x in res if x[1]]
        calls = [x[2] for x in res if x[1]]
        out[str(t)] = {
            "threshold": thr,
            "detection_rate": float(det[att].mean()) if att.any() else None,
            "normal_recordings_alarming": float(early[~att].mean()) if (~att).any() else None,
            "attacks_with_pre_exploit_alarm": float(early[att].mean()) if att.any() else None,
            "median_seconds_to_detect": float(np.median(secs)) if secs else None,
            "median_syscalls_to_detect": float(np.median(calls)) if calls else None,
        }
    return out
