import numpy as np

from sidsb.explain import context_line, explain_alert, gram_name, load_syscall_names
from sidsb.models.ngram import NgramUnseen


def test_tbl_parsing(tmp_path):
    p = tmp_path / "t.tbl"
    p.write_text("# comment\n3\ti386\tread\tsys_read\n4 i386 write sys_write\n5 x32 bogus x\n")
    assert load_syscall_names(p) == {3: "read", 4: "write"}


def test_explanation_reproduces_score_exactly():
    rng = np.random.default_rng(0)
    train = [list(rng.integers(1, 5, 300)) for _ in range(20)]
    m = NgramUnseen(n=3).fit(train)
    seq = list(rng.integers(1, 5, 150)) + list(rng.integers(20, 30, 40)) + list(rng.integers(1, 5, 60))
    for window, thr in ((20, 0.3), (50, 0.3), (1000, 0.1)):   # 1000 > trace: whole-trace mean
        e = explain_alert(m, seq, window, threshold=thr)
        assert e is not None
        denom = e["window_items"]
        assert np.isclose(len(e["unseen"]) / denom, e["score"])
        assert all(g not in m.db for _, g in e["unseen"])


def test_no_alarm_gives_none():
    m = NgramUnseen(n=3).fit([[1, 2, 3, 1, 2, 3, 1, 2, 3]])
    assert explain_alert(m, [1, 2, 3, 1, 2, 3], 3, threshold=0.5) is None


def test_names_and_context():
    names = {3: "read", 4: "write", 5: "open"}
    assert gram_name((3, 4, 99), names) == "read > write > sys_99"
    assert context_line([5, 5, 3, 4, 5, 5], 2, names, before=1, after=1) == "open [ read write open ] open"
