#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pytest -q
python scripts/run_baselines.py --config configs/default.yaml --out results
