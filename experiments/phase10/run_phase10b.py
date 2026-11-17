"""Phase 10b: confirmatory test of host-conditional calibration (PROTOCOL_PHASE10B.md).

Frozen rules (EXIST, HCOUNT, P10, CUSUM-P/H, eCUSUM-H, EWMA-P/H) are calibrated on a calibration split only, for
nominal budgets B, and evaluated on disjoint benign hosts/units and on attack streams. No threshold is ever set with
evaluation data. Settings: S1 MAIN, S2 SWAP, S3 DEVICE, S4 DEDUP (see the protocol).
Usage: python -I phase10/run_phase10b.py --setting MAIN --seeds 0 --tag s0
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_phase10 as RP  # noqa: E402  (also puts the trustids package on sys.path)
from run_phase10 import C, R, P10  # noqa: E402

ALPHA, BETA = RP.ALPHA, RP.BETA
RHO0 = 0.01                                   # selected in Phase 10 (validation stage), frozen
BUDGETS = [(0.5, 1000), (1.0, 1000), (2.0, 1000), (1.0, 5000)]
WS = [50, 100, 200]
RHOS = [0.05, 0.10, 0.25]
N_CAL_WIN = N_EVAL_WIN = 5000
N_CAL_STREAMS, CAL_DAYS = 200, 14
EVAL_STREAMS_PER_HOST, EVAL_DAYS = 12, 14
N_ATT, WARMUP, MIN_HOST_ROWS = 300, 1000, 20
SETTINGS = {"MAIN": 1, "SWAP": 2, "DEVICE": 3, "DEDUP": 4}
RULES = {  # code: (reference, kind, base method)
    "EXIST": ("pooled", "window", "W_COUNT_AU"), "HCOUNT": ("host", "window", "W_COUNT_AU"),
    "P10": ("host", "window", "W_EVID"),
    "CUSUM-P": ("pooled", "seq", "BCUSUM"), "CUSUM-H": ("host", "seq", "BCUSUM"),
    "eCUSUM-H": ("host", "seq", "E_CUSUM"),
    "EWMA-P": ("pooled", "seq", "EWMA_FLAG"), "EWMA-H": ("host", "seq", "EWMA_FLAG"),
}
W_DEP = {"EWMA_FLAG"}


# ------------------------------------------------------------------ data per setting
def load_setting(setting, seed, cfg, prep):
    """Returns p (per unit), units DataFrame (host, type, role), LR fit inputs, n_cal."""
    if setting == "DEVICE":
        z = np.load(RP.ART / "scores" / f"device_seed{seed}.npz")
        cal = z["benign_cal"]
        per = {sp: C.pvalues(cal, z[sp], seed=seed, model="ae") for sp in ["benign_test", "dev_test", "heldout_test"]}
    else:
        z = np.load(RP.ART / "scores" / f"seed{seed}.npz")
        cal = z["ae__benign_cal"]
        per = {sp: C.pvalues(cal, z["ae__" + sp], seed=seed, model="ae")
               for sp in ["benign_val", "benign_test", "dev_test", "heldout_test", "dev_val"]}
    if setting == "DEDUP":
        rows = pd.read_csv(HERE / "results" / "host_rows_dedup.csv.gz", keep_default_na=False)
    else:
        rows = pd.read_csv(RP.ART / "resolution" / "host_rows.csv.gz", keep_default_na=False)
        rows["split"] = rows["split"].replace({"": None})
    rows = rows[rows["split"].isin(["benign_val", "benign_test", "dev_test", "heldout_test"])].reset_index(drop=True)
    if setting == "DEVICE":
        rows = rows[rows["split"] != "benign_val"].reset_index(drop=True)
    p = R.row_values(rows, {k: v for k, v in per.items() if k in set(rows["split"])})
    role = np.full(len(rows), "", dtype=object)
    sp = rows["split"].to_numpy()
    rng = np.random.default_rng(7_000_000 + seed)
    if setting in ("MAIN", "DEDUP"):
        role[sp == "benign_val"], role[sp == "benign_test"] = "CAL", "EVAL"
    elif setting == "SWAP":
        role[sp == "benign_test"], role[sp == "benign_val"] = "CAL", "EVAL"
    else:                                              # DEVICE: disjoint halves of benign_test vectors
        n_bt = int(rows.loc[sp == "benign_test", "pos"].max()) + 1
        half = rng.random(n_bt) < 0.5
        m = sp == "benign_test"
        role[m] = np.where(half[rows.loc[m, "pos"].to_numpy()], "CAL", "EVAL")
    role[sp == "heldout_test"] = "ATT"
    if setting == "DEVICE":                            # LR on half A of dev_test vectors; known attacks from half B
        n_dt = int(rows.loc[sp == "dev_test", "pos"].max()) + 1
        dhalf = np.random.default_rng(8_000_000 + seed).random(n_dt) < 0.5
        m = sp == "dev_test"
        role[m] = np.where(dhalf[rows.loc[m, "pos"].to_numpy()], "LRFIT", "ATT")
        pt = per["dev_test"]
        types = np.asarray(prep["type_dev_test"]).astype(str)
        mult = np.asarray(prep["mult_dev_test"]).astype(float)
        fit = (pt[dhalf], types[dhalf], mult[dhalf])
    else:
        role[sp == "dev_test"] = "ATT"
        fit = (per["dev_val"], np.asarray(prep["type_dev_val"]).astype(str), np.asarray(prep["mult_dev_val"]).astype(float))
    units = pd.DataFrame({"host": rows["host"].astype(str).to_numpy(), "type": rows["type"].astype(str).to_numpy(), "role": role})
    return p, units, fit, len(cal)


def calibrate_seq(kind, x, X, ids, F, B):
    n, L = ids.shape
    mx = P10.max_stat_mix(X, ids) if X is not None else P10.max_stat(x, ids, kind, RP.PAR[0], RP.PAR[1])
    lo = RP.PAR[1] if (X is None and kind == 3) else 0.0
    hi = float(np.max(mx)) + 1e-9

    def wk(h):
        return (RP.run(kind, x, X, ids, h)[1].sum() + 1.0) / (n * L) * 7.0 * F

    if wk(hi) > B:
        return hi, wk(hi)
    if wk(lo) <= B:
        return lo, wk(lo)
    a, b = lo, hi
    for _ in range(24):
        m = 0.5 * (a + b)
        if wk(m) <= B:
            b = m
        else:
            a = m
    return b, wk(b)


def run_setting(setting, seed, cfg, prep):
    p, units, (pfit, tfit, mfit), n_cal = load_setting(setting, seed, cfg, prep)
    lr = P10.fit_likelihood_ratio(pfit, tfit, mfit, n_cal)
    lr2 = P10.fit_likelihood_ratio(pfit, tfit, mfit, n_cal, edges=P10.FLAG_EDGES)
    held = set(cfg["heldout_families"])
    groups = lambda role: {h: g.index.to_numpy() for h, g in units[units["role"] == role].groupby("host")}
    cal_g, ev_g = groups("CAL"), groups("EVAL")
    att = units[units["role"] == "ATT"]
    pools = {f: g.index.to_numpy() for f, g in att.groupby("type")}
    fam_group = {f: ("unseen" if f in held else "known") for f in pools}
    rng = np.random.default_rng(5_000_000 + 100_000 * SETTINGS[setting] + seed)
    all_hosts = sorted(set(cal_g) | set(ev_g))
    tabs = {"pooled": (p, len(p), {h: 0 for h in all_hosts})}
    Ph, info, N = RP.host_conditional_table(p, cal_g, all_hosts, np.random.default_rng(6_000_000 + seed))
    tabs["host"] = (Ph, N, {h: i for i, h in enumerate(all_hosts)})
    det, cost = [], []
    base = {"setting": setting, "seed": seed}
    cal_h = [h for h, ix in cal_g.items() if len(ix) >= MIN_HOST_ROWS]
    ev_h = [h for h, ix in ev_g.items() if len(ix) >= MIN_HOST_ROWS]
    cal_sz = np.array([len(cal_g[h]) for h in cal_h], float)
    ev_sz = np.array([len(ev_g[h]) for h in ev_h], float)
    # sequential calibration streams (shared by all budgets of a traffic level; offsets applied per reference)
    seq_cal = {}
    for F in sorted({F for _, F in BUDGETS}):
        ids, pick = RP.stream_ids(cal_g, cal_h, cal_sz, N_CAL_STREAMS, int(CAL_DAYS * F), rng, None)
        seq_cal[F] = (ids, [cal_h[k] for k in pick])
    erng_seed = 9_000_000 + 1000 * seed
    seq_cache = {}
    for W in WS:
        cw_h = [h for h, ix in cal_g.items() if len(ix) >= W]
        ew_h = [h for h, ix in ev_g.items() if len(ix) >= W]
        if not cw_h or not ew_h:
            cost.append(dict(base, W=W, note=f"no calibration or evaluation host with >= {W} units"))
            continue
        ew_sz = np.array([len(ev_g[h]) for h in ew_h], float)
        cal_w, cal_wh = R.sample_windows({h: cal_g[h] for h in cw_h}, W, N_CAL_WIN, rng)
        ev_w, ev_wh = R.sample_windows({h: ev_g[h] for h in ew_h}, W, N_EVAL_WIN, rng)
        a_ids, pick = RP.stream_ids(ev_g, ew_h, ew_sz, N_ATT, WARMUP + W, rng, None)
        a_hosts = [ew_h[k] for k in pick]
        segs = {}
        for rho in RHOS:
            na = int(round(rho * W))
            pos = np.argsort(rng.random((N_ATT, W)), axis=1)[:, :na]
            for fam, pool in pools.items():
                if len(pool) < na:
                    continue
                seg = a_ids[:, WARMUP:].copy()
                for i in range(N_ATT):
                    seg[i, pos[i]] = rng.choice(pool, na, replace=False)
                segs[(fam, rho)] = (na, seg)
        for ref, (Pf, Nf, hidx) in tabs.items():
            off = lambda ids, hs: ids + Nf * np.asarray([hidx[h] for h in hs])[:, None]
            cw, ew = off(cal_w, cal_wh), off(ev_w, ev_wh)
            hoff = Nf * np.asarray([hidx[h] for h in a_hosts])[:, None]
            warm = a_ids[:, :WARMUP] + hoff
            segs_r = {k: (na, s + hoff) for k, (na, s) in segs.items()}
            aux = {"a": ALPHA, "ab": ALPHA + BETA, "e_lr": lambda P: P10.lr_evalue(P, lr, RHO0)}
            val_flat = np.concatenate([np.asarray(cal_g[h]) + Nf * hidx[h] for h in cal_g])
            mu_flag = float(np.mean(Pf[val_flat] <= ALPHA + BETA))
            inc = RP.increments(Pf, lr, lr2, RHO0, W, mu_flag, 0.0)
            for code, (rref, kind_s, meth) in RULES.items():
                if rref != ref:
                    continue
                for B, F in BUDGETS:
                    if kind_s == "window":
                        a_w = R.window_budget(B, W, F)
                        thr = P10.conformal_threshold(P10.window_stat(meth, Pf[cw], aux), a_w)
                        Te = P10.window_stat(meth, Pf[ew], aux) >= thr
                        hr = pd.Series(Te).groupby(ev_wh).mean().apply(lambda r: R.per_week(r, W, F))
                        fe_w = R.per_week(float(Te.mean()), W, F)
                        cost.append(dict(base, rule=code, B=B, F=F, W=W, kind="window", threshold=thr,
                                         fe_mean=fe_w, fe_mean_unweighted=float(hr.mean()),
                                         fe_worst=float(hr.max()), worst_host=str(hr.idxmax()),
                                         hosts_over=int((hr > B).sum()), n_hosts=len(ew_h)))
                        for (fam, rho), (na, seg) in segs_r.items():
                            d = P10.window_stat(meth, Pf[seg], aux) >= thr
                            det.append(dict(base, rule=code, B=B, F=F, W=W, rho=rho, family=fam, group=fam_group[fam],
                                            detect=float(d.mean()), delay=float(W)))
                        continue
                    kind, x, par, s0 = inc[meth]
                    RP.PAR[0], RP.PAR[1] = par, s0
                    key = (code, B, F, W if meth in W_DEP else None)
                    if key not in seq_cache:
                        ids, hs = seq_cal[F]
                        h, wk = calibrate_seq(kind, x, None, off(ids, hs), F, B)
                        er = np.random.default_rng(erng_seed + F)
                        L = int(EVAL_DAYS * F)
                        rates = {}
                        for hst in ev_h:
                            e_ids = er.choice(ev_g[hst], (EVAL_STREAMS_PER_HOST, L), replace=True) + Nf * hidx[hst]
                            rates[hst] = float(RP.run(kind, x, None, e_ids, h)[1].sum()) / e_ids.size * 7.0 * F
                        seq_cache[key] = (h, wk, pd.Series(rates))
                    h, wk, hr = seq_cache[key]
                    if meth in W_DEP or W == WS[0]:
                        cost.append(dict(base, rule=code, B=B, F=F, W=W if meth in W_DEP else "all", kind="sequential",
                                         threshold=h, cal_estimate=wk,
                                         fe_mean=float(np.sum(hr[ev_h].to_numpy() * ev_sz) / ev_sz.sum()),
                                         fe_mean_unweighted=float(hr.mean()), fe_worst=float(hr.max()),
                                         worst_host=str(hr.idxmax()), hosts_over=int((hr > B).sum()), n_hosts=len(ev_h)))
                    s_w = RP.run(kind, x, None, warm, h)[0]
                    for (fam, rho), (na, seg) in segs_r.items():
                        first = RP.run(kind, x, None, seg, h, s_init=s_w)[2]
                        hit = first > 0
                        det.append(dict(base, rule=code, B=B, F=F, W=W, rho=rho, family=fam, group=fam_group[fam],
                                        detect=float(hit.mean()),
                                        delay=float(first[hit].mean()) if hit.any() else np.nan))
    ref_info = pd.DataFrame(info).assign(**base)
    return det, cost, ref_info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--setting", choices=list(SETTINGS), required=True)
    ap.add_argument("--seeds", default="0-9")
    ap.add_argument("--tag", default="")
    ap.add_argument("--out", default=str(HERE / "results_10b"))
    args = ap.parse_args()
    seeds = RP.parse_list(args.seeds)
    cfg, _, _ = RP.load_common()
    f = RP.ART / "prepared" / "prepared.npz"
    if not f.exists():                                 # repository copy: labels and multiplicities only
        f = RP.ART / "prepared" / "dev_val_meta.npz"
    prep = np.load(f, allow_pickle=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = Path(args.out) / f"{stamp}_phase10b_{args.setting}{('_' + args.tag) if args.tag else ''}"
    out.mkdir(parents=True, exist_ok=True)
    meta = {"setting": args.setting, "seeds": seeds, "rules": RULES, "budgets": BUDGETS, "Ws": WS, "rhos": RHOS,
            "rho0": RHO0, "N_ATT": N_ATT, "WARMUP": WARMUP, "N_CAL_WIN": N_CAL_WIN, "N_CAL_STREAMS": N_CAL_STREAMS,
            "CAL_DAYS": CAL_DAYS, "EVAL_STREAMS_PER_HOST": EVAL_STREAMS_PER_HOST, "EVAL_DAYS": EVAL_DAYS,
            "N_MIN_REF": RP.N_MIN_REF, "python": sys.version, "numpy": np.__version__, "pandas": pd.__version__,
            "platform": platform.platform(), "started": stamp, "command": " ".join(sys.argv)}
    (out / "config_phase10b.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    D, Cc, I = [], [], []
    for seed in seeds:
        t0 = time.time()
        d, c, i = run_setting(args.setting, seed, cfg, prep)
        D += d; Cc += c; I.append(i)
        pd.DataFrame(D).to_csv(out / "detection.csv", index=False)
        pd.DataFrame(Cc).to_csv(out / "benign_cost.csv", index=False)
        pd.concat(I).to_csv(out / "host_reference_info.csv", index=False)
        print(f"{args.setting} seed {seed} done in {time.time() - t0:.1f}s", flush=True)
    meta["finished"] = datetime.now().strftime("%Y%m%d-%H%M%S")
    (out / "config_phase10b.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("output:", out)


if __name__ == "__main__":
    main()
