import numpy as np

from sidsb.data import family_from_dir, make_splits, Trace
from sidsb.evaluate import evaluate, threshold_at_fpr
from sidsb.models.ngram import NgramUnseen
from sidsb.models.rules import RuleViolation


def test_family_names():
    assert family_from_dir("Hydra_FTP_3") == "Hydra_FTP"
    assert family_from_dir("Java_Meterpreter_1") == "Java_Meterpreter"
    assert family_from_dir("Adduser") == "Adduser"


def test_ngram_unseen_fraction():
    m = NgramUnseen(n=2).fit([[1, 2, 3, 4]])
    assert m.score_one([1, 2, 3, 4]) == 0.0
    assert m.score_one([1, 2, 9]) == 0.5  # (1,2) seen, (2,9) unseen


def test_rules_normal_scores_lower_than_shuffled():
    rng = np.random.default_rng(0)
    normal = [[1, 2, 3, 4, 5] * 20 for _ in range(50)]
    m = RuleViolation(window=10, step=5, min_support=0.3, min_confidence=0.8,
                      min_lift=1.0).fit(normal)
    weird = [list(rng.permutation([1, 2, 3, 4, 5] * 20)) for _ in range(10)]
    assert m.score(normal).mean() < m.score(weird).mean()


def test_threshold_hits_target_fpr():
    cal = np.random.default_rng(1).normal(size=10_000)
    thr = threshold_at_fpr(cal, 0.05)
    assert abs((cal > thr).mean() - 0.05) < 0.005


def test_splits_keep_attacks_out_of_calibration():
    tr = [Trace("t", "normal", [1])]
    va = [Trace(f"v{i}", "normal", [1]) for i in range(10)]
    at = [Trace("a", "Adduser", [2])]
    s = make_splits(tr, va, at, 0.5, 0)
    assert all(t.family == "normal" for t in s["calibration"])
    assert len(s["calibration"]) == 5 and len(s["test"]) == 6


def test_evaluate_perfect_separation():
    r = evaluate("x", np.zeros(100), np.array([0.0, 0.0, 1.0, 1.0]),
                 ["normal", "normal", "A", "B"], [0.05])
    assert r["auc"] == 1.0 and r["at_fpr"]["0.05"]["detection_rate"] == 1.0
