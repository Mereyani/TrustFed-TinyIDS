"""Descriptive: per-host share of benign flows with pooled p <= alpha+beta and p <= alpha, benign_val vs
benign_test, seeds 0-9 (explains the host-level budget violations). Output: results/host_heterogeneity.csv"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_phase10 as RP
cfg, rows, prep = RP.load_common()
out = []
for seed in range(10):
    p, _, _ = RP.seed_pvalues(rows, seed)
    for sp in ["benign_val", "benign_test"]:
        m = (rows["split"] == sp).to_numpy()
        d = pd.DataFrame({"host": rows["host"][m], "p": p[m]})
        g = d.groupby("host")["p"].agg(n="size", f05=lambda x: (x <= 0.05).mean(), f01=lambda x: (x <= 0.01).mean())
        g["seed"], g["split"] = seed, sp
        out.append(g.reset_index())
df = pd.concat(out)
df.to_csv(HERE / "results" / "host_heterogeneity.csv", index=False)
s = df.groupby(["split", "host"]).agg(n=("n", "first"), f05_mean=("f05", "mean"), f05_min=("f05", "min"), f05_max=("f05", "max"),
                                      f01_mean=("f01", "mean")).reset_index()
s = s[s.n >= 100].pivot_table(index="host", columns="split", values=["n", "f05_mean", "f05_max", "f01_mean"])
sys.stdout.reconfigure(encoding="utf-8")
print(s.round(3).to_string())
