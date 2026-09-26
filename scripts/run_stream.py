"""Streaming evaluation: per model, pick window W on DEV, report once on TEST.

Calibration normals = the 'norm' + 'thr' splits of protocol v2 (never dev/test).
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import yaml

from sidsb.data import load_adfa, make_dev_splits
from sidsb.models.registry import build
from sidsb.stream import (LstmStream, NgramStream, evaluate_stream, lstm_items_batch,
                          ngram_items, peak, trajectory)


def items_for(model, seqs):
    if model.name.startswith("ngram"):
        return [ngram_items(model, s) for s in seqs]
    return lstm_items_batch(model, seqs)


def throughput(model, seq, window):
    stream = (NgramStream if model.name.startswith("ngram") else LstmStream)(model, window)
    t0 = time.perf_counter()
    for s in seq:
        stream.update(s)
    return len(seq) / (time.perf_counter() - t0)


def fmt(v, spec=".3f"):
    return "-" if v is None else format(v, spec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/stream.yaml")
    ap.add_argument("--out", default="results/stream")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())
    fprs, sel, tb = cfg["fpr_targets"], cfg["selection_metric"], cfg["tiebreak_metric"]

    train, valid, attacks = load_adfa(cfg["data_root"])
    sp = make_dev_splits(train, valid, attacks, cfg["seed"], cfg["dev_folders_per_family"])
    cal = sp["norm"] + sp["thr"]
    print(f"calibration normals={len(cal)} dev={len(sp['dev'])} test={len(sp['test'])}")

    long_trace = max((t.seq for t in sp["test"]), key=len)
    tp_seq = (long_trace * 10)[:cfg["throughput_syscalls"]]

    report, dev_rows = {}, []
    for spec in cfg["models"]:
        m = build(spec)
        print(f"fitting {m.name} ...", flush=True)
        m.fit([t.seq for t in sp["train"]])
        items = {k: items_for(m, [t.seq for t in v])
                 for k, v in (("cal", cal), ("dev", sp["dev"]), ("test", sp["test"]))}
        meta = {k: ([t.family for t in sp[k]], [len(t.seq) for t in sp[k]]) for k in ("dev", "test")}

        results = []
        for w in cfg["windows"]:
            traj = {k: [trajectory(i, p, w) for i, p in v] for k, v in items.items()}
            cal_peaks = np.array([peak(s) for s, _ in traj["cal"]])
            dev = evaluate_stream(cal_peaks, traj["dev"], *meta["dev"], fprs)
            results.append((w, cal_peaks, traj, dev))
            dev_rows.append((m.name, w, dev))

        def key(r):
            d = r[3]
            delay = d[sel]["median_syscalls_to_alarm"]
            return (d[sel]["detection_rate"], d[tb]["detection_rate"],
                    -(delay if delay is not None else 1e12))
        w, cal_peaks, traj, _ = max(results, key=key)
        test = evaluate_stream(cal_peaks, traj["test"], *meta["test"], fprs)
        rate = throughput(m, tp_seq, w)
        report[m.name] = {"window": w, "test": test, "syscalls_per_sec": rate,
                          "device": getattr(m, "device", "cpu")}
        t1 = test["0.01"]
        print(f"{m.name:<14} W={w:<4} DR@1%={t1['detection_rate']:.3f} "
              f"(normals alarming {t1['normal_traces_alarming']:.3f})  "
              f"median syscalls to alarm={fmt(t1['median_syscalls_to_alarm'], '.0f')}  "
              f"throughput={rate:,.0f} syscalls/s", flush=True)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(
        {"test": report, "dev": [{"model": n, "window": w, "dev": d} for n, w, d in dev_rows]},
        indent=2))

    L = ["Streaming protocol: alarm at the first time the running mean of the last W items",
         "exceeds a threshold set so that the target fraction of CALIBRATION normal traces ever alarm.",
         f"W chosen per model on dev (criterion declared in config: dev DR@{sel}, then @{tb}, then delay).",
         "Syscalls-to-alarm is counted from the start of the trace (ADFA-LD has no attack start time).", "",
         "## Test results", "",
         "| Model | W | DR@1% | normals alarming | DR@5% | normals alarming | median syscalls to alarm @1% | median % of trace seen @1% | syscalls/s |",
         "|---|---|---|---|---|---|---|---|---|"]
    for name, r in report.items():
        a, b = r["test"]["0.01"], r["test"]["0.05"]
        frac = a["median_fraction_of_trace_seen"]
        L.append(f"| {name} | {r['window']} | {a['detection_rate']:.3f} | {a['normal_traces_alarming']:.3f} | "
                 f"{b['detection_rate']:.3f} | {b['normal_traces_alarming']:.3f} | "
                 f"{fmt(a['median_syscalls_to_alarm'], '.0f')} | {fmt(None if frac is None else 100 * frac, '.0f')} | "
                 f"{r['syscalls_per_sec']:,.0f} ({r['device']}) |")
    fams = sorted(next(iter(report.values()))["test"]["0.01"]["per_family"])
    L += ["", "## Test, per family @1% (detection rate / median syscalls to alarm)", "",
          "| Model | " + " | ".join(fams) + " |", "|---" * (len(fams) + 1) + "|"]
    for name, r in report.items():
        pf = r["test"]["0.01"]["per_family"]
        L.append(f"| {name} | " + " | ".join(
            f"{pf[f]['detection_rate']:.2f} / {fmt(pf[f]['median_syscalls_to_alarm'], '.0f')}" for f in fams) + " |")
    L += ["", "## Dev (used for choosing W)", "", "| Model | W | dev DR@1% | dev DR@5% | dev median delay @1% |",
          "|---|---|---|---|---|"]
    for n, w, d in dev_rows:
        L.append(f"| {n} | {w} | {d['0.01']['detection_rate']:.3f} | {d['0.05']['detection_rate']:.3f} | "
                 f"{fmt(d['0.01']['median_syscalls_to_alarm'], '.0f')} |")
    (out / "results.md").write_text("\n".join(L) + "\n")
    print(f"\nWrote {out}/results.md")


if __name__ == "__main__":
    main()
