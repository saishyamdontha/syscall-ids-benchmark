import numpy as np

from sidsb.data import Trace, make_dev_splits
from sidsb.fusion import TailScaler, fuse


def test_tail_scaler_orders_and_is_unit_free():
    s = TailScaler().fit(np.arange(100))
    a, b = s.transform([10, 99]), TailScaler().fit(np.arange(100) * 1000).transform([10_000, 99_000])
    assert a[1] > a[0] and np.allclose(a, b)


def test_fusion_rules():
    S = np.array([[1.0, 3.0]])
    assert fuse(S, "fisher")[0] == 4.0 and fuse(S, "min_p")[0] == 3.0


def test_dev_split_keeps_attack_folders_disjoint():
    valid = [Trace(f"v{i}", "normal", [1]) for i in range(100)]
    attacks = [Trace(f"a{f}{i}", "Fam", [2], f"Fam_{f}") for f in range(1, 11) for i in range(3)]
    sp = make_dev_splits([], valid, attacks, seed=0, dev_folders_per_family=3)
    dev_g = {t.group for t in sp["dev"] if t.family != "normal"}
    test_g = {t.group for t in sp["test"] if t.family != "normal"}
    assert len(dev_g) == 3 and len(test_g) == 7 and not dev_g & test_g
    assert len(sp["norm"]) == len(sp["thr"]) == len(sp["dev"]) - 9 == 20
