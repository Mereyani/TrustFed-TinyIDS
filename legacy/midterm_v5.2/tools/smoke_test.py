"""Run notebooks 00-04 end to end with nbclient.

  python tools/smoke_test.py WORKDIR                      synthetic data, quick mode (code check only)
  python tools/smoke_test.py WORKDIR --data FILE --full   real data, full configuration (10 seeds)

WORKDIR plays the role of the Google Drive project folder. Executed notebooks (with outputs)
are written to WORKDIR/executed/. Synthetic numbers are meaningless; never report them.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--data", help="real train_test_network.csv (default: synthetic)")
    ap.add_argument("--full", action="store_true", help="full configuration instead of quick mode")
    ap.add_argument("--overwrite", action="store_true",
                    help="allow deleting an existing WORKDIR that already holds results (runs/ or executed/)")
    a = ap.parse_args()
    work = Path(a.work)
    if work.exists():
        has_results = (work / "runs").exists() or (work / "executed").exists()
        if has_results and not a.overwrite:
            # an interrupted rerun once deleted the results a proposal referenced; never again silently
            sys.exit(f"{work} already contains results. Use a new WORKDIR or pass --overwrite.")
        shutil.rmtree(work)
    (work / "data").mkdir(parents=True)
    shutil.copytree(ROOT / "trustids", work / "trustids")
    target = work / "data" / "train_test_network.csv"
    if a.data:
        shutil.copy(a.data, target)
    else:
        subprocess.run([sys.executable, str(ROOT / "tests" / "make_synthetic_ton_iot.py"), str(target), "6000", "700"], check=True)
    os.environ["TRUSTIDS_PROJECT"] = str(work)
    os.environ["TRUSTIDS_QUICK"] = "0" if a.full else "1"
    os.environ["MPLBACKEND"] = "Agg"
    out = work / "executed"
    out.mkdir()
    for nb_path in sorted((ROOT / "notebooks").glob("0*.ipynb")):
        nb = nbformat.read(nb_path, as_version=4)
        print("running", nb_path.name, flush=True)
        NotebookClient(nb, timeout=7200, kernel_name="python3",
                       resources={"metadata": {"path": str(work)}}).execute()
        nbformat.write(nb, out / nb_path.name)
        print("  ok", flush=True)
    print("ALL NOTEBOOKS EXECUTED")


if __name__ == "__main__":
    main()
