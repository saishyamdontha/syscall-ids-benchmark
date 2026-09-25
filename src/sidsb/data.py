"""ADFA-LD loading and splitting."""
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Trace:
    path: str
    family: str  # "normal" or the attack family name
    seq: list
    group: str = ""  # attack folder, e.g. "Hydra_FTP_3"


def load_trace(path):
    return [int(t) for t in Path(path).read_text().split() if t.isdigit()]


def family_from_dir(name):
    """'Hydra_FTP_3' -> 'Hydra_FTP', 'Java_Meterpreter_1' -> 'Java_Meterpreter'."""
    head, _, tail = name.rpartition("_")
    return head if tail.isdigit() and head else name


def _load_dir(d, family, group=""):
    return [Trace(str(p), family, load_trace(p), group) for p in sorted(Path(d).glob("*.txt"))]


def load_adfa(root):
    root = Path(root)
    train = _load_dir(root / "Training_Data_Master", "normal")
    valid = _load_dir(root / "Validation_Data_Master", "normal")
    attacks = []
    attack_root = root / "Attack_Data_Master"
    if attack_root.is_dir():
        for d in sorted(p for p in attack_root.iterdir() if p.is_dir()):
            attacks += _load_dir(d, family_from_dir(d.name), d.name)
    if not (train and valid and attacks):
        raise FileNotFoundError(
            f"ADFA-LD not found or incomplete under {root}: "
            f"train={len(train)} valid={len(valid)} attack={len(attacks)}"
        )
    return train, valid, attacks


def make_splits(train, valid, attacks, calibration_fraction, seed):
    """Protocol v1. Train on Training_Data_Master. Split validation normals into a
    calibration set (threshold selection only) and a test set. All attacks go to test."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(valid))
    n_cal = int(len(valid) * calibration_fraction)
    calibration = [valid[i] for i in idx[:n_cal]]
    test = [valid[i] for i in idx[n_cal:]] + attacks
    return {"train": train, "calibration": calibration, "test": test}


def make_dev_splits(train, valid, attacks, seed, dev_folders_per_family=3,
                    fractions=(0.2, 0.2, 0.2)):
    """Protocol v2 (for model selection).

    Validation normals -> norm (score scaling), thr (threshold setting),
    dev normals, and the rest as test normals. Attacks are split by FOLDER
    (whole attack runs), so no run is shared between dev and test.
    """
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(valid))
    cuts = np.cumsum([int(len(valid) * f) for f in fractions])
    norm, thr, dev_n, test_n = (
        [valid[i] for i in part] for part in np.split(idx, cuts))

    by_family = {}
    for t in attacks:
        by_family.setdefault(t.family, set()).add(t.group)
    dev_groups = set()
    for fam in sorted(by_family):
        groups = sorted(by_family[fam])
        pick = rng.choice(len(groups), size=min(dev_folders_per_family, len(groups) - 1),
                          replace=False)
        dev_groups.update(groups[i] for i in pick)
    dev_a = [t for t in attacks if t.group in dev_groups]
    test_a = [t for t in attacks if t.group not in dev_groups]
    return {"train": train, "norm": norm, "thr": thr,
            "dev": dev_n + dev_a, "test": test_n + test_a}
