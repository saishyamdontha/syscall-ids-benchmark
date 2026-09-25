#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pytest -q
python scripts/run_baselines.py --config configs/default.yaml --out results
python scripts/run_baselines.py --config configs/phase2.yaml  --out results/phase2
python scripts/run_baselines.py --config configs/phase2b.yaml --out results/phase2b
python scripts/run_fusion.py    --config configs/fusion.yaml  --out results/fusion
