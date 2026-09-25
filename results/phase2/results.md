Per-family columns: detection rate at FPR 0.05 (threshold set on calibration normals).

| Model | AUC | DR@FPR 0.01 | DR@FPR 0.05 | Adduser | Hydra_FTP | Hydra_SSH | Java_Meterpreter | Meterpreter | Web_Shell |
|---|---|---|---|---|---|---|---|---|---|
| ngram_n3 | 0.695 | 0.170 | 0.327 | 0.34 | 0.40 | 0.29 | 0.26 | 0.25 | 0.39 |
| ngram_n6 | 0.827 | 0.000 | 0.216 | 0.13 | 0.33 | 0.28 | 0.10 | 0.13 | 0.21 |
| rules_median_nr0 | 0.562 | 0.044 | 0.135 | 0.09 | 0.15 | 0.23 | 0.05 | 0.03 | 0.16 |
| lstm_mean | 0.831 | 0.115 | 0.271 | 0.14 | 0.36 | 0.38 | 0.11 | 0.19 | 0.31 |
| lstm_max_window | 0.630 | 0.066 | 0.185 | 0.18 | 0.19 | 0.16 | 0.12 | 0.20 | 0.27 |
