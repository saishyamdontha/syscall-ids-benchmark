LID-DS 2021 / CWE-89-SQL-injection (threads interleaved). Alarm = first time the running mean of the last W items exceeds a
threshold set on calibration normal recordings. Alarms before the exploit count as false alarms;
detection = first alarm after the exploit starts; delay measured from the exploit timestamp.

## Test

| Model | W | DR@1% | normal recs alarming | attacks with pre-exploit alarm | median s to detect | DR@5% | normal recs alarming @5% |
|---|---|---|---|---|---|---|---|
| ngram_n3 | 20 | 1.000 | 0.007 | 0.000 | 2.53 | 1.000 | 0.013 |
| ngram_n6 | 50 | 1.000 | 0.003 | 0.000 | 2.53 | 1.000 | 0.033 |
| ngram_lm_n3 | 20 | 1.000 | 0.007 | 0.024 | 2.53 | 1.000 | 0.056 |
| lstm_mean_s42 | 10 | 1.000 | 0.010 | 0.024 | 2.50 | 1.000 | 0.056 |

## Dev (used for choosing W)

| Model | W | dev DR@1% | dev DR@5% | dev median s to detect @1% |
|---|---|---|---|---|
| ngram_n3 | 10 | 1.000 | 1.000 | 2.50 |
| ngram_n3 | 20 | 1.000 | 1.000 | 2.50 |
| ngram_n3 | 50 | 1.000 | 1.000 | 2.50 |
| ngram_n3 | 100 | 1.000 | 1.000 | 2.50 |
| ngram_n3 | 200 | 1.000 | 1.000 | 2.50 |
| ngram_n6 | 10 | 0.000 | 0.000 | - |
| ngram_n6 | 20 | 0.000 | 0.000 | - |
| ngram_n6 | 50 | 1.000 | 1.000 | 2.50 |
| ngram_n6 | 100 | 0.972 | 0.972 | 12.77 |
| ngram_n6 | 200 | 0.028 | 0.667 | 12.70 |
| ngram_lm_n3 | 10 | 0.083 | 1.000 | 12.67 |
| ngram_lm_n3 | 20 | 1.000 | 1.000 | 2.50 |
| ngram_lm_n3 | 50 | 1.000 | 1.000 | 2.50 |
| ngram_lm_n3 | 100 | 0.972 | 0.972 | 12.77 |
| ngram_lm_n3 | 200 | 0.972 | 0.972 | 12.77 |
| lstm_mean_s42 | 10 | 1.000 | 1.000 | 2.49 |
| lstm_mean_s42 | 20 | 1.000 | 1.000 | 2.50 |
| lstm_mean_s42 | 50 | 1.000 | 1.000 | 2.50 |
| lstm_mean_s42 | 100 | 1.000 | 1.000 | 2.50 |
| lstm_mean_s42 | 200 | 1.000 | 1.000 | 2.50 |
