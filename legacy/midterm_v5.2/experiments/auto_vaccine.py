"""Analyst-free "auto-vaccine" (exploratory, seed 0). Rules fixed before running (2026-11-05).

Goal: replace the analyst's label with two automatic checks that need no attack labels.
  Pool      = suspicious flows (AE conformal p <= alpha + beta) that the known-attack head does NOT recognise
              (the NOVEL cell), drawn from benign_test (all) + a campaign of n vectors per held-out family.
  Candidate = each pool point x with radius r_x = 0.5% quantile of its distances to benign_cal (8-dim latent),
              i.e. a ball that by construction holds <= 0.5% of clean reference traffic (CHECK 1: benign safety).
  Promote x if its ball holds >= m pool points coming from >= 2 distinct source hosts (CHECK 2: corroboration;
              a recurring pattern at several hosts, not one odd benign device). Greedy, largest support first,
              skipping points already covered. At most V = 10 vaccines.
  Then every flow inside any promoted ball -> ANOMALY.
Post-hoc variant (after seeing the 0.005 result): QBALL=0.001 gives each ball <= 0.1% of benign_cal, so 10 balls <= 1%.
Evaluation only (labels never used by the rules): held-out recall before/after, benign_test FPR of the union,
vaccine purity, for campaign sizes n in {10, 30, 100}, with and without CHECK 2. 30 repetitions.
"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from trustids import conformal as C, data as D, evaluation as E  # noqa
from trustids.config import Config  # noqa
from experiments.host_accumulation import map_rows  # noqa
from tensorflow import keras  # noqa

RUN = ROOT / "local_run_v52"
cfg = Config.load(RUN / "configs" / "default.json"); cfg.project_dir = str(RUN)
P = D.load_prepared(cfg.artifacts / "prepared"); X, T = P["X"], P["types"]
S = E.load_scores(cfg, 0)
ae = keras.models.load_model(cfg.artifacts / "models" / "ae_seed0.keras")
enc = keras.Model(ae.input, ae.get_layer("latent").output)
Z = {sp: enc.predict(X[sp], batch_size=4096, verbose=0).astype(np.float64) for sp in ["benign_cal", "benign_test", "heldout_test"]}
p = {sp: C.pvalues(S[("ae", "benign_cal")], S[("ae", sp)]) for sp in ["benign_test", "heldout_test"]}
rf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1, class_weight="balanced")
rf.fit(np.r_[X["benign_train"], X["dev_val"]], np.r_[np.zeros(len(X["benign_train"])), np.ones(len(X["dev_val"]))])
thr = np.quantile(rf.predict_proba(X["benign_cal"])[:, 1], 0.99, method="higher")
known = {sp: rf.predict_proba(X[sp])[:, 1] > thr for sp in ["benign_test", "heldout_test"]}
# host sets per vector (all raw rows that map to it)
rows, _ = map_rows(cfg)
hosts = {}
for sp in ["benign_test", "heldout_test"]:
    g = rows[rows["split"] == sp].groupby("pos")["src_ip"].apply(lambda s: frozenset(s))
    hosts[sp] = [g.get(i, frozenset()) for i in range(len(T[sp]))]

def dist(Q, R):
    return np.sqrt(((Q[:, None, :] - R[None, :, :]) ** 2).sum(-1))

novel = {sp: (p[sp] <= 0.05) & ~known[sp] for sp in p}
bpool = np.where(novel["benign_test"])[0]
fams = cfg.heldout_families
rng = np.random.default_rng(0)
out = []
for n in [10, 30, 100]:
    for rep in range(30):
        camp = {f: rng.choice(np.where(novel["heldout_test"] & (T["heldout_test"] == f))[0],
                              min(n, int((novel["heldout_test"] & (T["heldout_test"] == f)).sum())), replace=False) for f in fams}
        Zp = np.r_[Z["benign_test"][bpool], np.concatenate([Z["heldout_test"][camp[f]] for f in fams])]
        lab = np.r_[["normal"] * len(bpool), np.concatenate([[f] * len(camp[f]) for f in fams])]
        Hp = [hosts["benign_test"][i] for i in bpool] + [hosts["heldout_test"][i] for f in fams for i in camp[f]]
        import os; QB = float(os.environ.get("QBALL", "0.005"))
        r = np.quantile(dist(Zp, Z["benign_cal"]), QB, axis=1, method="lower")
        Dpp = dist(Zp, Zp)
        inside = Dpp <= r[:, None]
        support = inside.sum(1)
        nhost = np.array([len(frozenset().union(*[Hp[j] for j in np.where(inside[i])[0]])) for i in range(len(Zp))])
        for corroborate in [False, True]:
            ok = (support >= 5) & ((nhost >= 2) if corroborate else True)
            chosen, covered = [], np.zeros(len(Zp), bool)
            for i in np.argsort(-support):
                if ok[i] and not covered[i] and len(chosen) < 10:
                    chosen.append(i); covered |= inside[i]
            if chosen:
                C_, R_ = Zp[chosen], r[chosen]
                fire = lambda Q: (dist(Q, C_) <= R_[None, :]).any(1)
                b_fpr = np.mean(fire(Z["benign_test"]) | (p["benign_test"] <= 0.01) | known["benign_test"])
                fire_h = fire(Z["heldout_test"])
                purity = np.mean([np.mean(lab[inside[i]] != "normal") > 0.5 for i in chosen])
            else:
                b_fpr = np.mean((p["benign_test"] <= 0.01) | known["benign_test"]); fire_h = np.zeros(len(T["heldout_test"]), bool); purity = np.nan
            base_h = (p["heldout_test"] <= 0.01) | known["heldout_test"]
            row = {"n": n, "rep": rep, "corroboration": corroborate, "vaccines": len(chosen), "attack_vaccine_share": purity,
                   "benign_fpr_system": b_fpr}
            for f in fams:
                m = T["heldout_test"] == f
                row[f"{f}_before"] = base_h[m].mean(); row[f"{f}_after"] = (base_h | fire_h)[m].mean()
                row[f"{f}_novel_before"] = 0.0; row[f"{f}_novel_caught"] = fire_h[m & novel["heldout_test"]].mean()
            out.append(row)
R = pd.DataFrame(out); R.to_csv(RUN / "experiments" / f"auto_vaccine_q{os.environ.get('QBALL', '0.005')}.csv", index=False)
pd.set_option("display.width", 250)
cols = ["vaccines", "attack_vaccine_share", "benign_fpr_system"] + [f"{f}_{s}" for f in fams for s in ["before", "after", "novel_caught"]]
print(R.groupby(["n", "corroboration"])[cols].mean().round(3).T.to_string())
