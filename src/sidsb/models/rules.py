"""Association-rule model of normal syscall behaviour (cleaned port of the original ADFA layer).

Each window of syscalls becomes a transaction of bigrams. FP-Growth mines rules
A -> C from normal windows. A window's score is the weight of violated rules
(A present, C absent) divided by the weight of applicable rules (A present).
"""
from collections import Counter

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth


def windows(seq, size, step):
    if len(seq) < size:
        return [seq] if len(seq) >= 2 else []
    return [seq[i:i + size] for i in range(0, len(seq) - size + 1, step)]


def bigrams(seq):
    return frozenset(f"{a}_{b}" for a, b in zip(seq, seq[1:]))


class RuleViolation:
    def __init__(self, window=20, step=10, min_support=0.03, min_confidence=0.8,
                 min_lift=1.5, top_k=50, trace_agg="median", no_rule_score=0.0):
        self.window, self.step = window, step
        self.min_support, self.min_confidence, self.min_lift = min_support, min_confidence, min_lift
        self.top_k, self.trace_agg, self.no_rule_score = top_k, trace_agg, no_rule_score
        self.name = f"rules_{trace_agg}_nr{no_rule_score:g}"
        self.rules_ = []

    def fit(self, seqs):
        wins = [bigrams(w) for s in seqs for w in windows(s, self.window, self.step)]
        counts = Counter(i for w in wins for i in w)
        items = sorted(i for i, c in counts.items() if c / len(wins) >= self.min_support)
        ohe = pd.DataFrame([[i in w for i in items] for w in wins], columns=items, dtype=bool)
        freq = fpgrowth(ohe, min_support=self.min_support, use_colnames=True, max_len=2)
        rules = association_rules(freq, num_itemsets=len(ohe), metric="confidence",
                                  return_metrics=["support", "confidence", "lift"],
                                  min_threshold=self.min_confidence)
        rules = rules[rules["lift"] >= self.min_lift].copy()
        rules["weight"] = rules["lift"] * rules["confidence"]
        rules = rules.nlargest(self.top_k, "weight")
        self.rules_ = [(frozenset(r.antecedents), frozenset(r.consequents), float(r.weight))
                       for r in rules.itertuples()]
        if not self.rules_:
            raise RuntimeError("No rules mined: lower min_support / min_confidence / min_lift")
        return self

    def window_score(self, items):
        total = violated = 0.0
        for ante, cons, w in self.rules_:
            if ante <= items:
                total += w
                if not cons <= items:
                    violated += w
        return violated / total if total else self.no_rule_score

    def violations(self, seq):
        """Which rules a trace breaks, and how often. Used later to explain alerts."""
        hits = Counter()
        for win in windows(seq, self.window, self.step):
            items = bigrams(win)
            for k, (ante, cons, _) in enumerate(self.rules_):
                if ante <= items and not cons <= items:
                    hits[k] += 1
        return hits

    def score_one(self, seq):
        ws = [self.window_score(bigrams(w)) for w in windows(seq, self.window, self.step)]
        if not ws:
            return 0.0
        agg = {"median": np.median, "mean": np.mean, "max": np.max}[self.trace_agg]
        return float(agg(ws))

    def score(self, seqs):
        return np.array([self.score_one(s) for s in seqs], dtype=float)
