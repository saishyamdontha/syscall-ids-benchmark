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
