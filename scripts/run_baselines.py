"""Fit every model on train, set thresholds on calibration, report on test."""
import argparse
import json
import time
from pathlib import Path

import yaml

from sidsb.data import load_adfa, make_splits
from sidsb.evaluate import evaluate
from sidsb.models.registry import build


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())

    train, valid, attacks = load_adfa(cfg["data_root"])
    splits = make_splits(train, valid, attacks, cfg["calibration_fraction"], cfg["seed"])
    fams = [t.family for t in splits["test"]]
    print(f"train={len(splits['train'])} calibration={len(splits['calibration'])} "
          f"test={len(splits['test'])} (attacks={len(attacks)})")

    results = []
    for spec in cfg["models"]:
        model = build(spec)
        t0 = time.time()
        model.fit([t.seq for t in splits["train"]])
        cal = model.score([t.seq for t in splits["calibration"]])
        test = model.score([t.seq for t in splits["test"]])
        r = evaluate(model.name, cal, test, fams, cfg["fpr_targets"])
        r["seconds"] = round(time.time() - t0, 1)
        r["spec"] = spec
        results.append(r)
        print(f"{model.name:<16} AUC={r['auc']:.3f}  " + "  ".join(
            f"DR@{k}={v['detection_rate']:.3f} (testFPR={v['test_fpr']:.3f})"
            for k, v in r["at_fpr"].items()) + f"  [{r['seconds']}s]")

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(results, indent=2))

    fam_names = sorted(results[0]["at_fpr"][str(cfg["fpr_targets"][-1])]["per_family"])
    k = str(cfg["fpr_targets"][-1])
    lines = ["| Model | AUC | " + " | ".join(f"DR@FPR {t}" for t in cfg["fpr_targets"])
             + " | " + " | ".join(fam_names) + " |",
             "|---" * (2 + len(cfg["fpr_targets"]) + len(fam_names)) + "|"]
    for r in results:
        lines.append(f"| {r['model']} | {r['auc']:.3f} | "
                     + " | ".join(f"{r['at_fpr'][str(t)]['detection_rate']:.3f}" for t in cfg["fpr_targets"])
                     + " | " + " | ".join(f"{r['at_fpr'][k]['per_family'][f]:.2f}" for f in fam_names) + " |")
    (out / "results.md").write_text(
        f"Per-family columns: detection rate at FPR {k} (threshold set on calibration normals).\n\n"
        + "\n".join(lines) + "\n")
    print(f"\nWrote {out/'metrics.json'} and {out/'results.md'}")


if __name__ == "__main__":
    main()
