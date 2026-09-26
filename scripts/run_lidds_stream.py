"""Streaming detection on one LID-DS 2021 scenario: W chosen on dev, reported once on test."""
import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from sidsb.lidds import load_scenario
from sidsb.lidds_eval import evaluate_lidds, make_lidds_splits
from sidsb.models.registry import build
from sidsb.stream import lstm_items_batch, ngram_items, peak, trajectory
from sidsb.threads import per_thread_items, thread_training_seqs


def fmt(v, spec=".3f"):
    return "-" if v is None else format(v, spec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/lidds_stream.yaml")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())
    fprs, sel, tb = cfg["fpr_targets"], cfg["selection_metric"], cfg["tiebreak_metric"]
    scen = Path(cfg["scenario_zip"]).stem
    out = Path(args.out or f"results/lidds/{scen}")

    recs, vocab = load_scenario(cfg["scenario_zip"])
    sp = make_lidds_splits(recs, cfg["seed"])
    per_thread = bool(cfg.get("per_thread", False))
    print(f"{scen}: " + " ".join(f"{k}={len(v)}" for k, v in sp.items()),
          f"(dev attacks={sum(r.family == 'attack' for r in sp['dev'])},",
          f"test attacks={sum(r.family == 'attack' for r in sp['test'])})")

    report, dev_rows = {}, []
    for spec in cfg["models"]:
        m = build(spec)
        print(f"fitting {m.name} ...", flush=True)
        m.fit(thread_training_seqs(sp["train"]) if per_thread else [r.seq for r in sp["train"]])
        fn = ((lambda seqs, m=m: [ngram_items(m, s) for s in seqs]) if m.name.startswith("ngram")
              else (lambda seqs, m=m: lstm_items_batch(m, seqs)))
        items = {k: (per_thread_items(sp[k], fn) if per_thread else fn([r.seq for r in sp[k]]))
                 for k in ("cal", "dev", "test")}
        results = []
        for w in cfg["windows"]:
            traj = {k: [trajectory(i, p, w) for i, p in v] for k, v in items.items()}
            cal_peaks = np.array([peak(s) for s, _ in traj["cal"]])
            dev = evaluate_lidds(cal_peaks, sp["dev"], traj["dev"], fprs)
            results.append((w, cal_peaks, traj, dev))
            dev_rows.append((m.name, w, dev))

        def key(r):
            d = r[3]
            delay = d[sel]["median_seconds_to_detect"]
            return (d[sel]["detection_rate"], d[tb]["detection_rate"],
                    -(delay if delay is not None else 1e12))
        w, cal_peaks, traj, _ = max(results, key=key)
        test = evaluate_lidds(cal_peaks, sp["test"], traj["test"], fprs)
        report[m.name] = {"window": w, "test": test}
        t1 = test["0.01"]
        print(f"{m.name:<14} W={w:<4} DR@1%={fmt(t1['detection_rate'])} "
              f"normals alarming={fmt(t1['normal_recordings_alarming'])} "
              f"pre-exploit alarms={fmt(t1['attacks_with_pre_exploit_alarm'])} "
              f"median s to detect={fmt(t1['median_seconds_to_detect'], '.2f')}", flush=True)

    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(
        {"test": report, "dev": [{"model": n, "window": w, "dev": d} for n, w, d in dev_rows]}, indent=2))
    L = [f"LID-DS 2021 / {scen} ({'per-thread context' if per_thread else 'threads interleaved'}). Alarm = first time the running mean of the last W items exceeds a",
         "threshold set on calibration normal recordings. Alarms before the exploit count as false alarms;",
         "detection = first alarm after the exploit starts; delay measured from the exploit timestamp.", "",
         "## Test", "",
         "| Model | W | DR@1% | normal recs alarming | attacks with pre-exploit alarm | median s to detect | DR@5% | normal recs alarming @5% |",
         "|---|---|---|---|---|---|---|---|"]
    for n, r in report.items():
        a, b = r["test"]["0.01"], r["test"]["0.05"]
        L.append(f"| {n} | {r['window']} | {fmt(a['detection_rate'])} | {fmt(a['normal_recordings_alarming'])} | "
                 f"{fmt(a['attacks_with_pre_exploit_alarm'])} | {fmt(a['median_seconds_to_detect'], '.2f')} | "
                 f"{fmt(b['detection_rate'])} | {fmt(b['normal_recordings_alarming'])} |")
    L += ["", "## Dev (used for choosing W)", "", "| Model | W | dev DR@1% | dev DR@5% | dev median s to detect @1% |",
          "|---|---|---|---|---|"]
    for n, w, d in dev_rows:
        L.append(f"| {n} | {w} | {fmt(d['0.01']['detection_rate'])} | {fmt(d['0.05']['detection_rate'])} | "
                 f"{fmt(d['0.01']['median_seconds_to_detect'], '.2f')} |")
    (out / "results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\nWrote {out}/results.md")


if __name__ == "__main__":
    main()
