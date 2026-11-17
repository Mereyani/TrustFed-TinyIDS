"""Phase 10b analysis (PROTOCOL_PHASE10B.md sections 4-5). Reads results_10b/*_phase10b_<SETTING>_s*/ (finished only).
No threshold is set with evaluation data: every operating point is a nominal budget calibrated on the calibration split.
Usage: python -I phase10/analyze_phase10b.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from analyze_phase10 import holm, boot_ci, wilcoxon_p  # noqa: E402

RES = HERE / "results_10b"
OUT = RES / "analysis"
SETTINGS = ["MAIN", "SWAP", "DEVICE", "DEDUP"]
GRID = [(W, rho) for rho in (0.05, 0.10) for W in (50, 100, 200)]
RULES = ["EXIST", "HCOUNT", "P10", "CUSUM-P", "CUSUM-H", "eCUSUM-H", "EWMA-P", "EWMA-H"]


def load():
    det, cost = [], []
    for d in sorted(RES.glob("*_phase10b_*")):
        c = d / "config_phase10b.json"
        if not c.exists() or "finished" not in json.loads(c.read_text(encoding="utf-8")) or "smoke" in d.name:
            continue
        det.append(pd.read_csv(d / "detection.csv"))
        cost.append(pd.read_csv(d / "benign_cost.csv"))
    det, cost = pd.concat(det, ignore_index=True), pd.concat(cost, ignore_index=True)
    cost = cost[cost["rule"].notna()].copy()
    cost["W"] = cost["W"].astype(str)
    return det, cost


def seed_det(det, setting, rule, B, F, W, rho, group="unseen"):
    s = det[(det.setting == setting) & (det.rule == rule) & (det.B == B) & (det.F == F) & (det.W == W)
            & np.isclose(det.rho, rho) & (det.group == group)]
    return s.groupby("seed")["detect"].mean()


def cost_of(cost, setting, rule, B, F, W):
    c = cost[(cost.setting == setting) & (cost.rule == rule) & (cost.B == B) & (cost.F == F)]
    w = c[c.W == str(W)]
    return w if len(w) else c[c.W == "all"]


def paired(det, setting, a, b, B=1.0, F=1000):
    rows = []
    for W, rho in GRID:
        x, y = seed_det(det, setting, a, B, F, W, rho), seed_det(det, setting, b, B, F, W, rho)
        d = (x - y).dropna()
        if len(d) < 3:
            continue
        lo, hi = boot_ci(d)
        rows.append({"setting": setting, "A": a, "B_rule": b, "W": W, "rho": rho, "n_seeds": len(d), "A_mean": x.mean(),
                     "B_mean": y.mean(), "diff": d.mean(), "ci_low": lo, "ci_high": hi, "seeds_A_better": int((d > 0).sum()),
                     "seeds_B_better": int((d < 0).sum()), "p_wilcoxon": wilcoxon_p(d)})
    r = pd.DataFrame(rows)
    if len(r):
        r["p_holm"] = holm(r["p_wilcoxon"])
    return r


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    det, cost = load()
    present = [s for s in SETTINGS if s in set(det.setting)]
    # ---------------- primary hypothesis per setting
    prim, verdict = [], {}
    for s in present:
        r = paired(det, s, "HCOUNT", "EXIST")
        prim.append(r)
        sig = int(((r["p_holm"] < 0.05) & (r["diff"] > 0)).sum()) if len(r) else 0
        fe = {W: float(cost_of(cost, s, "HCOUNT", 1.0, 1000, W).groupby("seed")["fe_mean"].mean().mean()) for W in (50, 100, 200)}
        worst = {W: int((cost_of(cost, s, "HCOUNT", 1.0, 1000, W).groupby("seed")["fe_worst"].max() > 1.0).sum())
                 for W in (50, 100, 200)}
        fe_ex = {W: float(cost_of(cost, s, "EXIST", 1.0, 1000, W).groupby("seed")["fe_mean"].mean().mean()) for W in (50, 100, 200)}
        crit_a, crit_b = sig >= 4, all(v <= 1.0 for v in fe.values() if not np.isnan(v))
        verdict[s] = {"n_comparisons": int(len(r)), "significant_HCOUNT_better": sig, "criterion_a": bool(crit_a),
                      "HCOUNT_fe_mean_by_W": fe, "criterion_b": bool(crit_b), "supported": bool(crit_a and crit_b),
                      "HCOUNT_seeds_worst_host_over_budget_by_W": worst, "EXIST_fe_mean_by_W": fe_ex,
                      "n_seeds": int(det[det.setting == s]["seed"].nunique())}
    prim = pd.concat(prim, ignore_index=True)
    prim.to_csv(OUT / "primary_HCOUNT_vs_EXIST.csv", index=False)
    others = [x for x in ("SWAP", "DEVICE", "DEDUP") if x in verdict]
    n_rep = sum(verdict[x]["supported"] for x in others)
    overall = ("reproducible advantage" if verdict.get("MAIN", {}).get("supported") and n_rep >= 2
               else "not reproduced" if verdict.get("MAIN", {}).get("supported") else "not supported in MAIN")
    summary = {"verdict_per_setting": verdict, "replications_supported": n_rep, "replications_run": others,
               "overall": overall}
    (OUT / "verdict.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    # ---------------- all rules, all budgets
    rows = []
    for s in present:
        for rule in RULES:
            for B, F in [(0.5, 1000), (1.0, 1000), (2.0, 1000), (1.0, 5000)]:
                rec = {"setting": s, "rule": rule, "B": B, "F": F}
                for W, rho in [(50, 0.10), (200, 0.05), (200, 0.10), (200, 0.25)]:
                    for g in ("unseen", "known"):
                        v = seed_det(det, s, rule, B, F, W, rho, g)
                        rec[f"{g}_W{W}_r{rho}"] = v.mean()
                        rec[f"{g}_W{W}_r{rho}_sd"] = v.std()
                for W in (50, 200):
                    c = cost_of(cost, s, rule, B, F, W)
                    if len(c):
                        g = c.groupby("seed")
                        rec[f"fe_mean_W{W}"] = g["fe_mean"].mean().mean()
                        rec[f"fe_mean_sd_W{W}"] = g["fe_mean"].mean().std()
                        rec[f"fe_worst_mean_W{W}"] = g["fe_worst"].max().mean()
                        rec[f"seeds_mean_over_W{W}"] = int((g["fe_mean"].mean() > B).sum())
                        rec[f"seeds_worst_over_W{W}"] = int((g["fe_worst"].max() > B).sum())
                rows.append(rec)
    allr = pd.DataFrame(rows)
    allr.to_csv(OUT / "all_rules_by_budget.csv", index=False)
    # ---------------- secondary: HCOUNT vs other rules at B = 1
    sec = pd.concat([paired(det, s, "HCOUNT", b) for s in present for b in ("P10", "CUSUM-H", "eCUSUM-H", "EWMA-H", "CUSUM-P", "EWMA-P")],
                    ignore_index=True)
    sec.to_csv(OUT / "secondary_HCOUNT_vs_rules.csv", index=False)
    # ---------------- delays (sequential, B = 1)
    dl = det[(det.B == 1.0) & (det.F == 1000) & det.rule.isin(["CUSUM-P", "CUSUM-H", "eCUSUM-H", "EWMA-P", "EWMA-H"])]
    dl.groupby(["setting", "rule", "W", "rho", "group"])["delay"].mean().reset_index().to_csv(OUT / "delay_sequential.csv", index=False)
    # ---------------- figure: detection vs realised false escalations, one point per nominal budget
    show = ["EXIST", "HCOUNT", "P10", "CUSUM-H", "EWMA-H", "eCUSUM-H"]
    fig, axs = plt.subplots(2, len(present), figsize=(3.6 * len(present), 6.4), squeeze=False)
    for j, s in enumerate(present):
        for i, rho in enumerate((0.05, 0.10)):
            ax = axs[i, j]
            for rule in show:
                xs, ys = [], []
                for B in (0.5, 1.0, 2.0):
                    c = cost_of(cost, s, rule, B, 1000, 200)
                    if not len(c):
                        continue
                    xs.append(c.groupby("seed")["fe_mean"].mean().mean())
                    ys.append(100 * seed_det(det, s, rule, B, 1000, 200, rho).mean())
                ax.plot(xs, ys, "-o", ms=3, lw=2.2 if rule == "HCOUNT" else 1.1, label=rule)
            ax.axvline(1.0, color="0.5", ls=":", lw=0.8)
            ax.set_xscale("log")
            ax.set_title(f"{s}, W = 200, ρ = {rho:.2f}", fontsize=9)
            ax.set_xlabel("realised false esc. / host-week", fontsize=8)
            if j == 0:
                ax.set_ylabel("unseen-family detection (%)", fontsize=8)
    axs[0, 0].legend(fontsize=6.5)
    fig.suptitle("Phase 10b: detection vs realised benign false escalations; points = nominal budgets 0.5, 1, 2 per host-week "
                 "calibrated on the calibration split only (F = 1000, mean of 10 seeds; simulation)", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_10b_budget_curves.png", dpi=200)
    plt.close(fig)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, indent=1))
    print(prim.round(4).to_string())


if __name__ == "__main__":
    main()
