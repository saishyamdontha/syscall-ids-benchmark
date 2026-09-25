"""ADFA-LD loading and train / calibration / test splitting."""
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Trace:
    path: str
    family: str  # "normal" or the attack family name
    seq: list


def load_trace(path):
    return [int(t) for t in Path(path).read_text().split() if t.isdigit()]


def family_from_dir(name):
    """'Hydra_FTP_3' -> 'Hydra_FTP', 'Java_Meterpreter_1' -> 'Java_Meterpreter'."""
    head, _, tail = name.rpartition("_")
    return head if tail.isdigit() and head else name


def _load_dir(d, family):
    return [Trace(str(p), family, load_trace(p)) for p in sorted(Path(d).glob("*.txt"))]


def load_adfa(root):
    root = Path(root)
    train = _load_dir(root / "Training_Data_Master", "normal")
    valid = _load_dir(root / "Validation_Data_Master", "normal")
    attacks = []
    attack_root = root / "Attack_Data_Master"
    if attack_root.is_dir():
        for d in sorted(p for p in attack_root.iterdir() if p.is_dir()):
            attacks += _load_dir(d, family_from_dir(d.name))
    if not (train and valid and attacks):
        raise FileNotFoundError(
            f"ADFA-LD not found or incomplete under {root}: "
            f"train={len(train)} valid={len(valid)} attack={len(attacks)}"
        )
    return train, valid, attacks


def make_splits(train, valid, attacks, calibration_fraction, seed):
    """Train on Training_Data_Master. Split validation normals into a calibration
    set (threshold selection only) and a test set. All attacks go to test.
    No attack trace is ever used for fitting or threshold selection."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(valid))
    n_cal = int(len(valid) * calibration_fraction)
    calibration = [valid[i] for i in idx[:n_cal]]
    test = [valid[i] for i in idx[n_cal:]] + attacks
    return {"train": train, "calibration": calibration, "test": test}
