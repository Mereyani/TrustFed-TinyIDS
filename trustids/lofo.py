"""Leave-one-family-out (LOFO) evaluation: professor's feedback item 3, pre-registered as E7 in proposal v6 §7a.3.

Protocol (frozen before any confirmatory run):
* folds: each of the 9 attack families is held out once; the other 8 are the dev (known) families;
* fresh training seeds 10-19; split seed unchanged; AE size fixed at 32-16-8 (no per-fold selection);
* comparison set: AE (three-way, flow level); AE + Rung 2 (host counter); AE + Rung 1 + Rung 2;
  RF alone (trained on the 8 known families) at matched benign false-alarm rate;
* windows W in {20, 50, 100}, F in {1000, 5000} flows/day, rho in {0.10, 0.25, 0.50, 1.00};
  version B has no timestamps, so host windows are a SIMULATED stream.

Why the AE is trained once per seed and reused in every fold: the AE sees benign_train only, and the benign
split is drawn before any attack family is assigned (data.make_splits), so the benign data are identical in
every fold. The notebook checks this (assert) instead of assuming it.

Deviation from §7a.3, stated openly: §7a.3 lists per-client (Mondrian) calibration of k*. There are no FL
clients in this centralized LOFO run, so k* is calibrated on benign_val windows as in the midterm notebook 04b.
"""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd

from . import conformal as C
from . import resolution as R


def all_families(cfg) -> list:
    return list(cfg.dev_families) + list(cfg.heldout_families)


def fold_config(cfg, family: str):
    f = copy.deepcopy(cfg)
    fams = all_families(cfg)
    f.heldout_families = [family]
    f.dev_families = [x for x in fams if x != family]
    f.check()
    return f


def same_benign(P_a: dict, P_b: dict) -> bool:
    keys = ["benign_train", "benign_val", "benign_cal", "benign_test"]
    return all(P_a["X"][k].shape == P_b["X"][k].shape and np.array_equal(P_a["X"][k], P_b["X"][k]) for k in keys)


def fit_rf(P: dict, cfg, seed: int):
    """Rung 1 / RF-alone baseline: supervised, trained on benign_train + dev_val (known families of this fold)."""
    from sklearn.ensemble import RandomForestClassifier
    X = P["X"]
    rf = RandomForestClassifier(n_estimators=cfg.lofo_rf_trees, random_state=seed, n_jobs=-1, class_weight="balanced")
    rf.fit(np.r_[X["benign_train"], X["dev_val"]], np.r_[np.zeros(len(X["benign_train"])), np.ones(len(X["dev_val"]))])
    proba = {sp: rf.predict_proba(X[sp])[:, 1] for sp in ["benign_val", "benign_cal", "benign_test", "dev_test", "heldout_test"]}
    cal = proba["benign_cal"]
    thr = {"alpha": float(np.quantile(cal, 1 - cfg.alpha, method="higher")),
           "alpha+beta": float(np.quantile(cal, 1 - cfg.alpha - cfg.beta, method="higher"))}
    return proba, thr


def flow_level(P: dict, S: dict, rf: dict, thr: dict, cfg, family: str, seed: int) -> dict:
    """Flow-level rates for the held-out family and for benign test traffic."""
    cal = S["benign_cal"]
    pb = C.pvalues(cal, S["benign_test"], seed=seed, model="ae")
    ph = C.pvalues(cal, S["heldout_test"], seed=seed, model="ae")
    m = P["types"]["heldout_test"] == family
    ph, rh, coll = ph[m], rf["heldout_test"][m], P["collision"]["heldout_test"][m]
    rb = rf["benign_test"]
    a, ab = cfg.alpha, cfg.alpha + cfg.beta
    unc_h, unc_b = (ph > a) & (ph <= ab), (pb > a) & (pb <= ab)
    return {
        "aile": family, "tohum": seed, "n_vektör": int(m.sum()),
        "AE_ANOMALY": np.mean(ph <= a), "AE_UNCERTAIN": np.mean(unc_h), "AE_kaçan": np.mean(ph > ab),
        "AE_ANOMALY_çakışma_kaçmış": np.mean((ph <= a) & ~coll),
        "AE_kaçan+ertelenen": 1 - np.mean(ph <= a),
        "normal_AE_ANOMALY": np.mean(pb <= a), "normal_AE_UNCERTAIN": np.mean(unc_b),
        "RF_tek_recall_α": np.mean(rh > thr["alpha"]), "normal_RF_FPR_α": np.mean(rb > thr["alpha"]),
        "RF_tek_recall_α+β": np.mean(rh > thr["alpha+beta"]), "normal_RF_FPR_α+β": np.mean(rb > thr["alpha+beta"]),
        "AE+Basamak1_recall": np.mean((ph <= a) | (unc_h & (rh > thr["alpha"]))),
        "normal_AE+Basamak1_FPR": np.mean((pb <= a) | (unc_b & (rb > thr["alpha"]))),
    }


