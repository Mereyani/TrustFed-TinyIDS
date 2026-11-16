"""Apply the pre-specified Phase 10 selection rule (PROTOCOL_PHASE10.md, section 5) to validation results.

Reads every results/*_phase10_validation_s* folder, writes results/validation_selection.json and
results/validation_summary.csv. Uses known-family attacks from dev_val and benign_val only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
CANDIDATES = ["W_EVID", "E_CUSUM", "E_SR", "E_CUSUM_LEAKY", "E_SR_ADAPT"]
SIMPLICITY = {m: i for i, m in enumerate(CANDIDATES)}
BUDGET = 1.0


def main():
    dirs = sorted(RES.glob("*_phase10_validation_s*"))
    det = pd.concat([pd.read_csv(d / "detection_all.csv") for d in dirs if (d / "detection_all.csv").exists()])
    cost = pd.concat([pd.read_csv(d / "benign_cost_all.csv") for d in dirs if (d / "benign_cost_all.csv").exists()])
    seeds = sorted(det["seed"].unique())
    det = det[det["F"] == 1000]
    cost = cost[cost["F"] == 1000]
    # ρ0-independent methods were run only with the first ρ0: replicate them across ρ0 for the summary
    crit = (det[det["rho"].isin([0.05, 0.10])]
            .groupby(["seed", "ref", "method", "rho0", "W", "rho"])["detect"].mean()      # mean over families
            .groupby(["ref", "method", "rho0", "seed"]).mean())                          # mean over W, rho
    crit_m = crit.groupby(["ref", "method", "rho0"]).agg(["mean", "std", "count"])
    fe = cost.groupby(["ref", "method", "rho0", "seed"])["fe_week_mean"].mean().groupby(["ref", "method", "rho0"]).mean()
    worst = cost.groupby(["ref", "method", "rho0", "seed"])["fe_week_worst_host"].max().groupby(["ref", "method", "rho0"]).mean()
    summ = crit_m.join(fe.rename("val_fe_week_mean")).join(worst.rename("val_fe_week_worst_host_mean"))
    summ = summ.reset_index()
    summ.to_csv(RES / "validation_summary.csv", index=False)
    cand = summ[summ["method"].isin(CANDIDATES) & (summ["val_fe_week_mean"] <= BUDGET)].copy()
    best = cand["mean"].max()
    tied = cand[cand["mean"] >= best - 0.005].copy()
    tied["simplicity"] = tied["method"].map(SIMPLICITY)
    tied = tied.sort_values(["simplicity", "mean"], ascending=[True, False])
    pick = tied.iloc[0]
    out = {"seeds": [int(s) for s in seeds], "n_seed_folders": len(dirs),
           "criterion": "mean known-family detection over rho in {0.05,0.10} and W in {20,50,100,200}, F=1000",
           "constraint": "validation mean false escalations per host-week <= 1",
           "best_value": float(best), "tie_tolerance": 0.005,
           "tied_candidates": tied[["ref", "method", "rho0", "mean"]].to_dict(orient="records"),
           "selected": {"ref": pick["ref"], "method": pick["method"], "rho0": float(pick["rho0"]),
                        "criterion_mean": float(pick["mean"]), "criterion_sd": float(pick["std"])}}
    (RES / "validation_selection.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(summ.sort_values("mean", ascending=False).round(4).to_string())
    print(json.dumps(out["selected"], indent=2))


if __name__ == "__main__":
    main()
