import numpy as np

from sidsb.lidds import Recording
from sidsb.models.ngram import NgramUnseen
from sidsb.stream import ngram_items
from sidsb.threads import per_thread_items, split_threads, thread_training_seqs


def _rec(seq, tids):
    return Recording("r", "test/normal", "normal", seq, np.arange(len(seq)), tids=np.array(tids))


def _fn(m):
    return lambda seqs: [ngram_items(m, s) for s in seqs]


def test_single_thread_equals_plain_scoring():
    m = NgramUnseen(n=3).fit([[1, 2, 3, 4] * 5])
    seq = [1, 2, 3, 9, 1, 2, 3, 4]
    (items, pos), = per_thread_items([_rec(seq, [7] * len(seq))], _fn(m))
    p_items, p_pos = ngram_items(m, seq)
    assert np.allclose(items, p_items) and np.array_equal(pos, p_pos)


def test_context_never_crosses_threads():
    # each thread alone is perfectly normal; only the interleaving creates unseen 3-grams
    m = NgramUnseen(n=3).fit([[1, 2, 3] * 10, [7, 8, 9] * 10])
    seq = [1, 7, 2, 8, 3, 9, 1, 7, 2, 8, 3, 9]
    tids = [1, 2] * 6
    (items, pos), = per_thread_items([_rec(seq, tids)], _fn(m))
    assert items.sum() == 0                             # per-thread: nothing unseen
    assert ngram_items(m, seq)[0].sum() > 0            # interleaved: everything looks new
    assert list(pos) == sorted(pos) and pos[0] == 5   # thread 1's 3rd call is global #5


def test_split_and_training_seqs():
    r = _rec([1, 7, 2, 8], [1, 2, 1, 2])
    assert [s for s, _ in split_threads(r.seq, r.tids)] == [[1, 2], [7, 8]]
    assert thread_training_seqs([r]) == [[1, 2], [7, 8]]
