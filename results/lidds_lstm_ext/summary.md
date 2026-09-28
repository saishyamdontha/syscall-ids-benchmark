# LID-DS 2021, all scenarios (test, 1% of calibration normal recordings ever alarming)

| Scenario | Mode | Model | W | Detection | Normal recs alarming | Pre-exploit alarms | Median s to detect |
|---|---|---|---|---|---|---|---|
| CVE-2017-7529 | interleaved | lstm_mean | 20 | 1.000 | 0.021 | 0.036 | 0.00 |
| CVE-2017-7529 | per_thread | lstm_mean | 20 | 1.000 | 0.017 | 0.024 | 0.00 |
| CVE-2019-5418 | per_thread | lstm_mean | 200 | 0.000 | 0.020 | 0.000 | - |
| CVE-2020-9484 | interleaved | lstm_mean | 10 | 1.000 | 0.010 | 0.012 | 2.04 |
| CVE-2020-9484 | per_thread | lstm_mean | 10 | 1.000 | 0.013 | 0.000 | 2.04 |

## Summary across scenarios (detection @1%)

| Mode | Model | Scenarios | Median | Min | Max |
|---|---|---|---|---|---|
| interleaved | lstm_mean | 2 | 1.000 | 1.000 | 1.000 |
| per_thread | lstm_mean | 3 | 1.000 | 0.000 | 1.000 |
