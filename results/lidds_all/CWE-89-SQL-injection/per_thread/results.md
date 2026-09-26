LID-DS 2021 / CWE-89-SQL-injection (per-thread context). Alarm = first time the running mean of the last W items exceeds a
threshold set on calibration normal recordings. Alarms before the exploit count as false alarms;
detection = first alarm after the exploit starts; delay measured from the exploit timestamp.

## Test

| Model | W | DR@1% | normal recs alarming | attacks with pre-exploit alarm | median s to detect | DR@5% | normal recs alarming @5% |
|---|---|---|---|---|---|---|---|
| ngram_n3 | 10 | 1.000 | 0.013 | 0.024 | 1.41 | 1.000 | 0.013 |
| ngram_n6 | 50 | 1.000 | 0.013 | 0.012 | 0.79 | 1.000 | 0.033 |
| ngram_lm_n3 | 10 | 1.000 | 0.020 | 0.012 | 2.49 | 1.000 | 0.062 |
| lstm_mean_s42 | 50 | 1.000 | 0.016 | 0.000 | 2.49 | 1.000 | 0.046 |

## Dev (used for choosing W)

| Model | W | dev DR@1% | dev DR@5% | dev median s to detect @1% |
|---|---|---|---|---|
| ngram_n3 | 10 | 1.000 | 1.000 | 1.36 |
| ngram_n3 | 20 | 1.000 | 1.000 | 2.47 |
| ngram_n3 | 50 | 1.000 | 1.000 | 2.47 |
| ngram_n3 | 100 | 1.000 | 1.000 | 2.47 |
| ngram_n3 | 200 | 1.000 | 1.000 | 2.47 |
| ngram_n6 | 10 | 1.000 | 1.000 | 1.32 |
| ngram_n6 | 20 | 1.000 | 1.000 | 0.83 |
| ngram_n6 | 50 | 1.000 | 1.000 | 0.77 |
| ngram_n6 | 100 | 1.000 | 1.000 | 0.77 |
| ngram_n6 | 200 | 1.000 | 1.000 | 0.77 |
| ngram_lm_n3 | 10 | 1.000 | 1.000 | 2.47 |
| ngram_lm_n3 | 20 | 1.000 | 1.000 | 2.47 |
| ngram_lm_n3 | 50 | 1.000 | 1.000 | 2.50 |
| ngram_lm_n3 | 100 | 1.000 | 1.000 | 2.50 |
| ngram_lm_n3 | 200 | 1.000 | 1.000 | 2.50 |
| lstm_mean_s42 | 10 | 1.000 | 1.000 | 2.50 |
| lstm_mean_s42 | 20 | 1.000 | 1.000 | 2.50 |
| lstm_mean_s42 | 50 | 1.000 | 1.000 | 2.48 |
| lstm_mean_s42 | 100 | 1.000 | 1.000 | 2.48 |
| lstm_mean_s42 | 200 | 1.000 | 1.000 | 2.49 |
