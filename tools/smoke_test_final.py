"""Run the FINAL notebooks end to end with nbclient on SYNTHETIC data, quick mode (code check only).

  python tools/smoke_test_final.py WORKDIR [--only F1_fl_teshis F2_lofo ...] [--keep] [--data FILE]

WORKDIR plays the role of the Google Drive folder. Synthetic numbers are meaningless; never report them.
"""
import argparse, os, shutil, subprocess, sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / "TrustFed-TinyIDS-Final"
ap = argparse.ArgumentParser()
ap.add_argument("work"); ap.add_argument("--only", nargs="*"); ap.add_argument("--keep", action="store_true")
ap.add_argument("--data", help="real train_test_network.csv (still quick mode: a CODE CHECK, numbers are never reported)")
a = ap.parse_args()
work = Path(a.work)
if work.exists() and not a.keep:
    shutil.rmtree(work)
(work / "data").mkdir(parents=True, exist_ok=True)
shutil.copytree(PROJ / "trustids", work / "trustids", dirs_exist_ok=True)
target = work / "data" / "train_test_network.csv"
if a.data and not target.exists():
    shutil.copy(a.data, target)
if not target.exists():
    subprocess.run([sys.executable, str(ROOT / "tests" / "make_synthetic_ton_iot.py"), str(target), "6000", "700"], check=True)
os.environ.update({"TRUSTIDS_PROJECT": str(work), "TRUSTIDS_QUICK": "1", "MPLBACKEND": "Agg"})
out = work / "executed"; out.mkdir(exist_ok=True)
names = a.only or [p.stem for p in sorted((PROJ / "notebooks").glob("*.ipynb"))]
for name in names:
    nb = nbformat.read(PROJ / "notebooks" / f"{name}.ipynb", as_version=4)
    print("running", name, flush=True)
    NotebookClient(nb, timeout=7200, kernel_name="python3", resources={"metadata": {"path": str(work)}}).execute()
    nbformat.write(nb, out / f"{name}.ipynb")
    print("  ok", flush=True)
print("ALL NOTEBOOKS EXECUTED")
