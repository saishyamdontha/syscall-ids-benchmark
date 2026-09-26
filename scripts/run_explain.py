"""Explain every 3-gram streaming alert on the TEST split and summarise the evidence."""
import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import yaml

from sidsb.data import load_adfa, make_dev_splits
from sidsb.explain import context_line, explain_alert, gram_name, load_syscall_names
from sidsb.models.ngram import NgramUnseen, ngrams
from sidsb.stream import ngram_items, peak, trajectory


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/explain.yaml")
    ap.add_argument("--out", default="results/explain")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())
    n, W, k = cfg["n"], cfg["window"], cfg["top_k"]
    names = load_syscall_names(cfg["syscall_table"])

    train, valid, attacks = load_adfa(cfg["data_root"])
    sp = make_dev_splits(train, valid, attacks, cfg["seed"], cfg["dev_folders_per_family"])
    m = NgramUnseen(n=n).fit([t.seq for t in sp["train"]])
    train_calls = {s for t in sp["train"] for s in t.seq}
    cal_peaks = [peak(trajectory(*ngram_items(m, t.seq), W)[0]) for t in sp["norm"] + sp["thr"]]
    thr = float(np.quantile(cal_peaks, 1 - cfg["fpr"]))

    alerts = {}
    for t in sp["test"]:
        e = explain_alert(m, t.seq, W, thr)
        if e is not None:
            assert np.isclose(len(e["unseen"]) / e["window_items"], e["score"])  # exact
            alerts.setdefault(t.family, []).append((t, e))
    normals_test = [t for t in sp["test"] if t.family == "normal"]
    normal_grams = Counter(g for t in normals_test for g in set(ngrams(t.seq, n)))

    def top(entries):
        c = Counter(g for _, e in entries for g in e["unseen_counts"])
        return c.most_common(k)

    fams = sorted({t.family for t in sp["test"]} - {"normal"})
    totals = Counter(t.family for t in sp["test"])
    L = [f"3-gram streaming detector, W={W}, threshold at {cfg['fpr']:.0%} of calibration normals ever alarming.",
         "Each alert's evidence = the never-seen 3-grams in its alarm window; their count / W equals the",
         "alarm score exactly. Syscall names: i386 table (ADFA-LD is 32-bit).", "",
         "## Evidence per attack family (test)", "",
         "| Family | Alerts / traces | Alerts with a syscall never seen in training | Most frequent evidence (alerts containing it; % of test normal traces containing it anywhere) |",
         "|---|---|---|---|"]
    summary = {}
    for f in fams:
        ents = alerts.get(f, [])
        novel = sum(any(s not in train_calls for _, g in e["unseen"] for s in g) for _, e in ents)
        ev = [f"`{gram_name(g, names)}` ({c}; {100 * normal_grams[g] / len(normals_test):.1f}%)"
              for g, c in top(ents)]
        L.append(f"| {f} | {len(ents)} / {totals[f]} | {novel} | {'<br>'.join(ev) or '-'} |")
        summary[f] = {"alerts": len(ents), "traces": totals[f], "novel_syscall_alerts": novel,
                      "top_evidence": [[list(g), c, normal_grams[g]] for g, c in top(ents)]}

    fa = alerts.get("normal", [])
    L += ["", f"## False alarms: {len(fa)} of {len(normals_test)} test normal traces", "",
          "| Evidence in false alarms | False alarms containing it |", "|---|---|"]
    L += [f"| `{gram_name(g, names)}` | {c} |" for g, c in top(fa)]

    L += ["", "## One example alert per family", ""]
    for f in fams:
        if not alerts.get(f):
            continue
        t, e = alerts[f][0]
        L += [f"**{f}** - `{Path(t.path).name}` ({len(t.seq)} syscalls): alarm after {e['alarm_at']} syscalls, "
              f"{len(e['unseen'])} of {e['window_items']} 3-grams in the window never seen in training "
              f"(score {e['score']:.3f} > threshold {thr:.3f}).", ""]
        shown = set()
        for j, g in e["unseen"]:
            if g in shown:
                continue
            shown.add(g)
            L.append(f"- at syscall {j + 1}: `{context_line(t.seq, j, names, n)}`")
            if len(shown) == k:
                break
        L.append("")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(
        {"threshold": thr, "window": W, "families": summary, "false_alarms": len(fa)}, indent=2))
    print("\n".join(L[:len(fams) + 8 + 4 + k]))
    print(f"\nWrote {out}/report.md")


if __name__ == "__main__":
    main()
