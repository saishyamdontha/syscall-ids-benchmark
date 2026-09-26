import io
import json
import zipfile

import numpy as np

from sidsb.lidds import load_scenario


def _rec(name, lines, exploit_s=None):
    meta = {"container": [{"role": "normal"}], "exploit": exploit_s is not None,
            "time": {"exploit": [] if exploit_s is None else [{"absolute": exploit_s}]}}
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr(name + ".sc", "\n".join(lines))
        z.writestr(name + ".json", json.dumps(meta).replace('"', "'"))
    return b.getvalue()


def _line(ts, call, d):
    return f"{ts} 0 1 apache2 1 {call} {d} fd=3"


def test_loader_reads_nested_zips_and_attack_position(tmp_path):
    normal = _rec("a", [_line(1_000_000_000 + i, c, d) for i, (c, d) in
                        enumerate([("read", ">"), ("read", "<"), ("write", ">"), ("write", "<")])])
    attack = _rec("b", [_line(t, c, ">") for t, c in
                        [(1_000_000_000, "read"), (2_000_000_000, "write"), (3_000_000_000, "execve")]],
                  exploit_s=1.5)
    z = tmp_path / "S.zip"
    with zipfile.ZipFile(z, "w") as o:
        o.writestr("S/training/a.zip", normal)
        o.writestr("__MACOSX/S/training/._a.zip", b"junk")
        o.writestr("S/test/normal_and_attack/b.zip", attack)
    recs, vocab = load_scenario(z, cache_dir=tmp_path / "cache")
    by = {r.name: r for r in recs}
    assert set(by) == {"a", "b"}
    assert by["a"].split == "training" and by["a"].family == "normal" and len(by["a"].seq) == 2
    assert by["b"].split == "test/normal_and_attack" and by["b"].family == "attack"
    assert by["b"].attack_pos == 1                      # first syscall at/after 1.5 s
    assert by["b"].seq == [vocab["read"], vocab["write"], vocab["execve"]]
    again, _ = load_scenario(z, cache_dir=tmp_path / "cache")   # from cache
    assert [r.seq for r in again] == [r.seq for r in recs]
    assert isinstance(by["b"].ts, np.ndarray)
