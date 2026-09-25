"""Protocol v2: select single models or fusions on DEV, report once on TEST."""
import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import yaml

from sidsb.data import load_adfa, make_dev_splits
from sidsb.evaluate import evaluate
from sidsb.fusion import TailScaler, fuse
from sidsb.models.registry import build


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/fusion.yaml")
    ap.add_argument("--out", default="results/fusion")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())
    fprs = cfg["fpr_targets"]

    train, valid, attacks = load_adfa(cfg["data_root"])
    sp = make_dev_splits(train, valid, attacks, cfg["seed"], cfg["dev_folders_per_family"])
    print({k: len(v) for k, v in sp.items()},
          "dev attacks:", sum(t.family != "normal" for t in sp["dev"]),
          "test attacks:", sum(t.family != "normal" for t in sp["test"]))

    # 1. fit each model once, turn its scores into surprise via the `norm` split
    surprise = {}  # name -> {split: array}
    for spec in cfg["models"]:
        m = build(spec)
        print(f"fitting {m.name} ...", flush=True)
        m.fit([t.seq for t in sp["train"]])
        raw = {s: m.score([t.seq for t in sp[s]]) for s in ("norm", "thr", "dev", "test")}
        scaler = TailScaler().fit(raw["norm"])
        surprise[m.name] = {s: scaler.transform(raw[s]) for s in ("thr", "dev", "test")}

    # 2. candidates: every single model + every fusion rule over every model subset
    names = list(surprise)
    cands = {n: (n,) for n in names}
    for k in range(2, len(names) + 1):
        for combo in itertools.combinations(names, k):
            for rule in cfg["fusion_rules"]:
                cands[f"{rule}({'+'.join(combo)})"] = (rule,) + combo

    def scores(cand, split):
        if len(cand) == 1:
            return surprise[cand[0]][split]
        rule, members = cand[0], cand[1:]
        return fuse(np.column_stack([surprise[m][split] for m in members]), rule)

    fam = {s: [t.family for t in sp[s]] for s in ("dev", "test")}
    rows = []
    for name, cand in cands.items():
        thr_scores = scores(cand, "thr")
        rows.append({
            "candidate": name,
            "dev": evaluate(name, thr_scores, scores(cand, "dev"), fam["dev"], fprs),
            "test": evaluate(name, thr_scores, scores(cand, "test"), fam["test"], fprs),
        })

    # 3. selection uses DEV only, with the criterion declared in the config
    sel, tb = cfg["selection_metric"], cfg["tiebreak_metric"]
    key = lambda r: (r["dev"]["at_fpr"][sel]["detection_rate"],
                     r["dev"]["at_fpr"][tb]["detection_rate"])
    rows.sort(key=key, reverse=True)
    chosen = rows[0]["candidate"]

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps({"chosen": chosen, "rows": rows}, indent=2))
    hdr = ("| Candidate | dev DR@1% | dev DR@5% | TEST AUC | TEST DR@1% (FPR) | TEST DR@5% (FPR) |\n"
           "|---|---|---|---|---|---|")
    lines = [hdr]
    for r in rows:
        d, t = r["dev"]["at_fpr"], r["test"]["at_fpr"]
        mark = " **(selected on dev)**" if r["candidate"] == chosen else ""
        lines.append(
            f"| {r['candidate']}{mark} | {d['0.01']['detection_rate']:.3f} | {d['0.05']['detection_rate']:.3f} | "
            f"{r['test']['auc']:.3f} | {t['0.01']['detection_rate']:.3f} ({t['0.01']['test_fpr']:.3f}) | "
            f"{t['0.05']['detection_rate']:.3f} ({t['0.05']['test_fpr']:.3f}) |")
    table = "\n".join(lines)
    (out / "results.md").write_text(
        f"Protocol v2. Selection criterion (declared in config): dev DR@{sel}, tiebreak @{tb}.\n"
        f"Chosen: **{chosen}**\n\n{table}\n")
    print("\n" + table + f"\n\nSelected on dev: {chosen}\nWrote {out}/")


if __name__ == "__main__":
    main()
