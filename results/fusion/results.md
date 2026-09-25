Protocol v2. Selection criterion (declared in config): dev DR@0.01, tiebreak @0.05.
Chosen: **ngram_n3**

| Candidate | dev DR@1% | dev DR@5% | TEST AUC | TEST DR@1% (FPR) | TEST DR@5% (FPR) |
|---|---|---|---|---|---|
| ngram_n3 **(selected on dev)** | 0.183 | 0.389 | 0.700 | 0.165 (0.010) | 0.320 (0.057) |
| min_p(ngram_n3+ngram_n6) | 0.183 | 0.312 | 0.835 | 0.165 (0.010) | 0.297 (0.052) |
| min_p(ngram_n3+lstm_mean_s42) | 0.135 | 0.346 | 0.830 | 0.123 (0.009) | 0.316 (0.059) |
| fisher(ngram_n3+ngram_n6) | 0.135 | 0.322 | 0.818 | 0.136 (0.013) | 0.310 (0.058) |
| min_p(ngram_n3+ngram_n6+lstm_mean_s42) | 0.135 | 0.308 | 0.830 | 0.123 (0.009) | 0.292 (0.053) |
| lstm_mean_s42 | 0.130 | 0.341 | 0.836 | 0.106 (0.007) | 0.305 (0.057) |
| fisher(ngram_n3+lstm_mean_s42) | 0.130 | 0.341 | 0.814 | 0.113 (0.008) | 0.312 (0.058) |
| min_p(ngram_n6+lstm_mean_s42) | 0.130 | 0.231 | 0.833 | 0.106 (0.007) | 0.232 (0.053) |
| fisher(ngram_n3+ngram_n6+lstm_mean_s42) | 0.125 | 0.332 | 0.826 | 0.108 (0.006) | 0.307 (0.058) |
| fisher(ngram_n6+lstm_mean_s42) | 0.125 | 0.260 | 0.836 | 0.106 (0.006) | 0.240 (0.058) |
| ngram_n6 | 0.000 | 0.207 | 0.834 | 0.000 (0.000) | 0.225 (0.045) |
