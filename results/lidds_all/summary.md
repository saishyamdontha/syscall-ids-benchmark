# LID-DS 2021, all scenarios (test, 1% of calibration normal recordings ever alarming)

| Scenario | Mode | Model | W | Detection | Normal recs alarming | Pre-exploit alarms | Median s to detect |
|---|---|---|---|---|---|---|---|
| Bruteforce_CWE-307 | interleaved | ngram_n3 | 200 | 0.112 | 0.006 | 0.010 | 0.84 |
| Bruteforce_CWE-307 | interleaved | ngram_n6 | 200 | 0.071 | 0.006 | 0.010 | 0.74 |
| Bruteforce_CWE-307 | interleaved | ngram_lm_n3 | 20 | 0.020 | 0.006 | 0.000 | 0.83 |
| Bruteforce_CWE-307 | interleaved | lstm_mean | 10 | 1.000 | 0.016 | 0.010 | 0.00 |
| Bruteforce_CWE-307 | per_thread | ngram_n3 | 10 | 1.000 | 0.000 | 0.000 | 0.00 |
| Bruteforce_CWE-307 | per_thread | ngram_n6 | 10 | 1.000 | 0.000 | 0.000 | 0.00 |
| Bruteforce_CWE-307 | per_thread | ngram_lm_n3 | 10 | 1.000 | 0.010 | 0.010 | 0.00 |
| Bruteforce_CWE-307 | per_thread | lstm_mean | 10 | 1.000 | 0.016 | 0.000 | 0.00 |
| CWE-89-SQL-injection | interleaved | ngram_n3 | 20 | 1.000 | 0.007 | 0.000 | 2.53 |
| CWE-89-SQL-injection | interleaved | ngram_n6 | 50 | 1.000 | 0.003 | 0.000 | 2.53 |
| CWE-89-SQL-injection | interleaved | ngram_lm_n3 | 20 | 1.000 | 0.007 | 0.024 | 2.53 |
| CWE-89-SQL-injection | interleaved | lstm_mean | 10 | 1.000 | 0.010 | 0.024 | 2.50 |
| CWE-89-SQL-injection | per_thread | ngram_n3 | 10 | 1.000 | 0.013 | 0.024 | 1.41 |
| CWE-89-SQL-injection | per_thread | ngram_n6 | 50 | 1.000 | 0.013 | 0.012 | 0.79 |
| CWE-89-SQL-injection | per_thread | ngram_lm_n3 | 10 | 1.000 | 0.020 | 0.012 | 2.49 |
| CWE-89-SQL-injection | per_thread | lstm_mean | 50 | 1.000 | 0.016 | 0.000 | 2.49 |

## Summary across scenarios (detection @1%)

| Mode | Model | Scenarios | Median | Min | Max |
|---|---|---|---|---|---|
| interleaved | lstm_mean | 2 | 1.000 | 1.000 | 1.000 |
| interleaved | ngram_lm_n3 | 2 | 0.510 | 0.020 | 1.000 |
| interleaved | ngram_n3 | 2 | 0.556 | 0.112 | 1.000 |
| interleaved | ngram_n6 | 2 | 0.536 | 0.071 | 1.000 |
| per_thread | lstm_mean | 2 | 1.000 | 1.000 | 1.000 |
| per_thread | ngram_lm_n3 | 2 | 1.000 | 1.000 | 1.000 |
| per_thread | ngram_n3 | 2 | 1.000 | 1.000 | 1.000 |
| per_thread | ngram_n6 | 2 | 1.000 | 1.000 | 1.000 |

Per-thread 3-gram >= LSTM in 2 of 2 scenarios where both ran.
