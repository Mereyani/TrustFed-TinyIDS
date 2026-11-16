"""Feasibility test: does per-host accumulation of UNCERTAIN evidence turn deferred attacks into detections?

Written BEFORE looking at any window-level result (2026-11-05). Uses only cached v5.2 AE scores; no retraining.

Unit of decision
    A *window* = W flows (raw rows) from the same source host (`src_ip`) and the same traffic class, drawn at
    random without replacement (version B has no timestamp, so there is no real time order; disclosed).
    `src_ip` is used only as a grouping key, never as a model feature.
    Every raw row inherits the conformal p-value of its de-duplicated model vector (deployment scores every flow,
    so repeated identical flows are kept: this is the realistic, harder case for benign hosts).

Rows used
    benign_val vectors -> calibration windows (their p-values against benign_cal are out-of-sample),
    benign_test        -> benign evaluation windows,
    dev_test           -> known-family windows,  heldout_test -> unseen-family windows.

Pre-specified rules (alpha = 0.01, beta = 0.04, host budget a_h = 0.01, W in {5, 10, 20, 50})
    K = number of flows in the window with p <= alpha + beta  (ANOMALY or UNCERTAIN): one counter per host.
    R-bin : escalate if K >= k_bin, the smallest k with P[Binom(W, alpha+beta) >= k] <= a_h (assumes independence).
    R-cal : escalate if K >= k_cal, the smallest k with (1 + #{benign_val windows with K >= k}) / (n_val + 1) <= a_h
            (window-level split-conformal; no independence assumption, but needs exchangeable benign windows).
    Baseline: flow-level ANOMALY rate (p <= alpha) of the same rows.

Outputs: <run>/experiments/host_accumulation_{windows,summary}.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from trustids import conformal as C, data as D, evaluation as E  # noqa: E402
from trustids.config import Config  # noqa: E402

RUN = ROOT / "local_run_v52"
W_GRID = [5, 10, 20, 50]
A_HOST = 0.01
SPLITS_USED = ["benign_val", "benign_test", "dev_test", "heldout_test"]


def map_rows(cfg: Config):
    """Map every raw row to (split, position) of its model vector, using the final preprocessor."""
    df = D.load_raw(ROOT / "data" / "train_test_network.csv", cfg)
    P = D.load_prepared(cfg.artifacts / "prepared")
    pre = P["preprocessor"]
    h_all = D._row_hashes(pre.transform(df))
    look = {}
    for sp in SPLITS_USED:
        hs = D._row_hashes(P["X"][sp])
        for i, (h, t) in enumerate(zip(hs, P["types"][sp])):
            look.setdefault((h, t), (sp, i))
    keys = list(zip(h_all, df["type"].to_numpy()))
    hit = [look.get(k) for k in keys]
    rows = pd.DataFrame({"src_ip": df["src_ip"].astype(str).to_numpy(), "type": df["type"].to_numpy(),
                         "split": [x[0] if x else None for x in hit],
                         "pos": [x[1] if x else -1 for x in hit]})
    return rows, P


def make_windows(rows: pd.DataFrame, W: int, rng) -> list:
    """Non-overlapping random windows per (split, src_ip, type); remainder dropped."""
    out = []
    for (sp, ip, t), g in rows.groupby(["split", "src_ip", "type"]):
        idx = rng.permutation(g.index.to_numpy())
        for j in range(len(idx) // W):
            out.append((sp, ip, t, idx[j * W:(j + 1) * W]))
    return out


def k_binomial(W, q, a):
    for k in range(W + 1):
        if stats.binom.sf(k - 1, W, q) <= a:
            return k
    return W + 1


def k_calibrated(K_val, a):
    n = len(K_val)
    for k in range(int(K_val.max()) + 2):
        if (1 + np.sum(K_val >= k)) / (n + 1) <= a:
            return k
    return int(K_val.max()) + 1


def main():
    cfg = Config.load(RUN / "configs" / "default.json")
    cfg.project_dir = str(RUN)
    rows, P = map_rows(cfg)
    matched = rows["split"].notna()
    print("raw rows matched to a used split:", int(matched.sum()), "of", len(rows))
    rows = rows[matched].reset_index(drop=True)
    print(rows.groupby(["split"]).size().to_dict())
    q = cfg.alpha + cfg.beta
    recs, summ = [], []
    for seed in cfg.train_seeds:
        S = E.load_scores(cfg, seed)
        cal = S[("ae", "benign_cal")]
        p_vec = {sp: C.pvalues(cal, S[("ae", sp)], seed=seed, model="ae") for sp in SPLITS_USED}
        p_row = np.empty(len(rows))
        for sp in SPLITS_USED:
            m = (rows["split"] == sp).to_numpy()
            p_row[m] = p_vec[sp][rows.loc[m, "pos"].to_numpy()]
        rows["p"] = p_row
        for W in W_GRID:
            rng = np.random.default_rng(10_000 * seed + W)
            win = make_windows(rows, W, rng)
            K = np.array([int(np.sum(p_row[ix] <= q)) for _, _, _, ix in win])
            anom = np.array([float(np.mean(p_row[ix] <= cfg.alpha)) for _, _, _, ix in win])
            meta = pd.DataFrame([(sp, ip, t) for sp, ip, t, _ in win], columns=["split", "src_ip", "type"])
            meta["K"], meta["flow_anomaly_rate"] = K, anom
            kb = k_binomial(W, q, A_HOST)
            kc = k_calibrated(K[meta["split"].to_numpy() == "benign_val"], A_HOST)
            meta["esc_bin"], meta["esc_cal"] = K >= kb, K >= kc
            meta["seed"], meta["W"], meta["k_bin"], meta["k_cal"] = seed, W, kb, kc
            recs.append(meta)
            ev = meta[meta["split"] != "benign_val"]
            ben = ev[ev["type"] == cfg.normal_label]
            row = {"seed": seed, "W": W, "k_bin": kb, "k_cal": kc,
                   "n_val_windows": int((meta["split"] == "benign_val").sum()), "n_benign_windows": len(ben),
                   "benign_esc_bin": ben["esc_bin"].mean(), "benign_esc_cal": ben["esc_cal"].mean(),
                   "benign_esc_cal_host_mean": ben.groupby("src_ip")["esc_cal"].mean().mean(),
                   "benign_esc_cal_host_max": ben.groupby("src_ip")["esc_cal"].mean().max()}
            for grp, fams in [("known", cfg.dev_families), ("held-out", cfg.heldout_families)]:
                fr = []
                for f in fams:
                    g = ev[ev["type"] == f]
                    if len(g) == 0:
                        continue
                    row[f"{f}_windows"] = len(g)
                    row[f"{f}_flow_anomaly"] = g["flow_anomaly_rate"].mean()
                    row[f"{f}_esc_bin"] = g["esc_bin"].mean()
                    row[f"{f}_esc_cal"] = g["esc_cal"].mean()
                    fr.append(f)
                row[f"{grp}_macro_flow_anomaly"] = np.mean([row[f"{f}_flow_anomaly"] for f in fr])
                row[f"{grp}_macro_esc_bin"] = np.mean([row[f"{f}_esc_bin"] for f in fr])
                row[f"{grp}_macro_esc_cal"] = np.mean([row[f"{f}_esc_cal"] for f in fr])
            summ.append(row)
        print("seed", seed, "done")
    out = RUN / "experiments"
    out.mkdir(exist_ok=True)
    pd.concat(recs).to_csv(out / "host_accumulation_windows.csv", index=False)
    SM = pd.DataFrame(summ)
    SM.to_csv(out / "host_accumulation_summary.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["k_bin", "k_cal", "n_val_windows", "n_benign_windows", "benign_esc_bin", "benign_esc_cal",
            "benign_esc_cal_host_max", "held-out_macro_flow_anomaly", "held-out_macro_esc_bin",
            "held-out_macro_esc_cal", "known_macro_flow_anomaly", "known_macro_esc_cal"]
    print(SM.groupby("W")[cols].mean().round(4).T.to_string())
    fam = [c for c in SM.columns if any(c.startswith(f + "_") for f in cfg.heldout_families)]
    print(SM.groupby("W")[fam].mean().round(4).T.to_string())


if __name__ == "__main__":
    main()
