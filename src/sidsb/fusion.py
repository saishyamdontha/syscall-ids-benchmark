"""Score fusion on a common scale.

Each model's raw score x is turned into an empirical tail probability against
held-out NORMAL traces:  p(x) = (#norm scores >= x + 1) / (n + 1).
Small p = unusual. -log(p) puts every model on the same "surprise" scale,
so scores from different models can be combined fairly.
"""
import numpy as np


class TailScaler:
    def fit(self, normal_scores):
        self.ref = np.sort(np.asarray(normal_scores, dtype=float))
        return self

    def transform(self, scores):
        scores = np.asarray(scores, dtype=float)
        n = len(self.ref)
        n_ge = n - np.searchsorted(self.ref, scores, side="left")
        return -np.log((n_ge + 1) / (n + 1))


RULES = {
    "fisher": lambda S: S.sum(axis=1),   # evidence adds up across models
    "min_p": lambda S: S.max(axis=1),    # alarm if ANY model is very surprised
}


def fuse(surprise_matrix, rule):
    return RULES[rule](np.asarray(surprise_matrix, dtype=float))
