"""Frequency-aware n-gram language model (smoothed Markov model of order n-1).

Unlike NgramUnseen (binary: was this n-gram ever seen?), each syscall gets a
surprise score -log P(syscall | previous n-1 syscalls), with add-k smoothing.
Rare-but-seen patterns therefore score high, like the LSTM, at n-gram speed.
"""
import math
from collections import Counter, deque

import numpy as np


class NgramLM:
    def __init__(self, n=3, k=0.1):
        self.n, self.k = n, k
        self.name = f"ngram_lm_n{n}"

    def fit(self, seqs):
        self.counts, self.ctx, vocab = Counter(), Counter(), set()
        for s in seqs:
            vocab.update(s)
            for j in range(self.n - 1, len(s)):
                g = tuple(s[j - self.n + 1:j + 1])
                self.counts[g] += 1
                self.ctx[g[:-1]] += 1
        self.V = len(vocab) + 1          # +1: room for syscalls never seen in training
        return self

    def surprise(self, ctx, x):
        c = self.counts.get(ctx + (x,), 0)
        return -math.log((c + self.k) / (self.ctx.get(ctx, 0) + self.k * self.V))

    def items(self, seq):
        """Per-syscall surprise and the syscall count consumed when each is known."""
        n = self.n
        if len(seq) < n:
            return np.zeros(0), np.zeros(0, dtype=int)
        vals = [self.surprise(tuple(seq[j - n + 1:j]), seq[j]) for j in range(n - 1, len(seq))]
        return np.array(vals, dtype=float), np.arange(n, len(seq) + 1)

    def score_one(self, seq):
        v, _ = self.items(seq)
        return float(v.mean()) if len(v) else 0.0

    def score(self, seqs):
        return np.array([self.score_one(s) for s in seqs], dtype=float)

    def stream(self, window):
        return NgramLMStream(self, window)


class NgramLMStream:
    """One syscall at a time; same outputs as offline replay (tested)."""

    def __init__(self, model, window):
        self.m, self.window = model, window
        self.prev = deque(maxlen=model.n - 1)
        self.vals = deque(maxlen=window)

    def update(self, syscall):
        if len(self.prev) == self.m.n - 1:
            self.vals.append(self.m.surprise(tuple(self.prev), syscall))
        self.prev.append(syscall)
        return sum(self.vals) / self.window if len(self.vals) == self.window else None

    def finish(self):
        if 0 < len(self.vals) < self.window:
            return sum(self.vals) / len(self.vals)
        return None
