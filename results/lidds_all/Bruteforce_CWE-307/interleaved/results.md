LID-DS 2021 / Bruteforce_CWE-307 (threads interleaved). Alarm = first time the running mean of the last W items exceeds a
threshold set on calibration normal recordings. Alarms before the exploit count as false alarms;
detection = first alarm after the exploit starts; delay measured from the exploit timestamp.

## Test

| Model | W | DR@1% | normal recs alarming | attacks with pre-exploit alarm | median s to detect | DR@5% | normal recs alarming @5% |
|---|---|---|---|---|---|---|---|
| ngram_n3 | 200 | 0.112 | 0.006 | 0.010 | 0.84 | 0.408 | 0.013 |
| ngram_n6 | 200 | 0.071 | 0.006 | 0.010 | 0.74 | 0.959 | 0.049 |
| ngram_lm_n3 | 20 | 0.020 | 0.006 | 0.000 | 0.83 | 0.061 | 0.045 |
| lstm_mean_s42 | 10 | 1.000 | 0.016 | 0.010 | 0.00 | 1.000 | 0.055 |

## Dev (used for choosing W)

| Model | W | dev DR@1% | dev DR@5% | dev median s to detect @1% |
|---|---|---|---|---|
| ngram_n3 | 10 | 0.049 | 0.122 | 0.85 |
| ngram_n3 | 20 | 0.024 | 0.171 | 0.83 |
| ngram_n3 | 50 | 0.024 | 0.195 | 0.83 |
| ngram_n3 | 100 | 0.024 | 0.220 | 0.83 |
| ngram_n3 | 200 | 0.098 | 0.463 | 0.86 |
| ngram_n6 | 10 | 0.000 | 0.000 | - |
| ngram_n6 | 20 | 0.000 | 0.073 | - |
| ngram_n6 | 50 | 0.024 | 0.024 | 0.83 |
| ngram_n6 | 100 | 0.024 | 0.049 | 0.84 |
| ngram_n6 | 200 | 0.024 | 0.927 | 0.84 |
| ngram_lm_n3 | 10 | 0.000 | 0.024 | - |
| ngram_lm_n3 | 20 | 0.024 | 0.073 | 0.86 |
| ngram_lm_n3 | 50 | 0.000 | 0.049 | - |
| ngram_lm_n3 | 100 | 0.000 | 0.000 | - |
| ngram_lm_n3 | 200 | 0.000 | 0.000 | - |
| lstm_mean_s42 | 10 | 1.000 | 1.000 | 0.00 |
| lstm_mean_s42 | 20 | 1.000 | 1.000 | 0.00 |
| lstm_mean_s42 | 50 | 1.000 | 1.000 | 0.01 |
| lstm_mean_s42 | 100 | 1.000 | 1.000 | 0.01 |
| lstm_mean_s42 | 200 | 1.000 | 1.000 | 0.01 |
