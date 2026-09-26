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
./scripts/reproduce.sh   # also downloads the i386 syscall table (Linux v6.6) into data/raw/
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

## Real-time (streaming) detection

Each trace is replayed one syscall at a time. The running score is the mean of the
last W per-syscall items (3-gram: was this 3-gram unseen in training? LSTM: surprise
of this syscall). An alarm fires the first time the running score crosses a
threshold. The threshold is set on the **peak** running score of calibration normal
traces, so "1%" means at most 1% of normal traces *ever* alarm. W is chosen per model
on the dev split (W in {10, 20, 50, 100, 200}, rule declared in the config).

| Model (test, protocol v2 splits) | Detection @1% | Detection @5% | Syscalls/s, one at a time |
|---|---|---|---|
| **3-gram** (W=200) | **0.151** | **0.301** | ~1,500,000 (CPU) |
| LSTM, 3 seeds | 0.121 ± 0.044 | 0.259 ± 0.029 | ~4,000 (GPU) |
| 6-gram (W=200) | 0.000 | 0.206 | ~1,400,000 (CPU) |

**Findings**

- **The 3-gram is the better real-time detector here:** higher detection at both
  operating points, deterministic, and ~400x faster per syscall. The LSTM's
  dev-selected window varied across seeds (W=200, 20, 200) and its detection with it.
- **Detection vs delay:** alarms fire as soon as W syscalls are available, so W sets
  the delay. On dev, the 3-gram at W=50 catches 0.149 of attacks at a median of 61
  syscalls, versus 0.173 at 202 syscalls with W=200: 86% of the detection, ~3x sooner.
- **Short windows calibrate poorly:** with W=20 (one LSTM seed), 1.7% of test normal
  traces alarmed against a 1% target.
- **GPU does little for streaming:** scoring one syscall at a time is dominated by
  per-call overhead. Batching the next syscall of many processes into one call is
  the way to use a GPU in deployment (not implemented).

Limitation: ADFA-LD attack traces have no attack start time, so "syscalls to alarm"
is counted from the start of the trace. Streaming LSTM results were produced with
torch 2.11.0+cu128 on an NVIDIA RTX 2000 Ada. Full tables:
`results/gpu/stream/results.md`, `results/gpu/stream_seeds/results.md`.

## Why do alerts fire? (explained alerts)

Every 3-gram streaming alert is explained exactly: the evidence is the set of
never-seen 3-grams in the alarm window, and their count / W *is* the alarm score
(asserted for every alert). Syscall names use the i386 table, since ADFA-LD is 32-bit.
Full report with examples: `results/explain/report.md`.

| Family | Alerts / test traces (W=200, 1% threshold) | Most frequent evidence |
|---|---|---|
| Adduser | 13 / 67 | `clock_gettime > _newselect > _newselect` |
| Hydra_FTP | 22 / 111 | `ppoll > socketcall > socketcall` |
| Hydra_SSH | 19 / 137 | `_newselect > read > setitimer` |
| Java_Meterpreter | 13 / 88 | `clock_gettime > _newselect > clock_gettime` |
| Meterpreter | 7 / 55 | `_newselect > read > clock_gettime` |
| Web_Shell | 7 / 80 | `_newselect > _newselect > clock_gettime` |

**What the explanations reveal** (`scripts/syscall_presence.py`, output in
`results/explain/syscall_presence.txt`):

- No alert contains a syscall unseen in training: all evidence is new *orderings*
  of familiar calls.
- The evidence is dominated by event-loop and timing calls: `_newselect` 16.6%,
  `clock_gettime` 14.7%, `read` 10.0%, `nanosleep` 9.6%, `setitimer` 7.6%.
- `execve` appears in 9% of attack traces but 64% of normal test traces.
- So on ADFA-LD the detector largely recognises *which kind of process was
  recorded* (long-running server loops vs. short-lived commands), not the malicious
  actions themselves. Hydra_FTP is the clearest exception: `ppoll > socketcall > ...`
  is the server handling a burst of connections, i.e. the brute force as the victim
  sees it.
- False alarms (17 of 1,750 test normal traces) carry the same kind of timing-loop
  evidence (`_newselect > time > time`), which caps what any threshold can achieve.
- This is a property of the dataset as much as of the model, and motivates
  evaluating on data where attacks happen inside the normal activity of the same
  service (e.g. LID-DS-2021).
