"""Collect the Phase 10b numbers used in the manuscript into manuscript/en/p10b_values.json and copy the figure.
Reads only phase10/results_10b/analysis/. Usage: python -I phase10/make_p10b_values.py"""
import json, shutil, sys
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent
AN = HERE / "results_10b" / "analysis"
OUT = HERE.parent / "manuscript" / "en"
rec = lambda df: json.loads(df.to_json(orient="records"))
V = {"verdict": json.loads((AN / "verdict.json").read_text(encoding="utf-8"))}
for n in ["primary_HCOUNT_vs_EXIST", "all_rules_by_budget", "secondary_HCOUNT_vs_rules", "delay_sequential"]:
    V[n] = rec(pd.read_csv(AN / f"{n}.csv"))
(OUT / "p10b_values.json").write_text(json.dumps(V, indent=1), encoding="utf-8")
shutil.copy2(AN / "fig_10b_budget_curves.png", OUT / "figs" / "p10b_budget_curves.png")
sys.stdout.reconfigure(encoding="utf-8")
print("written", OUT / "p10b_values.json")