def host_level(ROWS: pd.DataFrame, P: dict, S: dict, rf: dict, thr: dict, cfg, family: str, seed: int, rng) -> list:
    """Rung 2 (host counter) with and without Rung 1, for the held-out family of this fold."""
    cal = S["benign_cal"]
    sp_list = ["benign_val", "benign_test", "dev_test", "heldout_test"]
    p = R.row_values(ROWS, {sp: C.pvalues(cal, S[sp], seed=seed, model="ae") for sp in sp_list})
    r = R.row_values(ROWS, {sp: rf[sp] for sp in sp_list})
    a, ab = cfg.alpha, cfg.alpha + cfg.beta
    with np.errstate(invalid="ignore"):
        flags = {"AE + Basamak 2": p <= ab,
                 "AE + Basamak 1 + Basamak 2": (p <= a) | ((p > a) & (p <= ab) & (r > thr["alpha"]))}
    g_val = R.host_groups(ROWS, (ROWS["split"] == "benign_val").to_numpy())
    g_ben = R.host_groups(ROWS, (ROWS["split"] == "benign_test").to_numpy())
    ben_all = np.concatenate(list(g_ben.values()))
    m_f = ((ROWS["split"] == "heldout_test") & (ROWS["type"] == family)).to_numpy()
    att_ix = np.where(m_f)[0]
    sizes = ROWS.groupby(["split", "host", "type"])["host"].transform("size").to_numpy()
    out = []
    for W in cfg.resolution_windows:
        cal_w, _ = R.sample_windows(g_val, W, cfg.resolution_cal_windows, rng)
        ev_w, ev_h = R.sample_windows(g_ben, W, cfg.resolution_eval_windows, rng)
        if len(cal_w) == 0 or len(ev_w) == 0:
            continue
        pure, _ = R.disjoint_windows(R.host_groups(ROWS, m_f), W, rng)
        mixed = {rho: R.mixed_windows(att_ix, ben_all, W, rho, 300, rng) for rho in cfg.resolution_rho if len(att_ix) >= W}
        unc_f = m_f & (p > a) & (p <= ab)
        dead = float(np.mean(sizes[unc_f] < W)) if unc_f.any() else 0.0
        for F in cfg.resolution_flows_per_day:
            a_w = R.window_budget(cfg.resolution_budget_per_week, W, F)
            for sysname, flag in flags.items():
                k = R.k_threshold(R.counts(flag, cal_w), a_w)
                esc = R.counts(flag, ev_w) >= k
                host_rate = pd.Series(esc).groupby(ev_h).mean()
                row = {"aile": family, "tohum": seed, "W": W, "F": F, "sistem": sysname, "k_yildiz": k, "α_w": a_w,
                       "normal_haftalik_ort": R.per_week(float(esc.mean()), W, F),
                       "normal_haftalik_p95_host": R.per_week(float(host_rate.quantile(0.95)), W, F),
                       "normal_haftalik_en_kotu_host": R.per_week(float(host_rate.max()), W, F),
                       "saf_pencere_sayisi": len(pure),
                       "saf_pencere_tespit": float(np.mean(R.counts(flag, pure) >= k)) if len(pure) else np.nan,
                       "cikmaz_orani": dead}
                for rho, mw in mixed.items():
                    row[f"karisik_ρ={rho:.2f}"] = float(np.mean(R.counts(flag, mw) >= k))
                out.append(row)
    return out
