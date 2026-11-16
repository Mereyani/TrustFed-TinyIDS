"""Phase 10 EXPLORATORY analyses, added after the test stage and labelled as such in every output.

1. host-conditional counter vs existing counter (both at the benign_val-calibrated budget);
2. matched realised false-escalation diagnostic (thresholds tuned on benign_test, oracle; from tradeoff_phase10.py);
3. trade-off curves figure (detection vs realised false escalations, window rules);
4. host heterogeneity figure.
Usage: python -I phase10/analyze_extra_phase10.py <test analysis folder>
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from analyze_phase10 import holm, boot_ci, wilcoxon_p, LABEL  # noqa: E402

GRID = [(rho, W) for rho in (0.05, 0.10) for W in (20, 50, 100, 200)]


def paired(g, a, b, value="detect"):
    rows = []
    for rho, W in GRID:
        sa = g[(g["key"] == a) & (g["W"] == W) & (g["rho"] == rho)].set_index("seed")[value]
        sb = g[(g["key"] == b) & (g["W"] == W) & (g["rho"] == rho)].set_index("seed")[value]
        d = (sa - sb).dropna()
        lo, hi = boot_ci(d)
        rows.append({"A": a, "B": b, "W": W, "rho": rho, "A_mean": sa.mean(), "B_mean": sb.mean(), "diff": d.mean(),
                     "ci_low": lo, "ci_high": hi, "seeds_A_better": int((d > 0).sum()),
                     "seeds_B_better": int((d < 0).sum()), "p_wilcoxon": wilcoxon_p(d)})
    r = pd.DataFrame(rows)
    r["p_holm"] = holm(r["p_wilcoxon"])
    return r


def main():
    an = Path(sys.argv[1])
    root = an.parent.parent
    det = pd.concat([pd.read_csv(f) for f in glob.glob(str(root / "*_phase10_test_s*" / "detection_all.csv"))])
    det = det[(det["F"] == 1000) & (det["group"] == "unseen")]
    det["key"] = det["ref"] + "|" + det["method"]
    g = det.groupby(["key", "seed", "W", "rho"], as_index=False)["detect"].mean()
    ex = paired(g, "host|W_COUNT_AU", "pooled|W_COUNT_AU")
    ex["analysis"] = "EXPLORATORY: calibrated budget (benign_val)"
    # matched diagnostic
    md = pd.concat([pd.read_csv(f) for f in glob.glob(str(root / "diagnostic_tradeoff" / "matched_fe1_*.csv"))])
    md["key"] = md["ref"] + "|" + md["method"]
    mu = md[md["group"] == "unseen"].groupby(["key", "seed", "W", "rho"], as_index=False)["detect"].mean()
    mk = md[md["group"] == "known"].groupby(["key", "seed", "W", "rho"], as_index=False)["detect"].mean()
    tabs = []
    for a, b in [("host|W_COUNT_AU", "pooled|W_COUNT_AU"), ("host|W_EVID", "host|W_COUNT_AU"),
                 ("host|W_EVID", "pooled|W_COUNT_AU"), ("host|E_CUSUM", "host|W_COUNT_AU")]:
        t = paired(mu, a, b)
        t["analysis"] = "DIAGNOSTIC (oracle): thresholds tuned on benign_test to realised false escalations <= 1/week"
        tabs.append(t)
    pd.concat([ex] + tabs).to_csv(an / "exploratory_comparisons.csv", index=False)
    summ = (mu.groupby(["key", "W", "rho"])["detect"].agg(["mean", "std"]).reset_index())
    summ["group"] = "unseen"
    summk = (mk.groupby(["key", "W", "rho"])["detect"].agg(["mean", "std"]).reset_index())
    summk["group"] = "known"
    fe = md.groupby(["key", "W"])["realised_fe"].mean().reset_index()
    pd.concat([summ, summk]).merge(fe, on=["key", "W"]).to_csv(an / "matched_fe1_summary.csv", index=False)
    # trade-off curves
    cv = pd.concat([pd.read_csv(f) for f in glob.glob(str(root / "diagnostic_tradeoff" / "curves_*.csv"))] + [md[md["method"].str.startswith("W_")].drop(columns="key")])
    cv["key"] = cv["ref"] + "|" + cv["method"]
    cu = cv[(cv["group"] == "unseen")].groupby(["key", "W", "rho", "target_fe", "seed"], as_index=False).agg(
        detect=("detect", "mean"), realised=("realised_fe", "mean"))
    cu = cu.groupby(["key", "W", "rho", "target_fe"], as_index=False)[["detect", "realised"]].mean()
    cu.to_csv(an / "tradeoff_curves_unseen.csv", index=False)
    show = ["pooled|W_COUNT_AU", "host|W_COUNT_AU", "pooled|W_EVID", "host|W_EVID", "host|W_TPM", "host|W_HC"]
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.8), sharey=True)
    for ax, (W, rho) in zip(axs, [(50, 0.10), (200, 0.05), (200, 0.10)]):
        for k in show:
            s = cu[(cu["key"] == k) & (cu["W"] == W) & (cu["rho"] == rho)].sort_values("realised")
            ref, m = k.split("|")
            ax.plot(s["realised"], 100 * s["detect"], "-" if ref == "host" else "--", marker="o", ms=3,
                    label=f"{LABEL[m]} [{ref}]")
        ax.axvline(1.0, color="0.5", lw=0.8, ls=":")
        ax.set_xscale("log")
        ax.set_xlabel("realised false escalations per host-week (benign_test)")
        ax.set_title(f"W = {W}, ρ = {rho:.2f}")
    axs[0].set_ylabel("detection, unseen families (%)")
    axs[0].legend(fontsize=6.5)
    fig.suptitle("Diagnostic: detection vs realised false escalations (thresholds swept on benign_test; F = 1000; "
                 "mean of 10 seeds; simulation)", fontsize=9)
    fig.tight_layout()
    fig.savefig(an / "fig_tradeoff.png", dpi=200)
    plt.close(fig)
    # heterogeneity figure
    hh = pd.read_csv(HERE / "results" / "host_heterogeneity.csv")
    hh = hh[hh["n"] >= 100]
    hosts = sorted(hh[hh["split"] == "benign_test"]["host"].unique(),
                   key=lambda h: -hh[(hh["host"] == h) & (hh["split"] == "benign_test")]["n"].iloc[0])
    lab = {h: f"H{i + 1}" for i, h in enumerate(hosts)}
    fig, ax = plt.subplots(figsize=(9, 3.4))
    for j, sp in enumerate(["benign_val", "benign_test"]):
        for i, h in enumerate(hosts):
            v = hh[(hh["host"] == h) & (hh["split"] == sp)]["f05"]
            if len(v):
                ax.scatter(np.full(len(v), i + (j - 0.5) * 0.25), 100 * v, s=9, color=["#2a78d6", "#d6602a"][j],
                           label=sp if i == 0 else None, alpha=0.8)
    ax.axhline(5, color="0.4", lw=0.8, ls=":")
    ax.text(len(hosts) - 0.5, 5.6, "nominal 5%", ha="right", fontsize=7, color="0.3")
    ax.set_xticks(range(len(hosts)))
    ax.set_xticklabels([lab[h] for h in hosts], fontsize=7)
    ax.set_ylabel("benign flows with p ≤ α+β (%)")
    ax.set_xlabel("benign host (≥ 100 flows), ordered by benign_test traffic")
    ax.legend(fontsize=7)
    ax.set_title("Per-host share of benign flows in the UNCERTAIN or ANOMALY region (one dot per seed)", fontsize=9)
    fig.tight_layout()
    fig.savefig(an / "fig_host_heterogeneity.png", dpi=200)
    plt.close(fig)
    pd.DataFrame({"host": hosts, "label": [lab[h] for h in hosts]}).to_csv(an / "host_labels.csv", index=False)
    sys.stdout.reconfigure(encoding="utf-8")
    print(pd.concat([ex] + tabs)[["A", "B", "W", "rho", "A_mean", "B_mean", "diff", "seeds_A_better", "p_holm"]].round(4).to_string())


if __name__ == "__main__":
    main()
