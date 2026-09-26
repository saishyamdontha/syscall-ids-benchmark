Streaming protocol: alarm at the first time the running mean of the last W items
exceeds a threshold set so that the target fraction of CALIBRATION normal traces ever alarm.
W chosen per model on dev (criterion declared in config: dev DR@0.01, then @0.05, then delay).
Syscalls-to-alarm is counted from the start of the trace (ADFA-LD has no attack start time).

## Test results

| Model | W | DR@1% | normals alarming | DR@5% | normals alarming | median syscalls to alarm @1% | median % of trace seen @1% | syscalls/s |
|---|---|---|---|---|---|---|---|---|
| ngram_n3 | 200 | 0.151 | 0.010 | 0.301 | 0.060 | 202 | 55 | 1,513,470 (cpu) |
| lstm_mean_s42 | 200 | 0.152 | 0.010 | 0.266 | 0.049 | 201 | 57 | 4,096 (cuda) |
| lstm_mean_s43 | 20 | 0.071 | 0.017 | 0.227 | 0.045 | 132 | 33 | 3,809 (cuda) |
| lstm_mean_s44 | 200 | 0.141 | 0.007 | 0.284 | 0.056 | 201 | 56 | 4,033 (cuda) |

## Test, per family @1% (detection rate / median syscalls to alarm)

| Model | Adduser | Hydra_FTP | Hydra_SSH | Java_Meterpreter | Meterpreter | Web_Shell |
|---|---|---|---|---|---|---|
| ngram_n3 | 0.19 / 202 | 0.20 / 202 | 0.14 / 202 | 0.15 / 202 | 0.13 / 202 | 0.09 / 202 |
| lstm_mean_s42 | 0.18 / 204 | 0.20 / 201 | 0.17 / 201 | 0.12 / 201 | 0.13 / 201 | 0.09 / 201 |
| lstm_mean_s43 | 0.07 / 47 | 0.07 / 218 | 0.05 / 47 | 0.07 / 167 | 0.11 / 106 | 0.07 / 172 |
| lstm_mean_s44 | 0.16 / 201 | 0.20 / 201 | 0.12 / 201 | 0.14 / 201 | 0.13 / 201 | 0.09 / 201 |

## Dev (used for choosing W)

| Model | W | dev DR@1% | dev DR@5% | dev median delay @1% |
|---|---|---|---|---|
| ngram_n3 | 10 | 0.000 | 0.245 | - |
| ngram_n3 | 20 | 0.072 | 0.288 | 75 |
| ngram_n3 | 50 | 0.149 | 0.317 | 61 |
| ngram_n3 | 100 | 0.163 | 0.332 | 102 |
| ngram_n3 | 200 | 0.173 | 0.327 | 202 |
| lstm_mean_s42 | 10 | 0.038 | 0.284 | 96 |
| lstm_mean_s42 | 20 | 0.101 | 0.269 | 81 |
| lstm_mean_s42 | 50 | 0.087 | 0.250 | 98 |
| lstm_mean_s42 | 100 | 0.120 | 0.269 | 101 |
| lstm_mean_s42 | 200 | 0.154 | 0.284 | 201 |
| lstm_mean_s43 | 10 | 0.019 | 0.284 | 248 |
| lstm_mean_s43 | 20 | 0.077 | 0.279 | 106 |
| lstm_mean_s43 | 50 | 0.014 | 0.279 | 209 |
| lstm_mean_s43 | 100 | 0.019 | 0.260 | 129 |
| lstm_mean_s43 | 200 | 0.034 | 0.274 | 201 |
| lstm_mean_s44 | 10 | 0.106 | 0.288 | 96 |
| lstm_mean_s44 | 20 | 0.125 | 0.240 | 51 |
| lstm_mean_s44 | 50 | 0.139 | 0.240 | 53 |
| lstm_mean_s44 | 100 | 0.144 | 0.284 | 101 |
| lstm_mean_s44 | 200 | 0.149 | 0.312 | 201 |
