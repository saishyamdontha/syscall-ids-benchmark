"""Metrics. Thresholds come ONLY from calibration normals, never from test data."""
import numpy as np
from sklearn.metrics import roc_auc_score


def threshold_at_fpr(calibration_scores, target_fpr):
    return float(np.quantile(calibration_scores, 1.0 - target_fpr))


def evaluate(name, cal_scores, test_scores, test_families, fpr_targets):
    fams = np.asarray(test_families)
    y = fams != "normal"
    test_scores = np.asarray(test_scores, dtype=float)
    out = {"model": name, "auc": float(roc_auc_score(y, test_scores)), "at_fpr": {}}
    for t in fpr_targets:
        thr = threshold_at_fpr(cal_scores, t)
        pred = test_scores > thr
        out["at_fpr"][str(t)] = {
            "threshold": thr,
            "detection_rate": float(pred[y].mean()),
            "test_fpr": float(pred[~y].mean()),
            "per_family": {f: float(pred[fams == f].mean())
                           for f in sorted(set(fams[y].tolist()))},
        }
    return out
