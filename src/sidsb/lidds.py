"""LID-DS 2021 loader: reads recordings straight from a scenario zip (no extraction).

Layout: <scenario>.zip -> <scenario>/{training,validation,test/normal,test/normal_and_attack}/<rec>.zip
Each <rec>.zip holds <rec>.sc (syscalls), <rec>.json (metadata), <rec>.pcap, <rec>.res.
.sc line: ts_ns uid pid process tid syscall dir args...   (dir '>' = enter, '<' = exit)
We keep ENTER events only, all threads interleaved in time order.
"""
import io
import json
import pickle
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class Recording:
    name: str
    split: str             # training | validation | test/normal | test/normal_and_attack
    family: str            # "normal" or "attack"
    seq: list              # syscall ids (enter events)
    ts: np.ndarray = field(repr=False)   # ns timestamp per syscall in seq
    attack_pos: int = -1   # index of first syscall at/after exploit start (-1: none)
    exploit_ns: int = -1


def _split_of(path):
    parts = path.split("/")
    return "test/" + parts[2] if parts[1] == "test" else parts[1]


def parse_recording(inner_bytes, base, vocab):
    inner = zipfile.ZipFile(io.BytesIO(inner_bytes))
    meta = json.loads(inner.read(base + ".json").decode().replace("'", '"'))
    seq, ts = [], []
    for line in inner.read(base + ".sc").decode(errors="replace").splitlines():
        f = line.split(" ", 7)
        if len(f) < 7 or f[6] != ">":
            continue
        seq.append(vocab.setdefault(f[5], len(vocab) + 1))
        ts.append(int(f[0]))
    ts = np.array(ts, dtype=np.int64)
    exploits = meta.get("time", {}).get("exploit") or []
    exploit_ns, attack_pos = -1, -1
    if meta.get("exploit") and exploits:
        exploit_ns = int(round(min(e["absolute"] for e in exploits) * 1e9))
        attack_pos = int(np.searchsorted(ts, exploit_ns, side="left"))
    return seq, ts, exploit_ns, attack_pos, bool(meta.get("exploit"))


def load_scenario(zip_path, cache_dir="data/cache"):
    """Return (recordings, vocab). Parsed result is cached next to the data."""
    zip_path = Path(zip_path)
    st = zip_path.stat()
    cache = Path(cache_dir) / f"{zip_path.stem}_{st.st_size}.pkl"
    if cache.exists():
        return pickle.loads(cache.read_bytes())
    outer = zipfile.ZipFile(zip_path)
    names = sorted(n for n in outer.namelist()
                   if n.endswith(".zip") and not n.startswith("__MACOSX") and "/._" not in n)
    vocab, recs = {}, []
    for n in names:
        base = n.rsplit("/", 1)[1][:-4]
        seq, ts, exploit_ns, attack_pos, is_attack = parse_recording(outer.read(n), base, vocab)
        recs.append(Recording(base, _split_of(n), "attack" if is_attack else "normal",
                              seq, ts, attack_pos, exploit_ns))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(pickle.dumps((recs, vocab)))
    return recs, vocab
