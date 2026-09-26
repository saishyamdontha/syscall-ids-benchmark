import numpy as np

from sidsb.lidds import Recording
from sidsb.lidds_eval import evaluate_lidds, make_lidds_splits, outcome


def _attack(attack_pos=5, n=10):
    ts = np.arange(n, dtype=np.int64) * 1_000_000_000          # one syscall per second
    return Recording("a", "test/normal_and_attack", "attack", list(range(n)), ts,
                     attack_pos, exploit_ns=int(ts[attack_pos]))


def test_alarm_before_exploit_is_false_alarm_not_detection():
    r = _attack()
    s, p = np.array([0.9, 0.1, 0.1]), np.array([3, 7, 9])       # only the pre-exploit score is high
    assert outcome(r, s, p, 0.5) == (True, False, None, None)


def test_detection_delay_in_syscalls_and_seconds():
    r = _attack()
    s, p = np.array([0.1, 0.2, 0.9]), np.array([5, 7, 9])       # score at 5 consumed = pre-exploit
    early, det, calls, secs = outcome(r, s, p, 0.5)
    assert not early and det and calls == 4 and secs == 3.0     # syscall #9 at t=8 s, exploit at 5 s


def test_normal_recording_alarm_counts_as_false_alarm():
    r = Recording("n", "test/normal", "normal", [1, 2], np.array([0, 1]))
    assert outcome(r, np.array([0.7]), np.array([2]), 0.5)[0] is True


def test_splits_disjoint_and_complete():
    mk = lambda i, sp, fam: Recording(str(i), sp, fam, [1], np.array([0]), 0 if fam == "attack" else -1)
    recs = ([mk(i, "training", "normal") for i in range(5)] + [mk(100 + i, "validation", "normal") for i in range(3)]
            + [mk(200 + i, "test/normal", "normal") for i in range(50)]
            + [mk(300 + i, "test/normal_and_attack", "attack") for i in range(10)])
    sp = make_lidds_splits(recs, seed=0)
    ids = [r.name for k in ("train", "cal", "dev", "test") for r in sp[k]]
    assert len(ids) == len(set(ids)) == len(recs)
    assert all(r.family == "normal" for r in sp["cal"])
    assert sum(r.family == "attack" for r in sp["dev"]) == 3


def test_evaluate_counts():
    good = _attack()
    trajs = [(np.array([0.1, 0.9]), np.array([4, 8]))]
    r = evaluate_lidds(np.zeros(100), [good], trajs, [0.05])["0.05"]
    assert r["detection_rate"] == 1.0 and r["attacks_with_pre_exploit_alarm"] == 1.0


def test_attack_without_exploit_time_is_excluded():
    recs = [Recording("n", "test/normal", "normal", [1], np.array([0])),
            Recording("a", "test/normal_and_attack", "attack", [1], np.array([0]), 0),
            Recording("x", "test/normal_and_attack", "attack", [1], np.array([0]), -1)]
    sp = make_lidds_splits(recs, seed=0)
    names = {r.name for k in ("dev", "test") for r in sp[k]}
    assert "a" in names and "x" not in names
