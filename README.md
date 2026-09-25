# Syscall IDS Benchmark: n-grams vs association rules vs LSTM on ADFA-LD

Host-based anomaly detection from Linux system-call traces. All models learn
from **normal traces only**; attacks are never used for training or threshold
selection.

## Key finding

A 2-layer LSTM language model has the best AUC (0.830 ± 0.004 over 3 seeds),
but a simple 3-gram lookup table detects **more attacks at the operating points
an IDS actually runs at** (1% and 5% false-positive rate). AUC alone would have
picked the wrong model.

## Protocol

- Train: `Training_Data_Master` (833 normal traces). The LSTM uses a 10% slice of
  these for early stopping.
- Calibration: 50% of `Validation_Data_Master` normals (2,186), used **only** to
  set thresholds at a target false-positive rate.
- Test: remaining validation normals (2,186) + all 746 attack traces (6 families).
- Fixed seed; results are exactly reproducible.

## Results (test set)

| Model | AUC | Detection @ 1% FPR | Detection @ 5% FPR |
|---|---|---|---|
| 3-gram unseen fraction | 0.695 | **0.170** | **0.327** |
| 6-gram unseen fraction | 0.827 | 0.000 | 0.216 |
| Association rules (median) | 0.562 | 0.044 | 0.135 |
| LSTM, mean NLL (3 seeds) | **0.830 ± 0.004** | 0.101 ± 0.013 | 0.273 ± 0.020 |
| LSTM, max 20-token window | 0.630 | 0.066 | 0.185 |

Per-family detection rates: `results/results.md`, `results/phase2/results.md`.

## Negative results worth knowing

- **Association rules** over syscall bigrams are close to random (AUC 0.56).
- **Max aggregation** of rule-violation scores saturates at 1.0 on normal traces,
  so no threshold can separate attacks (0% detection at any FPR).
- **Max-window aggregation** of LSTM surprise is much worse than mean (0.63 vs 0.83):
  ADFA attacks look abnormal across the whole trace, not in short bursts.

## Reproduce

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
pip install torch --index-url https://download.pytorch.org/whl/cpu
# ADFA-LD mirror: https://github.com/zhu1971/a-labelled-version-of-the-adfa-ld-dataset
unzip ADFA-LD.zip -d data/raw/
./scripts/reproduce.sh
```

## Limitations

- ADFA-LD dates from 2013 on Ubuntu 11.04; modern systems and attacks differ.
- Detection at 1% FPR is low for every model; none is deployable as-is.

## Origin

Rebuilt from a course group project ([Zero-Day-Attack-](https://github.com/saishyamdontha/Zero-Day-Attack-)).
This repository replaces its evaluation, which tuned thresholds on test data.

## Protocol v2: can fusion beat the best single model?

To choose models without touching test data, attack traces are split **by attack
run** (3 folders per family for dev, 7 for test), and validation normals are split
into score-scaling, threshold, dev and test sets. Each model's score is converted
to a tail probability against held-out normal traces, so models can be fused on a
common scale (sum or max of -log p). The selection rule was fixed in the config
before running: best dev detection at 1% FPR, tie-break at 5%.

| Candidate | Dev DR@1% | Test DR@1% (FPR) | Test DR@5% (FPR) | Test AUC |
|---|---|---|---|---|
| **3-gram (selected on dev)** | **0.183** | **0.165 (0.010)** | **0.320 (0.057)** | 0.700 |
| max(3-gram, 6-gram) | 0.183 | 0.165 (0.010) | 0.297 (0.052) | 0.835 |
| max(3-gram, LSTM) | 0.135 | 0.123 (0.009) | 0.316 (0.059) | 0.830 |
| LSTM alone | 0.130 | 0.106 (0.007) | 0.305 (0.057) | 0.836 |

**Result:** no fusion of n-grams and LSTM beat the 3-gram at the declared
operating point. The 3-gram's advantage holds under both protocols
(v1: 0.170 / 0.327, v2: 0.165 / 0.320). Full table: `results/fusion/results.md`.
