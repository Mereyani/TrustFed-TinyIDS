"""Item 6 of the professor's feedback: the host-level trust signal under SPARSE (low-and-slow) attacks.

The host counter (proposal v6 §7a, Rung 2) counts the flows of a host with p <= alpha + beta in a window of
W flows and escalates when the count reaches k*. An attacker who sends only a few malicious flows among many
benign ones may stay below k*. This module measures that, it does not change the mechanism:

* attack share rho per window from 1% to 100%; a window holds round(rho * W) attack flows (reported as such;
  combinations with zero attack flows are skipped, not counted as misses);
* windows W from 20 to 500 flows, where enough benign flows per host exist for calibration;
* the same operational budget as before (<= 1 false escalation per device per week) and the same calibration
  of k* on benign_val windows.

Version B of TON_IoT has no timestamps: windows are random draws, i.e. a SIMULATED stream. The daily
detection probability assumes independent windows and is therefore an approximation, labelled as such.
This analysis was not pre-registered; it is exploratory.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import conformal as C
from . import resolution as R


def evaluate_seed(ROWS: pd.DataFrame, S: dict, cfg, seed: int, rng) -> list:
    """ROWS: raw flows mapped to model vectors (resolution.map_rows), restricted to the four evaluation splits.
    S: split -> AE score (benign_cal, benign_val, benign_test, dev_test, heldout_test)."""
    sp_list = ["benign_val", "benign_test", "dev_test", "heldout_test"]
    p = R.row_values(ROWS, {sp: C.pvalues(S["benign_cal"], S[sp], seed=seed, model="ae") for sp in sp_list})
    a, ab = cfg.alpha, cfg.alpha + cfg.beta
    flags = {"ANOMALY+UNCERTAIN": p <= ab, "yalnız ANOMALY": p <= a}
    g_val = R.host_groups(ROWS, (ROWS["split"] == "benign_val").to_numpy())
    g_ben = R.host_groups(ROWS, (ROWS["split"] == "benign_test").to_numpy())
    ben_all = np.concatenate(list(g_ben.values()))
    fams = [f for f in list(cfg.dev_families) + list(cfg.heldout_families) if f in set(ROWS["type"])]
    att = {}
    for fam in fams:
        sp = "heldout_test" if fam in cfg.heldout_families else "dev_test"
        att[fam] = np.where(((ROWS["split"] == sp) & (ROWS["type"] == fam)).to_numpy())[0]
    out = []
    for W in cfg.sparse_windows:
        cal_w, _ = R.sample_windows(g_val, W, cfg.resolution_cal_windows, rng)
        ev_w, ev_h = R.sample_windows(g_ben, W, cfg.resolution_eval_windows, rng)
        if len(cal_w) == 0 or len(ev_w) == 0 or len(ben_all) < W:
            out.append({"tohum": seed, "W": W, "durum": "W akışa ulaşan normal host yok (atlandı)"})
            continue
        mixed = {}
        for fam in fams:
            for rho in cfg.sparse_rho:
                na = int(round(rho * W))
                if na >= 1 and len(att[fam]) >= na:
                    mixed[(fam, rho)] = (na, R.mixed_windows(att[fam], ben_all, W, rho, cfg.sparse_mixed_windows, rng))
        for F in cfg.resolution_flows_per_day:
            a_w = R.window_budget(cfg.resolution_budget_per_week, W, F)
            for cname, flag in flags.items():
                k = R.k_threshold(R.counts(flag, cal_w), a_w)
                esc = R.counts(flag, ev_w) >= k
                f_rate = float(esc.mean())
                host_rate = pd.Series(esc).groupby(ev_h).mean()
                base = {"tohum": seed, "W": W, "F": F, "sayaç": cname, "k_yildiz": int(k), "α_w": a_w, "durum": "tamam",
                        "normal_yanlis_yukseltme_pencere": f_rate,
                        "normal_haftalik_ort": R.per_week(f_rate, W, F),
                        "normal_haftalik_en_kotu_host": R.per_week(float(host_rate.max()), W, F)}
                for (fam, rho), (na, mw) in mixed.items():
                    d = float(np.mean(R.counts(flag, mw) >= k))
                    out.append(dict(base, aile=fam, grup="görülmemiş" if fam in cfg.heldout_families else "bilinen",
                                    ρ=rho, saldiri_akisi_pencerede=na, gercek_ρ=na / W,
                                    akis_ANOMALY=float(np.mean(p[att[fam]] <= a)),
                                    akis_isaretli=float(np.mean(p[att[fam]] <= ab)),
                                    pencere_tespit=d,
                                    gunluk_tespit_bagimsiz_pencere=float(1 - (1 - d) ** (F / W))))
    return out
