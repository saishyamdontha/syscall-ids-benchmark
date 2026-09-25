"""STIDE-style baseline: fraction of a trace's n-grams never seen in normal training data."""
import numpy as np


def ngrams(seq, n):
    return [tuple(seq[i:i + n]) for i in range(len(seq) - n + 1)]


class NgramUnseen:
    def __init__(self, n=6):
        self.n = n
        self.name = f"ngram_n{n}"
        self.db = set()

    def fit(self, seqs):
        for s in seqs:
            self.db.update(ngrams(s, self.n))
        return self

    def score_one(self, seq):
        grams = ngrams(seq, self.n)
        if not grams:
            return 0.0
        return sum(g not in self.db for g in grams) / len(grams)

    def score(self, seqs):
        return np.array([self.score_one(s) for s in seqs], dtype=float)
