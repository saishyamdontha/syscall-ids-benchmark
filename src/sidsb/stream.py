"""Streaming (real-time) anomaly scoring.

A detector sees a trace one syscall at a time. Each model turns every new syscall
into an "item" (3-gram: 1 if the n-gram ending here was never seen in training;
LSTM: surprise = -log p(this syscall | history)). The running score is the mean of
the last W items. No score is produced until W items are seen; a trace that ends
with fewer than W items is scored once, at its end, over everything seen.

Alarm rule: raise an alarm the first time the running score exceeds a threshold.
The threshold is calibrated on the PEAK running score of each normal trace, so the
target FPR means "fraction of normal traces that ever alarm", not "fraction of
final scores above threshold".
"""
from collections import deque

import numpy as np
import torch

from .models.ngram import NgramUnseen

# ---------------------------------------------------------------------------
# Offline replay (fast, vectorised) -- used for evaluation
# ---------------------------------------------------------------------------


def ngram_items(model: NgramUnseen, seq):
    """Unseen-flags per n-gram and the syscall count consumed when each is known."""
    if hasattr(model, "items"):
        return model.items(seq)
    n = model.n
    if len(seq) < n:
        return np.zeros(0), np.zeros(0, dtype=int)
    flags = np.array([tuple(seq[i:i + n]) not in model.db for i in range(len(seq) - n + 1)],
                     dtype=float)
    return flags, np.arange(n, len(seq) + 1)


@torch.no_grad()
def lstm_items_batch(model, seqs, batch_size=64):
    """Per-syscall surprise for many traces (batched, equals LstmLM.token_nll)."""
    model.net.eval()
    enc = [model._encode(s) for s in seqs]
    out = [(np.zeros(0), np.zeros(0, dtype=int))] * len(seqs)
    order = [i for i in sorted(range(len(enc)), key=lambda i: len(enc[i])) if len(enc[i]) >= 2]
    for b in range(0, len(order), batch_size):
        idxs = order[b:b + batch_size]
        x = model._pad([enc[i] for i in idxs]).to(model.device)
        inp, tgt = x[:, :-1], x[:, 1:]
        logp = torch.log_softmax(model.net(inp), dim=-1)
        nll = (-logp.gather(2, tgt.unsqueeze(-1)).squeeze(-1)).cpu().numpy()
        for row, i in enumerate(idxs):
            L = len(enc[i])
            out[i] = (nll[row, :L - 1].astype(float), np.arange(2, L + 1))
    return out


def trajectory(items, positions, window):
    """Running score over time: (scores, syscalls_consumed_at_each_score)."""
    L = len(items)
    if L == 0:
        return np.zeros(0), np.zeros(0, dtype=int)
    if L < window:
        return np.array([items.mean()]), positions[-1:]
    c = np.concatenate([[0.0], np.cumsum(items)])
    scores = (c[window:] - c[:-window]) / window
    return scores, positions[window - 1:]


def peak(scores):
    return float(scores.max()) if len(scores) else -np.inf


def first_alarm(scores, positions, threshold):
    """Syscalls consumed when the alarm fires, or None."""
    hit = np.flatnonzero(scores > threshold)
    return int(positions[hit[0]]) if hit.size else None


def evaluate_stream(cal_peaks, trajs, families, lengths, fpr_targets):
    fams = np.asarray(families)
    y = fams != "normal"
    out = {}
    for t in fpr_targets:
        thr = float(np.quantile(cal_peaks, 1.0 - t))
        alarm = [first_alarm(s, p, thr) for s, p in trajs]
        fired = np.array([a is not None for a in alarm])
        delays = np.array([a if a is not None else np.nan for a in alarm], dtype=float)
        frac = delays / np.asarray(lengths, dtype=float)
        per_family = {}
        for f in sorted(set(fams[y].tolist())):
            m = fams == f
            d = delays[m & fired]
            per_family[f] = {"detection_rate": float(fired[m].mean()),
                             "median_syscalls_to_alarm": float(np.median(d)) if d.size else None}
        det = y & fired
        out[str(t)] = {
            "threshold": thr,
            "detection_rate": float(fired[y].mean()),
            "normal_traces_alarming": float(fired[~y].mean()),
            "median_syscalls_to_alarm": float(np.median(delays[det])) if det.any() else None,
            "median_fraction_of_trace_seen": float(np.median(frac[det])) if det.any() else None,
            "per_family": per_family,
        }
    return out


# ---------------------------------------------------------------------------
# True online scorers (one syscall at a time) -- used for live use & throughput
# ---------------------------------------------------------------------------


class NgramStream:
    def __init__(self, model: NgramUnseen, window):
        self.m, self.window = model, window
        self.prev = deque(maxlen=model.n - 1)
        self.items = deque(maxlen=window)
        self.seen = 0

    def update(self, syscall):
        """Feed one syscall; returns the running score, or None before W items."""
        self.seen += 1
        if len(self.prev) == self.m.n - 1:
            self.items.append(float(tuple(self.prev) + (syscall,) not in self.m.db))
        self.prev.append(syscall)
        return sum(self.items) / self.window if len(self.items) == self.window else None

    def finish(self):
        """Process exited: score a trace that never reached W items."""
        if 0 < len(self.items) < self.window:
            return sum(self.items) / len(self.items)
        return None


class LstmStream:
    def __init__(self, model, window):
        self.m, self.window = model, window
        self.items = deque(maxlen=window)
        self.state = None
        self.logp = None
        self.m.net.eval()

    @torch.no_grad()
    def update(self, syscall):
        tok = self.m.vocab.get(syscall, 1)
        if self.logp is not None:
            self.items.append(float(-self.logp[tok]))
        x = torch.tensor([[tok]], dtype=torch.long, device=self.m.device)
        h, self.state = self.m.net.lstm(self.m.net.emb(x), self.state)
        self.logp = torch.log_softmax(self.m.net.out(h[0, -1]), dim=-1).cpu().numpy()
        return sum(self.items) / self.window if len(self.items) == self.window else None

    def finish(self):
        if 0 < len(self.items) < self.window:
            return sum(self.items) / len(self.items)
        return None
