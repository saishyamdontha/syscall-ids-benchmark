"""Copy scenario zips out of the LID-DS 2021 bundle without extracting anything else.

Usage: python scripts/extract_scenarios.py <bundle.zip> [Scenario ...]   (no names = all)
Skips scenarios already present with the right size, so it is safe to rerun.
"""
import shutil
import sys
import zipfile
from pathlib import Path

out = Path("data/raw/lidds")
out.mkdir(parents=True, exist_ok=True)
bundle = zipfile.ZipFile(sys.argv[1])
wanted = set(sys.argv[2:])
members = [i for i in bundle.infolist()
           if i.filename.endswith(".zip") and "__MACOSX" not in i.filename
           and i.filename.count("/") <= 1]            # top-level scenario zips only
print("scenarios in bundle:", sorted(Path(i.filename).stem for i in members))
for info in members:
    name = Path(info.filename).name
    if wanted and Path(name).stem not in wanted:
        continue
    dest = out / name
    if dest.exists() and dest.stat().st_size == info.file_size:
        print(f"  {name}: already there")
        continue
    print(f"  {name}: extracting {info.file_size / 1e9:.2f} GB ...", flush=True)
    with bundle.open(info) as src, open(dest, "wb") as dst:
        shutil.copyfileobj(src, dst, length=16 * 1024 * 1024)
print("done")
