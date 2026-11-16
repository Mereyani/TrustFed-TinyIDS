"""Phase 10 experiment runner: host-level evidence accumulation under sparse attacks (SIMULATION).

Stages
  validation : model selection using ONLY benign_val streams and KNOWN-family attacks from dev_val (half B;
               the likelihood ratio is fitted on half A). No test split is read.
  test       : frozen configuration; thresholds calibrated on benign_val; false escalations measured on
               benign_test hosts; detection on dev_test (known) and heldout_test (unseen) attack flows.

Two p-value references (factor "ref"):
  pooled : the existing conformal p-value against benign_cal (unchanged from phases 3-9);
  host   : p' = max(p_pooled, p_host), where p_host is a conformal p-value of the flow against the host's OWN
           benign reference flows from benign_val (Mondrian-by-host). The maximum of two p-values is
           super-uniform if EITHER is (Vovk & Wang 2020), so p' is valid if the host's benign traffic is
           exchangeable with the pooled calibration set OR with its own reference. benign_val rows of each host
           are split in two folds; a val row is referenced against the other fold (cross-fitting), every other
           row against fold 0. Hosts with fewer than N_MIN_REF reference rows fall back to the pooled p-value.

Inputs are the saved Colab outputs of phases 2-9 (AE scores per seed, host map); nothing is retrained.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import os

ROOT = Path(__file__).resolve().parents[1]                    # project layout: Final_Asama/
if (ROOT / "colab_sonuclari").exists():                        # original working layout
    CODE = ROOT / "TrustFed-TinyIDS-Final"
    ART = ROOT / "colab_sonuclari" / "artifacts"
    F5_CFG = ROOT / "colab_sonuclari" / "20261111-064904_final_F5_seyrek_saldiri" / "config_used.json"
else:                                                          # GitHub repository layout: experiments/phase10/
    ROOT = Path(__file__).resolve().parents[2]
    CODE = ROOT
    ART = ROOT / "results" / "artifacts"
    F5_CFG = ROOT / "results" / "colab_runs" / "20261111-064904_final_F5_seyrek_saldiri" / "config_used.json"
ART = Path(os.environ.get("TRUSTIDS_ARTIFACTS", ART))
sys.path.insert(0, str(CODE))
from trustids import conformal as C, resolution as R, phase10 as P10   # noqa: E402

ALPHA, BETA = 0.01, 0.04
BUDGET = 1.0                                   # false escalations per host per week (unchanged from F5)
WS = [20, 50, 100, 200]
RHOS = [0.01, 0.05, 0.10, 0.25, 0.50]
RHO0_GRID = [0.01, 0.02, 0.05, 0.10, 0.25]
ADAPT_GRID = [0.01, 0.02, 0.05, 0.10, 0.25, 0.50]
N_CAL_WIN, N_EVAL_WIN = 5000, 5000            # window rules (as in F5)
N_CAL_STREAMS, CAL_DAYS = 200, 14              # sequential calibration: 200 benign_val streams x 14 days
EVAL_STREAMS_PER_HOST, EVAL_DAYS = 12, 14      # sequential false escalations per benign_test host
N_ATT = 300                                    # attack streams per (family, rho, W) (F5: 300 windows)
WARMUP = 1000                                  # benign flows of the same host before the attack starts
MIN_HOST_ROWS = 20                             # hosts used for sequential calibration / evaluation
N_MIN_REF = 20                                 # minimum reference rows for a host-conditional p-value

WINDOW_METHODS = ["W_COUNT_AU", "W_COUNT_A", "W_FISHER", "W_TPM", "W_MINP", "W_HC", "W_EVID"]
SEQ_METHODS = ["BCUSUM", "EWMA_FLAG", "EWMA_NLP", "E_CUSUM", "E_SR", "E_CUSUM_MIX", "E_CUSUM_LEAKY",
               "E_SR_ADAPT", "E_CUSUM_TH", "E_SR_TH", "E_SR_ADAPT_TH"]
W_DEPENDENT = {"EWMA_FLAG", "EWMA_NLP", "E_CUSUM_LEAKY"}
THEORY = {"E_CUSUM_TH": "E_CUSUM", "E_SR_TH": "E_SR", "E_SR_ADAPT_TH": "E_SR_ADAPT"}


def parse_list(s, typ=int):
    if s is None:
        return None
    if "-" in s and typ is int:
        a, b = s.split("-")
        return list(range(int(a), int(b) + 1))
    return [typ(x) for x in s.split(",")]


def load_common():
    cfg = json.loads(F5_CFG.read_text(encoding="utf-8"))
    rows = pd.read_csv(ART / "resolution" / "host_rows.csv.gz", keep_default_na=False)
    rows["split"] = rows["split"].replace({"": None})
    rows = rows[rows["split"].isin(["benign_val", "benign_test", "dev_test", "heldout_test"])].reset_index(drop=True)
    f = ART / "prepared" / "prepared.npz"
    if not f.exists():                         # repository copy: only the dev_val labels/multiplicities are kept
        f = ART / "prepared" / "dev_val_meta.npz"
    prep = np.load(f, allow_pickle=True)
    return cfg, rows, prep


def seed_pvalues(rows, seed):
    z = np.load(ART / "scores" / f"seed{seed}.npz")
    cal = z["ae__benign_cal"]
    per = {sp: C.pvalues(cal, z["ae__" + sp], seed=seed, model="ae")
           for sp in ["benign_val", "benign_test", "dev_test", "heldout_test", "dev_val"]}
    p_rows = R.row_values(rows, {k: v for k, v in per.items() if k != "dev_val"})
    return p_rows, per["dev_val"], len(cal)


# ------------------------------------------------------------------ p-value tables per reference
def host_conditional_table(p_all, val_groups, hosts, rng):
    """Returns P (H x N): row h holds the p-values seen by a detector on host hosts[h], and info per host."""
    N = len(p_all)
    P = np.tile(p_all, (len(hosts), 1))
    info = []

    def ph(p, ref):
        r = np.sort(p_all[ref])
        return (1.0 + np.searchsorted(r, p, side="right")) / (len(r) + 1.0)

    folds = {}
    for h in hosts:
        ix = np.asarray(val_groups.get(h, np.array([], dtype=int)), dtype=int)
        fold = rng.random(len(ix)) < 0.5
        folds[h] = (ix[~fold], ix[fold])                       # fold 0 = default reference
    own = {h for h in hosts if min(len(folds[h][0]), len(folds[h][1])) >= N_MIN_REF}
    # Mondrian fallback category: every host without enough own reference shares one "low-traffic" reference
    small = [h for h in hosts if h not in own]
    s0 = np.concatenate([folds[h][0] for h in small]) if small else np.array([], dtype=int)
    s1 = np.concatenate([folds[h][1] for h in small]) if small else np.array([], dtype=int)
    for h_i, h in enumerate(hosts):
        ref0, ref1 = folds[h] if h in own else (s0, s1)
        if min(len(ref0), len(ref1)) < N_MIN_REF:
            info.append({"host": h, "n_ref": int(len(ref0)), "reference": "pooled_only"})
            continue
        P[h_i] = np.maximum(p_all, ph(p_all, ref0))
        P[h_i, ref0] = np.maximum(p_all[ref0], ph(p_all[ref0], ref1))   # cross-fitted for the reference rows
        if h not in own:                                                 # own val rows of a small host in fold 1
            P[h_i, folds[h][1]] = np.maximum(p_all[folds[h][1]], ph(p_all[folds[h][1]], s0))
        info.append({"host": h, "n_ref": int(len(ref0)), "reference": "own" if h in own else "low_traffic_group"})
    return P.reshape(-1), info, N


def increments(Pf, lr, lr2, rho0, W, mu_flag, mu_nlp):
    lam = 2.0 / (W + 1)
    return {
        "BCUSUM":        (0, np.log(P10.lr_evalue(Pf, lr2, rho0)), 0.0, 0.0),
        "EWMA_FLAG":     (3, (Pf <= ALPHA + BETA).astype(float), lam, mu_flag),
        "EWMA_NLP":      (3, -np.log(Pf), lam, mu_nlp),
        "E_CUSUM":       (0, np.log(P10.lr_evalue(Pf, lr, rho0)), 0.0, 0.0),
        "E_SR":          (2, np.log(P10.lr_evalue(Pf, lr, rho0)), 0.0, 0.0),
        "E_CUSUM_MIX":   (0, np.log(1 - rho0 + rho0 * P10.mixture_calibrator(Pf)), 0.0, 0.0),
        "E_CUSUM_LEAKY": (1, np.log(P10.lr_evalue(Pf, lr, rho0)), 1.0 - lam, 0.0),
    }


def run(kind, x, X, ids, h, s_init=None):
    n = ids.shape[0]
    if X is None:
        use = s_init is not None
        return P10.run_streams(x, ids, kind, 0.0 if kind not in (1, 3) else PAR[0], PAR[1], h,
                               s_init if use else np.zeros(n), use)
    use = s_init is not None
    return P10.run_streams_mix(X, ids, h, s_init if use else np.zeros((n, X.shape[0])), use)


PAR = [0.0, 0.0]          # (par, s0) of the method currently being run (set by the caller)


def calibrate_seq(kind, x, X, ids, F):
    """Smallest threshold whose alarm count (with reset) on benign_val streams gives
    (alarms + 1) / flows * 7F <= BUDGET. Bisection on the threshold."""
    n, L = ids.shape
    mx = P10.max_stat_mix(X, ids) if X is not None else P10.max_stat(x, ids, kind, PAR[0], PAR[1])
    lo = PAR[1] if (X is None and kind == 3) else 0.0
    hi = float(np.max(mx)) + 1e-9

    def wk(h):
        _, n_al, _ = run(kind, x, X, ids, h)
        return (n_al.sum() + 1.0) / (n * L) * 7.0 * F

    if wk(hi) > BUDGET:
        return hi, wk(hi)
    if wk(lo) <= BUDGET:
        return lo, wk(lo)
    a, b = lo, hi
    for _ in range(24):
        m = 0.5 * (a + b)
        if wk(m) <= BUDGET:
            b = m
        else:
            a = m
    return b, wk(b)


def stream_ids(groups, hosts, sizes, n, L, rng, hidx):
    """(n, L) row ids drawn with replacement within a host chosen proportional to its rows; returns the ids
    already offset into the flattened (host x row) table, and the host per stream."""
    pick = rng.choice(len(hosts), size=n, p=sizes / sizes.sum())
    ids = np.empty((n, L), dtype=np.int64)
    for i, k in enumerate(pick):
        ids[i] = rng.choice(groups[hosts[k]], L, replace=True)
    return ids, pick


def evaluate(p_all, ref, lr, lr2, rho0, cal_g, ev_g, pools, fam_group, seed, Fs, stage, wts, methods,
             val_rows_all):
    rng = np.random.default_rng(2_000_000 + seed)                  # common random numbers across ref and rho0
    all_hosts = sorted(set(cal_g) | set(ev_g))
    if ref == "pooled":
        Pf, info, N = p_all, [], len(p_all)
        hidx = {h: 0 for h in all_hosts}
    else:
        Pf, info, N = host_conditional_table(p_all, cal_g, all_hosts, np.random.default_rng(3_000_000 + seed))
        hidx = {h: i for i, h in enumerate(all_hosts)}
    off = lambda ids, hosts_of_rows: ids + N * np.asarray([hidx[h] for h in hosts_of_rows])[:, None]
    val_flat = np.concatenate([np.asarray(cal_g[h]) + N * hidx[h] for h in cal_g])
    mu_flag = float(np.mean(Pf[val_flat] <= ALPHA + BETA))
    mu_nlp = float(np.mean(-np.log(Pf[val_flat])))
    aux = {"a": ALPHA, "ab": ALPHA + BETA, "e_lr": lambda P: P10.lr_evalue(P, lr, rho0)}
    det_rows, cost_rows = [], []
    base = {"stage": stage, "seed": seed, "ref": ref, "rho0": rho0}
    win_m = [m for m in methods if m in WINDOW_METHODS]
    seq_m = [m for m in methods if m in SEQ_METHODS]
    # sequential host sets (independent of W)
    cal_h = [h for h, ix in cal_g.items() if len(ix) >= MIN_HOST_ROWS]
    ev_h = [h for h, ix in ev_g.items() if len(ix) >= MIN_HOST_ROWS]
    cal_sz = np.array([len(cal_g[h]) for h in cal_h], float)
    ev_sz = np.array([len(ev_g[h]) for h in ev_h], float)
    seq_thr = {}                                                    # (F, method, W or None) -> (h, wk)
    seq_cal_ids = {}
    for F in Fs:
        ids, pick = stream_ids(cal_g, cal_h, cal_sz, N_CAL_STREAMS, int(CAL_DAYS * F), rng, hidx)
        seq_cal_ids[F] = off(ids, [cal_h[k] for k in pick])
    for W in WS:
        cw_h = [h for h, ix in cal_g.items() if len(ix) >= W]
        ew_h = [h for h, ix in ev_g.items() if len(ix) >= W]
        if not cw_h or not ew_h:
            continue
        ew_sz = np.array([len(ev_g[h]) for h in ew_h], float)
        inc = increments(Pf, lr, lr2, rho0, W, mu_flag, mu_nlp)
        X_adapt = np.vstack([np.log(P10.lr_evalue(Pf, lr, r)) for r in ADAPT_GRID]) if (
            "E_SR_ADAPT" in seq_m or "E_SR_ADAPT_TH" in seq_m) else None
        cal_w, cal_wh = R.sample_windows({h: cal_g[h] for h in cw_h}, W, N_CAL_WIN, rng)
        ev_w, ev_wh = R.sample_windows({h: ev_g[h] for h in ew_h}, W, N_EVAL_WIN, rng)
        cal_w, ev_w = off(cal_w, cal_wh), off(ev_w, ev_wh)
        att, pick = stream_ids(ev_g, ew_h, ew_sz, N_ATT, WARMUP + W, rng, hidx)
        att_hosts = [ew_h[k] for k in pick]
        hoff = N * np.asarray([hidx[h] for h in att_hosts])[:, None]
        warm, seg_ben = att[:, :WARMUP] + hoff, att[:, WARMUP:] + hoff
        segs = {}
        for rho in RHOS:
            na = int(round(rho * W))
            if na < 1:
                continue
            pos = np.argsort(rng.random((N_ATT, W)), axis=1)[:, :na]
            for fam, pool in pools.items():
                if len(pool) < na:
                    continue
                seg = seg_ben.copy()
                w = None if wts is None else wts[fam]
                for i in range(N_ATT):
                    seg[i, pos[i]] = rng.choice(pool, na, replace=w is not None, p=w) + hoff[i, 0]
                segs[(fam, rho)] = (na, seg)
        for F in Fs:
            a_w = R.window_budget(BUDGET, W, F)
            for m in win_m:
                thr = P10.conformal_threshold(P10.window_stat(m, Pf[cal_w], aux), a_w)
                Te = P10.window_stat(m, Pf[ev_w], aux) >= thr
                hr = pd.Series(Te).groupby(ev_wh).mean().apply(lambda r: R.per_week(r, W, F))
                cost_rows.append(dict(base, W=W, F=F, method=m, kind="window", threshold=thr,
                                      fe_week_mean=R.per_week(float(Te.mean()), W, F),
                                      fe_week_worst_host=float(hr.max()), worst_host=str(hr.idxmax()),
                                      hosts_over_budget=int((hr > BUDGET).sum()), n_eval_hosts=len(ew_h)))
                for (fam, rho), (na, seg) in segs.items():
                    d = P10.window_stat(m, Pf[seg], aux) >= thr
                    det_rows.append(dict(base, W=W, F=F, method=m, family=fam, group=fam_group[fam], rho=rho,
                                         n_attack_flows=na, detect=float(d.mean()),
                                         delay_mean=float(W) if d.any() else np.nan,
                                         delay_median=float(W) if d.any() else np.nan))
            for m in seq_m:
                bm = THEORY.get(m, m)
                if bm == "E_SR_ADAPT":
                    kind, x, X = 2, None, X_adapt
                    PAR[0], PAR[1] = 0.0, 0.0
                else:
                    kind, x, par, s0 = inc[bm]
                    X = None
                    PAR[0], PAR[1] = par, s0
                key = (F, m, W if bm in W_DEPENDENT else None)
                if key not in seq_thr:
                    if m in THEORY:
                        h = float(np.log(7.0 * F / BUDGET))
                        _, n_al, _ = run(kind, x, X, seq_cal_ids[F], h)
                        wk = (n_al.sum() + 1.0) / seq_cal_ids[F].size * 7.0 * F
                    else:
                        h, wk = calibrate_seq(kind, x, X, seq_cal_ids[F], F)
                    # benign_test false escalations per host
                    erng = np.random.default_rng(90_000 + 1000 * seed + F)
                    L = int(EVAL_DAYS * F)
                    hr = {}
                    for hst in ev_h:
                        ids = erng.choice(ev_g[hst], (EVAL_STREAMS_PER_HOST, L), replace=True) + N * hidx[hst]
                        _, n_al, _ = run(kind, x, X, ids, h)
                        hr[hst] = float(n_al.sum()) / ids.size * 7.0 * F
                    hr = pd.Series(hr)
                    seq_thr[key] = (h, wk, hr)
                h, wk, hr = seq_thr[key]
                if bm in W_DEPENDENT or W == WS[0]:
                    cost_rows.append(dict(base, W=W if bm in W_DEPENDENT else "all", F=F, method=m,
                                          kind="sequential", threshold=h, cal_week_estimate=wk,
                                          fe_week_mean=float(np.sum(hr[ev_h].to_numpy() * ev_sz) / ev_sz.sum()),
                                          fe_week_mean_unweighted=float(hr.mean()),
                                          fe_week_worst_host=float(hr.max()), worst_host=str(hr.idxmax()),
                                          hosts_over_budget=int((hr > BUDGET).sum()), n_eval_hosts=len(ev_h)))
                s_w = run(kind, x, X, warm, h)[0]
                for (fam, rho), (na, seg) in segs.items():
                    _, _, first = run(kind, x, X, seg, h, s_init=s_w)
                    hit = first > 0
                    det_rows.append(dict(base, W=W, F=F, method=m, family=fam, group=fam_group[fam], rho=rho,
                                         n_attack_flows=na, detect=float(hit.mean()),
                                         delay_mean=float(first[hit].mean()) if hit.any() else np.nan,
                                         delay_median=float(np.median(first[hit])) if hit.any() else np.nan))
    return det_rows, cost_rows, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["validation", "test"], required=True)
    ap.add_argument("--seeds", default="0-9")
    ap.add_argument("--rho0", default=None, help="comma list; default: the full grid")
    ap.add_argument("--refs", default="pooled,host")
    ap.add_argument("--methods", default=None, help="comma list; default: all")
    ap.add_argument("--F", default="1000,5000")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "results"))
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    seeds = parse_list(args.seeds)
    Fs = parse_list(args.F)
    rho0s = parse_list(args.rho0, float) or RHO0_GRID
    refs = args.refs.split(",")
    methods = args.methods.split(",") if args.methods else WINDOW_METHODS + SEQ_METHODS
    cfg, rows, prep = load_common()
    dev_f, held_f = cfg["dev_families"], cfg["heldout_families"]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = Path(args.out) / f"{stamp}_phase10_{args.stage}{('_' + args.tag) if args.tag else ''}"
    out.mkdir(parents=True, exist_ok=True)
    meta = {k: v for k, v in globals().items() if k.isupper() and isinstance(v, (int, float, list, str, dict))
            and k not in ("ROOT", "ART", "F5_CFG", "PAR")}
    meta.update({"stage": args.stage, "seeds": seeds, "Fs": Fs, "rho0s": rho0s, "refs": refs, "methods": methods,
                 "bin_edges": list(P10.BIN_EDGES), "python": sys.version, "numpy": np.__version__,
                 "pandas": pd.__version__, "platform": platform.platform(), "started": stamp,
                 "command": " ".join(sys.argv)})
    (out / "config_phase10.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    dev_types = prep["type_dev_val"].astype(str)
    dev_mult = prep["mult_dev_val"].astype(float)
    det_all, cost_all, lr_rows, info_rows = [], [], [], []
    for seed in seeds:
        t0 = time.time()
        p_rows, p_dev, n_cal = seed_pvalues(rows, seed)
        half = np.random.default_rng(1_000_000 + seed).random(len(p_dev)) < 0.5
        fitm = half if args.stage == "validation" else np.ones(len(p_dev), bool)
        lr = P10.fit_likelihood_ratio(p_dev[fitm], dev_types[fitm], dev_mult[fitm], n_cal)
        lr2 = P10.fit_likelihood_ratio(p_dev[fitm], dev_types[fitm], dev_mult[fitm], n_cal, edges=P10.FLAG_EDGES)
        for b in range(len(lr["r"])):
            lr_rows.append({"seed": seed, "bin": b, "upper_edge": lr["edges"][b], "null_mass": lr["f0"][b],
                            "q_known": lr["q"][b], "r": lr["r"][b]})
        cal_g = R.host_groups(rows, (rows["split"] == "benign_val").to_numpy())
        if args.stage == "validation":
            offs = len(p_rows)
            p_all = np.r_[p_rows, p_dev[~half]]
            idxB = np.where(~half)[0]
            pools, wts = {}, {}
            for f in dev_f:
                m = dev_types[idxB] == f
                pools[f] = offs + np.where(m)[0]
                wts[f] = dev_mult[idxB][m] / dev_mult[idxB][m].sum()
            fam_group = {f: "known" for f in dev_f}
            ev_g = cal_g
        else:
            p_all, wts = p_rows, None
            pools = {f: np.where(((rows["split"] == "dev_test") & (rows["type"] == f)).to_numpy())[0] for f in dev_f}
            pools.update({f: np.where(((rows["split"] == "heldout_test") & (rows["type"] == f)).to_numpy())[0]
                          for f in held_f})
            fam_group = {**{f: "known" for f in dev_f}, **{f: "unseen" for f in held_f}}
            ev_g = R.host_groups(rows, (rows["split"] == "benign_test").to_numpy())
        for ref in refs:
            for k, rho0 in enumerate(rho0s):
                ms = methods if k == 0 else [m for m in methods if m not in
                                             ("W_COUNT_AU", "W_COUNT_A", "W_FISHER", "W_TPM", "W_MINP", "W_HC",
                                              "EWMA_FLAG", "EWMA_NLP", "E_SR_ADAPT", "E_SR_ADAPT_TH")]
                d, c, info = evaluate(p_all, ref, lr, lr2, rho0, cal_g, ev_g, pools, fam_group, seed, Fs,
                                      args.stage, wts, ms, None)
                det_all += d
                cost_all += c
                if k == 0:
                    info_rows += [dict(i, seed=seed, ref=ref) for i in info]
        pd.DataFrame(det_all).to_csv(out / "detection_all.csv", index=False)
        pd.DataFrame(cost_all).to_csv(out / "benign_cost_all.csv", index=False)
        pd.DataFrame(lr_rows).to_csv(out / "likelihood_ratio_bins.csv", index=False)
        pd.DataFrame(info_rows).to_csv(out / "host_reference_info.csv", index=False)
        print(f"seed {seed} done in {time.time() - t0:.1f}s", flush=True)
    meta["finished"] = datetime.now().strftime("%Y%m%d-%H%M%S")
    (out / "config_phase10.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("output:", out)


if __name__ == "__main__":
    main()
