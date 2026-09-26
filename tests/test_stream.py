import numpy as np
import pytest

from sidsb.models.ngram import NgramUnseen
from sidsb.stream import (NgramStream, evaluate_stream, first_alarm, ngram_items,
                          peak, trajectory)

RNG = np.random.default_rng(5)
TRAIN = [list(RNG.integers(1, 6, 80)) for _ in range(30)]


def _online(stream, seq):
    out = [(stream.update(s), i + 1) for i, s in enumerate(seq)]
    scores = [(v, i) for v, i in out if v is not None]
    end = stream.finish()
    if end is not None:
        scores.append((end, len(seq)))
    return np.array([v for v, _ in scores]), np.array([i for _, i in scores])


@pytest.mark.parametrize("window,length", [(10, 60), (50, 30), (5, 5)])
def test_online_ngram_equals_offline_replay(window, length):
    m = NgramUnseen(n=3).fit(TRAIN)
    seq = list(RNG.integers(1, 9, length))
    on_s, on_p = _online(NgramStream(m, window), seq)
    off_s, off_p = trajectory(*ngram_items(m, seq), window)
    assert np.allclose(on_s, off_s) and np.array_equal(on_p, off_p)


def test_window_covering_whole_trace_equals_batch_score():
    m = NgramUnseen(n=3).fit(TRAIN)
    seq = list(RNG.integers(1, 9, 40))
    s, _ = trajectory(*ngram_items(m, seq), window=1000)
    assert len(s) == 1 and np.isclose(s[0], m.score_one(seq))


def test_first_alarm_and_peak():
    s, p = np.array([0.1, 0.5, 0.9]), np.array([10, 11, 12])
    assert first_alarm(s, p, 0.4) == 11 and first_alarm(s, p, 0.95) is None
    assert peak(s) == 0.9 and peak(np.zeros(0)) == -np.inf


def test_peak_calibration_limits_alarming_normals():
    cal = RNG.normal(size=2000)
    trajs = [(np.array([v]), np.array([100])) for v in RNG.normal(size=4000)]
    trajs.append((np.array([9.0]), np.array([100])))
    r = evaluate_stream(cal, trajs, ["normal"] * 4000 + ["A"], [100] * 4001, [0.05])
    assert r["0.05"]["detection_rate"] == 1.0
    assert abs(r["0.05"]["normal_traces_alarming"] - 0.05) < 0.015


torch = pytest.importorskip("torch")


def test_online_lstm_equals_offline_replay():
    from sidsb.models.lstm import LstmLM
    from sidsb.stream import LstmStream, lstm_items_batch
    m = LstmLM(emb=8, hidden=16, layers=2, chunk=20, stride=10, max_epochs=2,
               patience=2, device="cpu").fit(TRAIN)
    seqs = [list(RNG.integers(1, 9, L)) for L in (40, 7, 1, 25)]
    batch = lstm_items_batch(m, seqs, batch_size=3)
    for seq, (items, pos) in zip(seqs, batch):
        assert np.allclose(items, m.token_nll(seq), atol=1e-5)
        on_s, on_p = _online(LstmStream(m, 10), seq)
        off_s, off_p = trajectory(items, pos, 10)
        assert np.allclose(on_s, off_s, atol=1e-5) and np.array_equal(on_p, off_p)
