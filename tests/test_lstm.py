import numpy as np
import pytest

torch = pytest.importorskip("torch")
from sidsb.models.lstm import LstmLM  # noqa: E402


def test_lstm_scores_normal_below_random():
    rng = np.random.default_rng(0)
    normal = [[1, 2, 3, 4, 5, 6] * 15 for _ in range(40)]
    m = LstmLM(emb=8, hidden=16, layers=1, chunk=20, stride=10, max_epochs=15,
               patience=15, device="cpu").fit(normal)
    weird = [list(rng.integers(1, 7, 90)) for _ in range(10)]
    assert m.score(normal).mean() < m.score(weird).mean()


def test_unseen_syscall_is_surprising():
    normal = [[1, 2, 3] * 20 for _ in range(20)]
    m = LstmLM(emb=8, hidden=16, layers=1, chunk=20, stride=10, max_epochs=10,
               patience=10, device="cpu").fit(normal)
    assert m.token_nll([1, 2, 999, 2, 3])[1] > m.token_nll([1, 2, 3, 1, 2])[1]


def test_batched_score_matches_single():
    rng = np.random.default_rng(1)
    normal = [list(rng.integers(1, 6, rng.integers(30, 80))) for _ in range(30)]
    for agg in ("mean", "max_window"):
        m = LstmLM(emb=8, hidden=16, layers=1, chunk=20, stride=10, max_epochs=2,
                   patience=2, trace_agg=agg, device="cpu").fit(normal)
        test = normal[:10] + [[3], [], list(rng.integers(1, 9, 57))]
        single = np.array([m.score_one(s) for s in test])
        assert np.allclose(m.score(test, batch_size=4), single, atol=1e-5)
