"""WITHDRAWN (2026-11-17): thresholds are set on benign_test (test data); kept only for the history of the
analysis and not used in the manuscript (PROTOCOL_PHASE10B.md section 6).

Phase 10 DIAGNOSTIC (not part of the pre-specified protocol; added after the test stage).

The test stage showed that thresholds calibrated on benign_val do not keep every rule within the budget on
benign_test. To separate "better evidence" from "looser realised alarm rate", this script sets each rule's
threshold ON THE TEST HOSTS so that its realised traffic-weighted false-escalation rate equals the budget
(1 per host-week at F = 1000), and reports the detection at that operating point. These thresholds are tuned on
test data, so the numbers are an oracle comparison of the statistics, NOT deployable performance.

It also writes detection / false-escalation trade-off curves for the window rules.
Usage: python -I phase10/tradeoff_phase10.py --seeds 0-9
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_phase10 as RP  # noqa: E402
from run_phase10 import P10, R  # noqa: E402

F = 1000
WIN = ["W_COUNT_AU", "W_COUNT_A", "W_EVID", "W_TPM", "W_MINP", "W_HC", "W_FISHER"]
SEQ = ["E_CUSUM", "BCUSUM", "E_SR_ADAPT"]
N_ATT = 300
FE_GRID = np.array([0.25, 0.5, 1.0, 2.0, 4.0, 8.0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="0-9")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    seeds = RP.parse_list(args.seeds)
    cfg, rows, prep = RP.load_common()
    dev_f, held_f = cfg["dev_families"], cfg["heldout_families"]
    out = HERE / "results" / f"diagnostic_tradeoff{('_' + args.tag) if args.tag else ''}"
    out.mkdir(parents=True, exist_ok=True)
    dev_types, dev_mult = prep["type_dev_val"].astype(str), prep["mult_dev_val"].astype(float)
    res, curves = [], []
    for seed in seeds:
        t0 = time.time()
        p_rows, p_dev, n_cal = RP.seed_pvalues(rows, seed)
        lr = P10.fit_likelihood_ratio(p_dev, dev_types, dev_mult, n_cal)
        lr2 = P10.fit_likelihood_ratio(p_dev, dev_types, dev_mult, n_cal, edges=P10.FLAG_EDGES)
        cal_g = R.host_groups(rows, (rows["split"] == "benign_val").to_numpy())
        ev_g = R.host_groups(rows, (rows["split"] == "benign_test").to_numpy())
        pools = {f: np.where(((rows["split"] == "dev_test") & (rows["type"] == f)).to_numpy())[0] for f in dev_f}
        pools.update({f: np.where(((rows["split"] == "heldout_test") & (rows["type"] == f)).to_numpy())[0] for f in held_f})
        grp = {**{f: "known" for f in dev_f}, **{f: "unseen" for f in held_f}}
        rng = np.random.default_rng(7_000_000 + seed)
        for ref in ["pooled", "host"]:
            all_hosts = sorted(set(cal_g) | set(ev_g))
            if ref == "pooled":
                Pf, N, hidx = p_rows, len(p_rows), {h: 0 for h in all_hosts}
            else:
                Pf, _, N = RP.host_conditional_table(p_rows, cal_g, all_hosts, np.random.default_rng(3_000_000 + seed))
                hidx = {h: i for i, h in enumerate(all_hosts)}
            aux = {"a": RP.ALPHA, "ab": RP.ALPHA + RP.BETA, "e_lr": lambda P: P10.lr_evalue(P, lr, 0.01)}
            for W in RP.WS:
                ew_h = [h for h, ix in ev_g.items() if len(ix) >= W]
                ew_sz = np.array([len(ev_g[h]) for h in ew_h], float)
                ev_w, ev_wh = R.sample_windows({h: ev_g[h] for h in ew_h}, W, RP.N_EVAL_WIN, rng)
                ev_w = ev_w + N * np.asarray([hidx[h] for h in ev_wh])[:, None]
                att, pick = RP.stream_ids(ev_g, ew_h, ew_sz, N_ATT, RP.WARMUP + W, rng, hidx)
                hoff = N * np.asarray([hidx[ew_h[k]] for k in pick])[:, None]
                warm, seg_ben = att[:, :RP.WARMUP] + hoff, att[:, RP.WARMUP:] + hoff
                segs = {}
                for rho in RP.RHOS:
                    na = int(round(rho * W))
                    if na < 1:
                        continue
                    pos = np.argsort(rng.random((N_ATT, W)), axis=1)[:, :na]
                    for fam, pool in pools.items():
                        seg = seg_ben.copy()
                        for i in range(N_ATT):
                            seg[i, pos[i]] = rng.choice(pool, na, replace=False) + hoff[i, 0]
                        segs[(fam, rho)] = seg
                for m in WIN:
                    Tb = P10.window_stat(m, Pf[ev_w], aux)
                    Ta = {k: P10.window_stat(m, Pf[s], aux) for k, s in segs.items()}
                    cand = np.unique(np.r_[Tb, np.inf])
                    fe = np.array([R.per_week(float(np.mean(Tb >= c)), W, F) for c in cand])
                    for target in FE_GRID:
                        ok = np.where(fe <= target)[0]
                        c = cand[ok[0]]
                        for (fam, rho), Tv in Ta.items():
                            row = dict(seed=seed, ref=ref, method=m, W=W, rho=rho, family=fam, group=grp[fam],
                                       target_fe=target, realised_fe=float(fe[ok[0]]), detect=float(np.mean(Tv >= c)))
                            (res if target == 1.0 else curves).append(row)
                # sequential rules: bisection on the threshold for realised weighted mean fe <= 1 on benign_test
                ev_h = [h for h, ix in ev_g.items() if len(ix) >= RP.MIN_HOST_ROWS]
                ev_sz = np.array([len(ev_g[h]) for h in ev_h], float)
                if W == RP.WS[0]:
                    seq_thr = {}
                inc = RP.increments(Pf, lr, lr2, 0.01, W, 0.0, 0.0)
                X_ad = np.vstack([np.log(P10.lr_evalue(Pf, lr, r)) for r in RP.ADAPT_GRID])
                erng = np.random.default_rng(8_000_000 + seed)
                L = int(7 * F)
                bids = {h: erng.choice(ev_g[h], (6, L), replace=True) + N * hidx[h] for h in ev_h}
                for m in SEQ:
                    if m == "E_SR_ADAPT":
                        kind, x, X = 2, None, X_ad
                        RP.PAR[0], RP.PAR[1] = 0.0, 0.0
                    else:
                        kind, x, par, s0 = inc[m]
                        X = None
                        RP.PAR[0], RP.PAR[1] = par, s0
                    if m not in seq_thr:
                        def wfe(h):
                            r = [RP.run(kind, x, X, bids[hh], h)[1].sum() / bids[hh].size * 7 * F for hh in ev_h]
                            return float(np.sum(np.array(r) * ev_sz) / ev_sz.sum())
                        lo, hi = 0.0, 60.0
                        for _ in range(18):
                            mid = 0.5 * (lo + hi)
                            if wfe(mid) <= 1.0:
                                hi = mid
                            else:
                                lo = mid
                        seq_thr[m] = (hi, wfe(hi))
                    h, fe_r = seq_thr[m]
                    s_w = RP.run(kind, x, X, warm, h)[0]
                    for (fam, rho), seg in segs.items():
                        first = RP.run(kind, x, X, seg, h, s_init=s_w)[2]
                        res.append(dict(seed=seed, ref=ref, method=m, W=W, rho=rho, family=fam, group=grp[fam],
                                        target_fe=1.0, realised_fe=fe_r, detect=float(np.mean(first > 0))))
        pd.DataFrame(res).to_csv(out / f"matched_fe1_{seed}.csv", index=False)
        pd.DataFrame(curves).to_csv(out / f"curves_{seed}.csv", index=False)
        res, curves = [], []
        print(f"seed {seed} done in {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
