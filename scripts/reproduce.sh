#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f data/raw/syscall_32.tbl ] || curl -sS -o data/raw/syscall_32.tbl \
  https://raw.githubusercontent.com/torvalds/linux/v6.6/arch/x86/entry/syscalls/syscall_32.tbl
python -m pytest -q
python scripts/run_baselines.py --config configs/default.yaml --out results
python scripts/run_baselines.py --config configs/phase2.yaml  --out results/phase2
python scripts/run_baselines.py --config configs/phase2b.yaml --out results/phase2b
python scripts/run_fusion.py    --config configs/fusion.yaml  --out results/fusion
python scripts/run_stream.py    --config configs/stream_seeds.yaml --out results/gpu/stream_seeds
python scripts/run_explain.py   --config configs/explain.yaml --out results/explain
python scripts/syscall_presence.py > results/explain/syscall_presence.txt
