"""Phase 10 test-stage analysis: tables, statistics and figures (PROTOCOL_PHASE10.md sections 6-7).

Usage: python -I phase10/analyze_phase10.py <test results folder> [<test folder 2> ...]
Writes <first folder>/analysis/*.csv, *.md, *.png and summary.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
BUDGET = 1.0
F0 = 1000
UNSEEN = ["ransomware", "xss", "mitm"]
BASE = ("pooled", "W_COUNT_AU")
LABEL = {
    "W_COUNT_AU": "Count p≤α+β (existing)", "W_COUNT_A": "Count p≤α", "W_FISHER": "Fisher window",
    "W_TPM": "Truncated product", "W_MINP": "Min-p (Tippett)", "W_HC": "Higher Criticism", "W_EVID": "LR e-value window",
    "BCUSUM": "Bernoulli CUSUM", "EWMA_FLAG": "EWMA (flag)", "EWMA_NLP": "EWMA (−log p)", "E_CUSUM": "e-CUSUM",
    "E_SR": "e-Shiryaev–Roberts", "E_CUSUM_MIX": "e-CUSUM (mixture calibrator)", "E_CUSUM_LEAKY": "leaky e-CUSUM",
    "E_SR_ADAPT": "adaptive e-SR (ρ0 mixture)", "E_CUSUM_TH": "e-CUSUM, theory threshold",
    "E_SR_TH": "e-SR, theory threshold", "E_SR_ADAPT_TH": "adaptive e-SR, theory threshold",
}


def holm(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    adj = np.empty_like(p)
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, (len(p) - r) * p[i])
        adj[i] = min(1.0, run)
    return adj


def boot_ci(d, B=10_000, seed=0):
    rng = np.random.default_rng(seed)
    d = np.asarray(d, float)
    m = rng.choice(d, (B, len(d)), replace=True).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def wilcoxon_p(d):
    d = np.asarray(d, float)
    if np.allclose(d, 0):
        return 1.0
    return float(stats.wilcoxon(d, zero_method="wilcox", alternative="two-sided").pvalue)


def main():
    dirs = [Path(a) for a in sys.argv[1:]]
    det = pd.concat([pd.read_csv(d / "detection_all.csv") for d in dirs], ignore_index=True)
    cost = pd.concat([pd.read_csv(d / "benign_cost_all.csv") for d in dirs], ignore_index=True)
    sel = json.loads((HERE / "results" / "validation_selection.json").read_text(encoding="utf-8"))["selected"]
    P10 = (sel["ref"], sel["method"])
    rho0 = sel["rho0"]
    det = det[(det["rho0"] == rho0) | ~det["method"].isin(["W_EVID", "BCUSUM", "E_CUSUM", "E_SR", "E_CUSUM_MIX",
                                                           "E_CUSUM_LEAKY", "E_CUSUM_TH", "E_SR_TH"])]
    out = dirs[0] / "analysis"
    out.mkdir(exist_ok=True)
    det["key"] = det["ref"] + "|" + det["method"]
    cost["key"] = cost["ref"] + "|" + cost["method"]
    seeds = sorted(det["seed"].unique())

    # ---------------------------------------------------------------- per-seed group detection
    g = (det.groupby(["key", "ref", "method", "seed", "W", "F", "group", "rho"], as_index=False)["detect"].mean())
    tab = (g.groupby(["key", "ref", "method", "W", "F", "group", "rho"])["detect"].agg(["mean", "std"]).reset_index())
    tab.to_csv(out / "detection_group_mean_sd.csv", index=False)
    fam = (det.groupby(["key", "ref", "method", "W", "F", "family", "rho"])["detect"].agg(["mean", "std"]).reset_index())
    fam.to_csv(out / "detection_family_mean_sd.csv", index=False)
    dl = det[det["method"].isin([m for m in det["method"].unique() if not m.startswith("W_")])]
    delay = (dl.groupby(["key", "ref", "method", "W", "F", "group", "rho"])[["delay_mean", "delay_median"]].mean()
             .reset_index())
    delay.to_csv(out / "delay_group.csv", index=False)

    # ---------------------------------------------------------------- budget compliance on benign_test
    c = cost.copy()
    c["W"] = c["W"].astype(str)
    comp = (c.groupby(["key", "ref", "method", "kind", "W", "F"])
            .agg(fe_mean=("fe_week_mean", "mean"), fe_sd=("fe_week_mean", "std"),
                 worst_mean=("fe_week_worst_host", "mean"), worst_max=("fe_week_worst_host", "max"),
                 seeds_mean_over=("fe_week_mean", lambda s: int((s > BUDGET).sum())),
                 seeds_worst_over=("fe_week_worst_host", lambda s: int((s > BUDGET).sum())),
                 host_seed_over=("hosts_over_budget", "sum"), n_seeds=("seed", "nunique"))
            .reset_index())
    comp.to_csv(out / "benign_cost_compliance.csv", index=False)
    worst_hosts = c.groupby(["key", "W", "F"])["worst_host"].agg(lambda s: s.value_counts().to_dict()).reset_index()
    worst_hosts.to_csv(out / "worst_host_identity.csv", index=False)

    # ---------------------------------------------------------------- primary comparison P1
    def series(key, W, rho, F=F0, group="unseen"):
        s = g[(g["key"] == key) & (g["W"] == W) & (g["rho"] == rho) & (g["F"] == F) & (g["group"] == group)]
        return s.set_index("seed")["detect"].reindex(seeds)

    p10k = "|".join(P10)
    basek = "|".join(BASE)
    rows = []
    for rho in [0.05, 0.10]:
        for W in [20, 50, 100, 200]:
            a, b = series(p10k, W, rho), series(basek, W, rho)
            d = (a - b).dropna()
            lo, hi = boot_ci(d)
            rows.append({"comparison": "P10 vs existing counter", "W": W, "rho": rho, "n_seeds": len(d),
                         "P10_mean": float(a.mean()), "existing_mean": float(b.mean()),
                         "diff_mean": float(d.mean()), "ci_low": lo, "ci_high": hi,
                         "seeds_P10_better": int((d > 0).sum()), "p_wilcoxon": wilcoxon_p(d)})
    prim = pd.DataFrame(rows)
    prim["p_holm"] = holm(prim["p_wilcoxon"])
    prim.to_csv(out / "primary_comparison.csv", index=False)

    # ---------------------------------------------------------------- secondary: P10 vs every other configuration
    rows = []
    for key in sorted(g["key"].unique()):
        if key == p10k:
            continue
        sub = []
        for rho in [0.05, 0.10]:
            for W in [20, 50, 100, 200]:
                a, b = series(p10k, W, rho), series(key, W, rho)
                d = (a - b).dropna()
                if len(d) < 5:
                    continue
                sub.append({"other": key, "W": W, "rho": rho, "P10_mean": float(a.mean()), "other_mean": float(b.mean()),
                            "diff_mean": float(d.mean()), "seeds_P10_better": int((d > 0).sum()),
                            "seeds_other_better": int((d < 0).sum()), "p_wilcoxon": wilcoxon_p(d)})
        if sub:
            s = pd.DataFrame(sub)
            s["p_holm_within_comparison"] = holm(s["p_wilcoxon"])
            rows.append(s)
    sec = pd.concat(rows, ignore_index=True)
    sec.to_csv(out / "secondary_comparisons.csv", index=False)

    # ---------------------------------------------------------------- research-target table (W = 200, F = 1000)
    tgt = []
    for key, name in [(basek, "existing counter (pooled)"), (p10k, "P10 (selected)")]:
        for rho in [0.01, 0.05, 0.10, 0.25, 0.50]:
            s = series(key, 200, rho)
            tgt.append({"config": name, "rho": rho, "unseen_mean": float(s.mean()), "unseen_sd": float(s.std())})
    pd.DataFrame(tgt).to_csv(out / "target_table_W200.csv", index=False)

    # ---------------------------------------------------------------- figures
    show = [basek, "host|W_COUNT_AU", "pooled|W_EVID", "host|W_EVID", "host|BCUSUM", "host|E_CUSUM",
            "host|E_SR_ADAPT", "host|W_HC", "host|EWMA_FLAG"]
    if p10k not in show:
        show.insert(1, p10k)
    fig, axs = plt.subplots(1, 4, figsize=(15, 3.8), sharey=True)
    for ax, W in zip(axs, [20, 50, 100, 200]):
        for key in show:
            s = tab[(tab["key"] == key) & (tab["W"] == W) & (tab["F"] == F0) & (tab["group"] == "unseen")]
            if len(s) == 0:
                continue
            ref, m = key.split("|")
            ls = "-" if ref == "host" else "--"
            lw = 2.6 if key == p10k else 1.2
            ax.plot(s["rho"], 100 * s["mean"], ls, marker="o", ms=3, lw=lw, label=f"{LABEL.get(m, m)} [{ref}]")
        ax.set_xscale("log")
        ax.set_title(f"W = {W}")
        ax.set_xlabel("attack share ρ in the window")
    axs[0].set_ylabel("host-level detection, unseen families (%)")
    axs[-1].legend(fontsize=6.5, loc="lower right")
    fig.suptitle("Phase 10: sparse-attack detection, thresholds calibrated on benign_val for 1 false escalation per host-week "
                 "(F = 1000 flows/day; simulation; mean of 10 seeds)", fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "fig_detection_vs_rho.png", dpi=200)
    plt.close(fig)

    summary = {"selected": sel, "seeds": [int(s) for s in seeds], "primary": prim.to_dict(orient="records")}
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(prim.round(4).to_string())
    print("output:", out)


if __name__ == "__main__":
    main()
