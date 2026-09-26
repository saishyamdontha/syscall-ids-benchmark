Streaming protocol: alarm at the first time the running mean of the last W items
exceeds a threshold set so that the target fraction of CALIBRATION normal traces ever alarm.
W chosen per model on dev (criterion declared in config: dev DR@0.01, then @0.05, then delay).
Syscalls-to-alarm is counted from the start of the trace (ADFA-LD has no attack start time).

## Test results

| Model | W | DR@1% | normals alarming | DR@5% | normals alarming | median syscalls to alarm @1% | median % of trace seen @1% | syscalls/s |
|---|---|---|---|---|---|---|---|---|
| ngram_n3 | 200 | 0.151 | 0.010 | 0.301 | 0.060 | 202 | 55 | 1,462,915 (cpu) |
| ngram_lm_n3 | 200 | 0.134 | 0.011 | 0.217 | 0.045 | 202 | 52 | 881,731 (cpu) |
| ngram_lm_n4 | 50 | 0.158 | 0.015 | 0.216 | 0.059 | 112 | 31 | 1,735,910 (cpu) |

## Test, per family @1% (detection rate / median syscalls to alarm)

| Model | Adduser | Hydra_FTP | Hydra_SSH | Java_Meterpreter | Meterpreter | Web_Shell |
|---|---|---|---|---|---|---|
| ngram_n3 | 0.19 / 202 | 0.20 / 202 | 0.14 / 202 | 0.15 / 202 | 0.13 / 202 | 0.09 / 202 |
| ngram_lm_n3 | 0.12 / 202 | 0.21 / 203 | 0.14 / 202 | 0.09 / 202 | 0.13 / 202 | 0.09 / 203 |
| ngram_lm_n4 | 0.12 / 123 | 0.27 / 94 | 0.18 / 124 | 0.08 / 159 | 0.11 / 180 | 0.12 / 100 |

## Dev (used for choosing W)

| Model | W | dev DR@1% | dev DR@5% | dev median delay @1% |
|---|---|---|---|---|
| ngram_n3 | 10 | 0.000 | 0.245 | - |
| ngram_n3 | 20 | 0.072 | 0.288 | 75 |
| ngram_n3 | 50 | 0.149 | 0.317 | 61 |
| ngram_n3 | 100 | 0.163 | 0.332 | 102 |
| ngram_n3 | 200 | 0.173 | 0.327 | 202 |
| ngram_lm_n3 | 10 | 0.087 | 0.279 | 104 |
| ngram_lm_n3 | 20 | 0.125 | 0.269 | 170 |
| ngram_lm_n3 | 50 | 0.106 | 0.231 | 168 |
| ngram_lm_n3 | 100 | 0.130 | 0.221 | 102 |
| ngram_lm_n3 | 200 | 0.149 | 0.226 | 202 |
| ngram_lm_n4 | 10 | 0.029 | 0.202 | 294 |
| ngram_lm_n4 | 20 | 0.062 | 0.231 | 245 |
| ngram_lm_n4 | 50 | 0.159 | 0.188 | 125 |
| ngram_lm_n4 | 100 | 0.130 | 0.192 | 133 |
| ngram_lm_n4 | 200 | 0.135 | 0.197 | 203 |
