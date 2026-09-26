"""Run the LID-DS streaming evaluation over every scenario zip, both context modes.

Each (scenario, mode) runs in its own process (memory is freed between scenarios) and is
skipped if its metrics.json already exists, so the whole run can be stopped and resumed.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

import yaml


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/lidds_all.yaml")
    ap.add_argument("--only", nargs="*", help="scenario names to run (default: all present)")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())
    zips = sorted(Path(cfg["data_dir"]).glob("*.zip"), key=lambda p: p.stat().st_size)
    if args.only:
        zips = [z for z in zips if z.stem in args.only]
    tmp = Path(cfg["out_dir"]) / "_configs"
    tmp.mkdir(parents=True, exist_ok=True)
    for z in zips:
        gb = z.stat().st_size / 1e9
        models = list(cfg["ngram_models"])
        if gb <= cfg["lstm_max_zip_gb"]:
            models.append(cfg["lstm_model"])
        for mode in cfg["modes"]:
            out = Path(cfg["out_dir"]) / z.stem / mode
            if (out / "metrics.json").exists():
                print(f"[skip] {z.stem} / {mode} (done)")
                continue
            run_cfg = {k: cfg[k] for k in ("seed", "fpr_targets", "windows",
                                           "selection_metric", "tiebreak_metric")}
            run_cfg.update(scenario_zip=str(z), per_thread=(mode == "per_thread"), models=models)
            cfg_path = tmp / f"{z.stem}_{mode}.yaml"
            cfg_path.write_text(yaml.safe_dump(run_cfg))
            print(f"\n=== {z.stem} ({gb:.2f} GB) / {mode} / {len(models)} models ===", flush=True)
            t0 = time.time()
            r = subprocess.run([sys.executable, "scripts/run_lidds_stream.py",
                                "--config", str(cfg_path), "--out", str(out)])
            if (out / "metrics.json").exists():
                status = "ok" + ("" if r.returncode == 0 else f" (results saved; exit code {r.returncode} at shutdown)")
            else:
                status = f"FAILED (exit {r.returncode}), no results"
            print(f"=== {z.stem} / {mode}: {status} in {(time.time() - t0) / 60:.1f} min ===", flush=True)


if __name__ == "__main__":
    main()
