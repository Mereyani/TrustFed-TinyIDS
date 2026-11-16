"""Check that the saved Colab scores reproduce the stored F5 (existing host counter) results exactly.
Runs trustids.sparse.evaluate_seed with the F5 seed RNG and compares every numeric column with the stored
per-seed file. Output: results/f5_reproduction_check.csv"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_phase10 as RP  # resolves code and artifact locations for both layouts
from trustids.config import Config
from trustids import sparse as SPR
cfg = Config.load(RP.F5_CFG)
ART = RP.ART
ROWS = pd.read_csv(ART / "resolution" / "host_rows.csv.gz", keep_default_na=False)
ROWS["split"] = ROWS["split"].replace({"": None})
ROWS = ROWS[ROWS["split"].isin(["benign_val", "benign_test", "dev_test", "heldout_test"])].reset_index(drop=True)
out = []
for seed in range(10):
    z = np.load(ART / "scores" / f"seed{seed}.npz")
    S = {sp: z["ae__" + sp] for sp in ["benign_cal", "benign_val", "benign_test", "dev_test", "heldout_test"]}
    new = pd.DataFrame(SPR.evaluate_seed(ROWS, S, cfg, seed, np.random.default_rng(50_000 + seed)))
    ref = pd.read_csv(sorted((ART / "sparse").glob(f"seed{seed}_*.csv"))[0])
    num = [c for c in ref.columns if ref[c].dtype.kind in "fi"]
    d = float(np.nanmax(np.abs(new[num].to_numpy(float) - ref[num].to_numpy(float))))
    out.append({"seed": seed, "rows": len(new), "rows_stored": len(ref), "max_abs_diff": d})
    print(out[-1], flush=True)
pd.DataFrame(out).to_csv(HERE / "results" / "f5_reproduction_check.csv", index=False)
