"""Final-phase evaluation helpers: one metric row per configuration, and seed summaries.

Every metric is computed from the same evaluation sets as the midterm (benign_test, dev_test = known
families, heldout_test = unseen families); nothing is tuned on these sets.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import conformal as C
from . import metrics as MT


def config_row(name: str, cal, bt, kn, ho, cfg, *, three_way: bool, model: str, seed: int,
               coll_ho: np.ndarray | None = None) -> dict:
    """All performance metrics of one configuration (A1-A6 style).

    three_way=False -> binary rule at alpha (ANOMALY vs NORMAL), as A1, A2, A4;
    three_way=True  -> conformal three-way rule (alpha, beta), as A3, A5, A6.
    model selects the p-value type ('iforest', 'int8' -> randomized p-values, ties)."""
    a = cfg.alpha
    b = cfg.beta if three_way else 0.0
    pb, pk, ph = (C.pvalues(cal, x, seed=seed, model=model) for x in (bt, kn, ho))
    db, dk, dh = (C.decide(p, a, b) for p in (pb, pk, ph))
    y = np.r_[np.zeros(len(db)), np.ones(len(dk) + len(dh))].astype(bool)
    d = np.r_[db, dk, dh]
    yh = np.r_[np.zeros(len(db)), np.ones(len(dh))].astype(bool)
    dhh = np.r_[db, dh]
    s_h = np.r_[-pb, -ph]
    row = {"yapılandırma": name, "tohum": seed,
           "normal_FPR": np.mean(db == C.ANOMALY), "normal_UNCERTAIN": np.mean(db == C.UNCERTAIN),
           "bilinen_ANOMALY": np.mean(dk == C.ANOMALY),
           "görülmemiş_ANOMALY": np.mean(dh == C.ANOMALY), "görülmemiş_UNCERTAIN": np.mean(dh == C.UNCERTAIN),
           "görülmemiş_kaçan": np.mean(dh == C.NORMAL)}
    if coll_ho is not None:
        row["görülmemiş_ANOMALY_çakışma_kaçmış"] = np.mean((dh == C.ANOMALY) & ~coll_ho)
    bm = MT.binary_metrics(yh, s_h, dhh == C.ANOMALY)
    row.update({"precision_görülmemiş": bm["precision"], "recall_görülmemiş": bm["recall"], "f1_görülmemiş": bm["f1"]})
    bm1 = MT.binary_metrics(yh, s_h, dhh == C.ANOMALY, pi=0.01)
    row["precision_görülmemiş_π=%1"] = bm1["precision"]
    for pi, tag in [(None, ""), (0.01, "_π=%1")]:
        sm = MT.selective_metrics(y, d, pi)
        row[f"coverage{tag}"] = sm["coverage"]
        row[f"selective_risk{tag}"] = sm["selective_risk"]
    return row


RC_GRID = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]


def rc_rows(name: str, cal, bt, kn, ho, cfg, *, model: str, seed: int, grid=RC_GRID) -> list:
    """Risk-coverage curve of one model (alpha fixed, beta swept), read at fixed coverage levels so that
    curves of different seeds can be averaged. Evaluation set = benign test + known + unseen attacks,
    at the test-set attack share and re-weighted to an attack prevalence of 1%.
    A coverage level the model cannot reach (below its ANOMALY share) is left empty (NaN)."""
    pb, pk, ph = (C.pvalues(cal, x, seed=seed, model=model) for x in (bt, kn, ho))
    y = np.r_[np.zeros(len(pb)), np.ones(len(pk) + len(ph))].astype(bool)
    p = np.r_[pb, pk, ph]
    rows = []
    for pi, tag in [(None, "test kümesi"), (0.01, "π=%1")]:
        cur = MT.risk_coverage_curve(y, p, cfg.alpha, pi=pi).dropna(subset=["selective_risk"])
        cur = cur.groupby("coverage", as_index=False)["selective_risk"].mean().sort_values("coverage")
        cov, sr = cur["coverage"].to_numpy(), cur["selective_risk"].to_numpy()
        for c in grid:
            ok = len(cov) > 0 and cov.min() - 1e-12 <= c <= cov.max() + 1e-12
            rows.append({"model": name, "tohum": seed, "yaygınlık": tag, "kapsama": c,
                         "seçici_risk": float(np.interp(c, cov, sr)) if ok else np.nan})
    return rows


def seed_summary(df: pd.DataFrame, by: list, cols: list, repeats: int = 1000) -> pd.DataFrame:
    """Mean, std, bootstrap 95% CI of the mean (over seeds) and number of seeds, per group.
    The CI reflects training-seed variability only (fixed data split), as in the midterm."""
    out = []
    for key, g in df.groupby(by, sort=False):
        key = key if isinstance(key, tuple) else (key,)
        for c in cols:
            v = g[c].dropna().to_numpy(dtype=float)
            if len(v) == 0:
                continue
            lo, hi = MT.bootstrap_ci(v, repeats, 0) if len(v) > 1 else (np.nan, np.nan)
            out.append({**dict(zip(by, key)), "metrik": c, "ortalama": v.mean(), "std": v.std(ddof=1) if len(v) > 1 else np.nan,
                        "ga95_alt": lo, "ga95_üst": hi, "tohum_sayısı": len(v)})
    return pd.DataFrame(out)


def paired_tests(df: pd.DataFrame, key: str, pairs: list, metric: str, seed_col: str = "tohum") -> pd.DataFrame:
    """Paired Wilcoxon over seeds for each (a, b) pair of `key` values, Holm-corrected across pairs."""
    from scipy import stats
    rows = []
    for a, b in pairs:
        A = df[df[key] == a].set_index(seed_col)[metric]
        B = df[df[key] == b].set_index(seed_col)[metric]
        common = A.index.intersection(B.index)
        if len(common) < 5:
            continue
        diff = (A.loc[common] - B.loc[common]).to_numpy(dtype=float)
        p = 1.0 if np.allclose(diff, 0) else float(stats.wilcoxon(diff).pvalue)
        rows.append({"a": a, "b": b, "metrik": metric, "ortalama_fark_a-b": diff.mean(),
                     "a_daha_büyük_tohum": int(np.sum(diff > 0)), "tohum": len(common), "p_raw": p})
    res = pd.DataFrame(rows)
    if len(res):
        res = res.sort_values("p_raw").reset_index(drop=True)
        m, run, adj = len(res), 0.0, []
        for i, p in enumerate(res["p_raw"]):
            run = max(run, min(1.0, (m - i) * p)); adj.append(run)
        res["p_holm"] = adj
    return res
