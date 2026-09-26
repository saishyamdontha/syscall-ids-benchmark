import numpy as np
import pytest

torch = pytest.importorskip("torch")
from sidsb.models.lstm import LstmLM  # noqa: E402


def _data():
    rng = np.random.default_rng(3)
    return [list(rng.integers(1, 8, rng.integers(30, 70))) for _ in range(40)]


def _model(tmp_path, **kw):
    return LstmLM(emb=8, hidden=16, layers=1, chunk=20, stride=10, max_epochs=6,
                  patience=6, device="cpu", checkpoint_dir=str(tmp_path), **kw)


def test_resume_after_crash_matches_uninterrupted(tmp_path):
    data = _data()
    ref = LstmLM(emb=8, hidden=16, layers=1, chunk=20, stride=10, max_epochs=6,
                 patience=6, device="cpu").fit(data)

    m = _model(tmp_path)
    real = m._epoch_loss
    calls = {"n": 0}

    def crash(chunks, train):
        calls["n"] += 1
        if calls["n"] > 6:          # 3 epochs x (train + holdout), then "power cut"
            raise KeyboardInterrupt
        return real(chunks, train)

    m._epoch_loss = crash
    with pytest.raises(KeyboardInterrupt):
        m.fit(data)
    assert len(list(tmp_path.glob("*.pt"))) == 1

    resumed = _model(tmp_path).fit(data)
    assert [h["epoch"] for h in resumed.history] == [1, 2, 3, 4, 5, 6]
    assert np.allclose([h["holdout_nll"] for h in resumed.history],
                       [h["holdout_nll"] for h in ref.history], atol=1e-6)
    assert np.allclose(resumed.score(data[:5]), ref.score(data[:5]), atol=1e-6)


def test_finished_checkpoint_is_reused_not_retrained(tmp_path, capsys):
    data = _data()
    a = _model(tmp_path).fit(data)
    capsys.readouterr()
    b = _model(tmp_path, trace_agg="max_window").fit(data)   # scoring change only
    assert "loaded finished checkpoint" in capsys.readouterr().out
    assert np.allclose(a.token_nll(data[0]), b.token_nll(data[0]), atol=1e-7)


def test_config_change_gets_new_checkpoint(tmp_path):
    data = _data()
    _model(tmp_path).fit(data)
    _model(tmp_path, seed=7).fit(data)
    assert len(list(tmp_path.glob("*.pt"))) == 2
