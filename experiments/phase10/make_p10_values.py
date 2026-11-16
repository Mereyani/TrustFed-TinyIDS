"""Collect every Phase 10 number used in the manuscript into manuscript/en/p10_values.json and copy the figures.
Reads only phase10/results/. Usage: python -I phase10/make_p10_values.py"""
import json, shutil, sys
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent
RES = HERE / "results"
AN = sorted(RES.glob("*_phase10_test_s0"))[0] / "analysis"
OUT = HERE.parent / "manuscript" / "en"
rec = lambda df: json.loads(df.to_json(orient="records"))
V = {}
V["selection"] = json.loads((RES / "validation_selection.json").read_text(encoding="utf-8"))
vs = pd.read_csv(RES / "validation_summary.csv")
V["validation"] = rec(vs)
for name in ["primary_comparison", "detection_group_mean_sd", "benign_cost_compliance", "detection_family_mean_sd",
             "delay_group", "exploratory_comparisons", "matched_fe1_summary", "secondary_comparisons", "host_labels"]:
    V[name] = rec(pd.read_csv(AN / f"{name}.csv"))
V["overhead"] = rec(pd.read_csv(RES / "overhead.csv"))
hh = pd.read_csv(RES / "host_heterogeneity.csv")
lab = dict(pd.read_csv(AN / "host_labels.csv").values)
hh = hh[hh["host"].isin(lab)]
s = hh.groupby(["host", "split"]).agg(n=("n", "first"), f05_mean=("f05", "mean"), f05_min=("f05", "min"),
                                      f05_max=("f05", "max"), f01_mean=("f01", "mean")).reset_index()
s["label"] = s["host"].map(lab)
V["heterogeneity"] = rec(s.drop(columns="host"))
cfg = json.loads(sorted(RES.glob("*_phase10_test_s0"))[0].joinpath("config_phase10.json").read_text(encoding="utf-8"))
V["config"] = {k: cfg[k] for k in ["N_CAL_WIN", "N_EVAL_WIN", "N_CAL_STREAMS", "CAL_DAYS", "EVAL_STREAMS_PER_HOST",
                                   "EVAL_DAYS", "N_ATT", "WARMUP", "MIN_HOST_ROWS", "N_MIN_REF", "python", "numpy"]}
OUT.joinpath("p10_values.json").write_text(json.dumps(V, indent=1, ensure_ascii=False), encoding="utf-8")
for f in ["fig_detection_vs_rho.png", "fig_tradeoff.png", "fig_host_heterogeneity.png"]:
    shutil.copy2(AN / f, OUT / "figs" / ("p10_" + f))
sys.stdout.reconfigure(encoding="utf-8")
print("written", OUT / "p10_values.json", {k: (len(v) if isinstance(v, list) else "obj") for k, v in V.items()})
