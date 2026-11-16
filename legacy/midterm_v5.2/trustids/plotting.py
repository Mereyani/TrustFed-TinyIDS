"""Figures used in the midterm report. Every function saves to `path` if given."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def _finish(fig, path):
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig


def score_distributions(scores_by_group: dict, title: str, path=None, log=True):
    fig, ax = plt.subplots(figsize=(7, 4))
    allv = np.concatenate([v for v in scores_by_group.values() if len(v)])
    lo, hi = np.quantile(allv, 0.001), np.quantile(allv, 0.999)
    bins = np.logspace(np.log10(max(lo, 1e-8)), np.log10(hi), 80) if log else np.linspace(lo, hi, 80)
    for name, v in scores_by_group.items():
        if len(v):
            ax.hist(v, bins=bins, histtype="step", density=True, label=f"{name} (n={len(v)})")
    if log:
        ax.set_xscale("log")
    ax.set_xlabel("anomali skoru s(x)")
    ax.set_ylabel("yoğunluk")
    ax.set_title(title)
    ax.legend(fontsize=8)
    return _finish(fig, path)


def validity_histogram(realized: np.ndarray, level: float, theory_dist, n_test: int, title: str, path=None):
    """Realised benign rate over resplits vs the theoretical Beta-Binomial law."""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(realized, bins=30, density=True, alpha=0.6, label="gerçekleşen (yeniden bölmeler)")
    xs = np.arange(theory_dist.ppf(0.0005), theory_dist.ppf(0.9995) + 1)
    ax.plot(xs / n_test, theory_dist.pmf(xs) * n_test, lw=1.5, label="teori (Beta-Binom)")
    ax.axvline(level, color="k", ls="--", lw=1, label=f"bütçe = {level}")
    ax.set_xlabel("normal testte gerçekleşen oran")
    ax.set_title(title)
    ax.legend(fontsize=8)
    return _finish(fig, path)


def validity_qq(realized: np.ndarray, theory_dist, n_test: int, title: str, path=None):
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    q = np.linspace(0.01, 0.99, len(realized))
    emp = np.sort(realized)
    th = theory_dist.ppf(q) / n_test
    ax.plot(th, emp, ".", ms=3)
    lim = [min(th.min(), emp.min()), max(th.max(), emp.max())]
    ax.plot(lim, lim, "k--", lw=1)
    ax.set_xlabel("teorik yüzdelik")
    ax.set_ylabel("deneysel yüzdelik")
    ax.set_title(title)
    return _finish(fig, path)


def risk_coverage(curves: dict, title: str, path=None, marker_points: dict | None = None):
    fig, ax = plt.subplots(figsize=(6, 4))
    for name, df in curves.items():
        ax.plot(df["coverage"], df["selective_risk"], lw=1.5, label=name)
    for name, (cov, sr) in (marker_points or {}).items():
        ax.plot(cov, sr, "o", ms=6, label=name)
    ax.set_xlabel("kapsama (otomatik karar payı)")
    ax.set_ylabel("seçici risk (karar verilenlerde hata)")
    ax.set_title(title)
    ax.legend(fontsize=8)
    return _finish(fig, path)


def reliability_bins(table, title: str, path=None):
    fig, ax = plt.subplots(figsize=(7, 3.5))
    labels = [str(b) for b in table["bin"]]
    ax.bar(range(len(table)), table["attack_share"], label="saldırı payı")
    ax.plot(range(len(table)), table["error_rate"], "ko-", ms=4, label="karar hatası")
    ax.set_xticks(range(len(table)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
    ax.set_xlabel("konformal p-değeri aralığı")
    ax.set_title(title)
    ax.legend(fontsize=8)
    return _finish(fig, path)


def family_bars(df, title: str, path=None):
    d = df[df["family"] != "macro-average"]
    fig, ax = plt.subplots(figsize=(8, 3.8))
    x = np.arange(len(d))
    ax.bar(x, d["anomaly_rate"], label="ANOMALY")
    ax.bar(x, d["uncertain_rate"], bottom=d["anomaly_rate"], label="UNCERTAIN")
    ax.bar(x, d["normal_rate"], bottom=d["anomaly_rate"] + d["uncertain_rate"], label="NORMAL")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{f}\n({g})" for f, g in zip(d["family"], d["group"])], fontsize=7)
    ax.set_ylabel("örnek payı")
    ax.set_title(title)
    ax.legend(fontsize=8, ncol=3)
    return _finish(fig, path)
