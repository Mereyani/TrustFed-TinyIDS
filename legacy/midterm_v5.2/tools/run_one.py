"""Run selected notebooks in an existing WORKDIR (e.g. to resume, or to add 04b to a finished run).

  python tools/run_one.py WORKDIR 04b_uncertain_resolution [02_baseline_models ...] [--full] [--sync-code]

--sync-code copies the current trustids/ package into WORKDIR first (additive changes only)."""
import argparse, os, shutil, sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("work"); ap.add_argument("names", nargs="+")
ap.add_argument("--full", action="store_true"); ap.add_argument("--sync-code", action="store_true")
a = ap.parse_args()
work = Path(a.work)
if a.sync_code:
    shutil.copytree(ROOT / "trustids", work / "trustids", dirs_exist_ok=True)
os.environ["TRUSTIDS_PROJECT"] = str(work)
os.environ["TRUSTIDS_QUICK"] = "0" if a.full else "1"
os.environ["MPLBACKEND"] = "Agg"
(work / "executed").mkdir(exist_ok=True)
for name in a.names:
    nb_path = ROOT / "notebooks" / f"{name}.ipynb"
    nb = nbformat.read(nb_path, as_version=4)
    print("running", nb_path.name, flush=True)
    NotebookClient(nb, timeout=7200, kernel_name="python3", resources={"metadata": {"path": str(work)}}).execute()
    nbformat.write(nb, work / "executed" / nb_path.name)
    print("  ok", flush=True)
