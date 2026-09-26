import numpy as np

from sidsb.models.ngram_lm import NgramLM
from sidsb.stream import ngram_items, trajectory


def _model():
    common = [1, 2, 3] * 50
    rare = [1, 2, 4]                       # seen once
    return NgramLM(n=3, k=0.1).fit([common + rare + common])


def test_rare_seen_scores_between_common_and_unseen():
    m = _model()
    common = m.surprise((1, 2), 3)
    rare = m.surprise((1, 2), 4)
    unseen = m.surprise((1, 2), 9)
    assert common < rare < unseen


def test_items_align_with_positions():
    m = _model()
    v, p = m.items([1, 2, 3, 1, 2, 4])
    assert len(v) == 4 and list(p) == [3, 4, 5, 6]
    assert np.isclose(v[-1], m.surprise((1, 2), 4))


def test_stream_equals_offline_replay():
    m = _model()
    seq = [1, 2, 3, 1, 2, 4, 1, 2, 9, 3, 1, 2, 3] * 3
    for w in (4, 100):
        s = m.stream(w)
        on = [(v, i + 1) for i, x in enumerate(seq) if (v := s.update(x)) is not None]
        end = s.finish()
        if end is not None:
            on.append((end, len(seq)))
        off_s, off_p = trajectory(*ngram_items(m, seq), w)   # ngram_items dispatches to .items()
        assert np.allclose([v for v, _ in on], off_s) and [i for _, i in on] == list(off_p)
