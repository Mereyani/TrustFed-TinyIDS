"""Sensitivity (written after seeing the pure-window results): real hosts mix attack and benign flows.
A window of W = 20 flows holds a fraction rho of attack flows (one family) and 1 - rho benign_test flows.
Threshold k_cal is the one calibrated on pure benign_val windows in host_accumulation.py (same seeds)."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.host_accumulation import map_rows, RUN, SPLITS_USED  # noqa: E402
from trustids import conformal as C, evaluation as E  # noqa: E402
from trustids.config import Config  # noqa: E402

cfg = Config.load(RUN / "configs" / "default.json"); cfg.project_dir = str(RUN)
rows, _ = map_rows(cfg)
rows = rows[rows["split"].notna()].reset_index(drop=True)
SM = pd.read_csv(RUN / "experiments" / "host_accumulation_summary.csv")
W, q, out = 20, cfg.alpha + cfg.beta, []
ben_idx = rows.index[(rows["split"] == "benign_test")].to_numpy()
for seed in cfg.train_seeds:
    S = E.load_scores(cfg, seed)
    p = np.empty(len(rows))
    for sp in SPLITS_USED:
        m = (rows["split"] == sp).to_numpy()
        p[m] = C.pvalues(S[("ae", "benign_cal")], S[("ae", sp)], seed=seed, model="ae")[rows.loc[m, "pos"].to_numpy()]
    kc = int(SM[(SM.seed == seed) & (SM.W == W)]["k_cal"].iloc[0])
    rng = np.random.default_rng(seed)
    for fam in cfg.heldout_families + cfg.dev_families:
        sp = "heldout_test" if fam in cfg.heldout_families else "dev_test"
        att = rows.index[(rows["split"] == sp) & (rows["type"] == fam)].to_numpy()
        for rho in [0.1, 0.25, 0.5, 1.0]:
            na = int(round(rho * W)); hits = []
            for _ in range(500):
                ix = np.r_[rng.choice(att, na, replace=False), rng.choice(ben_idx, W - na, replace=False)]
                hits.append(np.sum(p[ix] <= q) >= kc)
            out.append({"seed": seed, "family": fam, "group": "held-out" if fam in cfg.heldout_families else "known",
                        "rho": rho, "k_cal": kc, "esc_rate": float(np.mean(hits))})
    print("seed", seed, "done")
R = pd.DataFrame(out); R.to_csv(RUN / "experiments" / "host_accumulation_mixed.csv", index=False)
pd.set_option("display.width", 200)
print(R.groupby(["group", "family", "rho"])["esc_rate"].mean().unstack().round(3).to_string())
print(R.groupby(["group", "rho", "seed"])["esc_rate"].mean().groupby(["group", "rho"]).agg(["mean", "std"]).round(3).to_string())
