"""Build one results table from every results/lidds_all/<scenario>/<mode>/metrics.json."""
import json
import sys
from pathlib import Path

import numpy as np

root = Path(sys.argv[1] if len(sys.argv) > 1 else "results/lidds_all")
rows = []
for mf in sorted(root.glob("*/*/metrics.json")):
    scen, mode = mf.parent.parent.name, mf.parent.name
    for model, r in json.loads(mf.read_text())["test"].items():
        a = r["test"]["0.01"]
        rows.append((scen, mode, model.split("_s")[0] if model.startswith("lstm") else model,
                     r["window"], a["detection_rate"], a["normal_recordings_alarming"],
                     a["attacks_with_pre_exploit_alarm"], a["median_seconds_to_detect"]))

f = lambda v, s=".3f": "-" if v is None else format(v, s)
L = ["# LID-DS 2021, all scenarios (test, 1% of calibration normal recordings ever alarming)", "",
     "| Scenario | Mode | Model | W | Detection | Normal recs alarming | Pre-exploit alarms | Median s to detect |",
     "|---|---|---|---|---|---|---|---|"]
L += [f"| {s} | {m} | {mo} | {w} | {f(d)} | {f(n)} | {f(p)} | {f(t, '.2f')} |" for s, m, mo, w, d, n, p, t in rows]

L += ["", "## Summary across scenarios (detection @1%)", "",
      "| Mode | Model | Scenarios | Median | Min | Max |", "|---|---|---|---|---|---|"]
for mode in sorted({r[1] for r in rows}):
    for model in sorted({r[2] for r in rows if r[1] == mode}):
        d = np.array([r[4] for r in rows if r[1] == mode and r[2] == model and r[4] is not None])
        if len(d):
            L.append(f"| {mode} | {model} | {len(d)} | {np.median(d):.3f} | {d.min():.3f} | {d.max():.3f} |")

pt = {(r[0], r[2]): r[4] for r in rows if r[1] == "per_thread"}
both = [s for s in {r[0] for r in rows} if (s, "ngram_n3") in pt and (s, "lstm_mean") in pt]
if both:
    wins = sum(pt[(s, "ngram_n3")] >= pt[(s, "lstm_mean")] for s in both)
    L += ["", f"Per-thread 3-gram >= LSTM in {wins} of {len(both)} scenarios where both ran."]
out = root / "summary.md"
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L[-12:]))
print(f"\nWrote {out}")
