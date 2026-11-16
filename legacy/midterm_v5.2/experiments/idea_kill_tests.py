"""Quick go/no-go tests for the brainstorm shortlist (2026-11-05). Seed 0 only, cached v5.2 artifacts, exploratory.
Rules fixed before running.

A. Cascade (UNCERTAIN -> gateway). Inside the seed-0 AE UNCERTAIN band, ROC-AUC of held-out vs benign for
   gateway candidates: the AE score itself, IF, latent-Mahalanobis, and a supervised RandomForest trained on
   benign_train vs dev_val (known families only). Kill: best AUC <= 0.6 for a family.

B1. Vaccination (k-shot). For each held-out family F, an analyst labels k vectors drawn from F's UNCERTAIN set.
    Vaccine score = distance to the nearest labelled vector, in two representations:
    z (8-dim latent) and e (53-dim per-feature squared reconstruction error, i.e. the "why it is odd" profile).
    Fires if distance <= the 1% quantile of benign_cal distances (conformal, so the vaccine adds <= 1% benign FPR).
    Report F recall on the unlabelled rest of F (ANOMALY by AE or vaccine), the benign_test FPR of the combined
    rule, and cross-family firing. k in {1, 5, 10, 20}, 50 draws.

B2. Discovery under an analyst budget. Review pool = all benign_test UNCERTAIN vectors + m = 5 random UNCERTAIN
    vectors per held-out family (about 9% attacks, close to the UNCERTAIN-tier precision at 1% prevalence).
    Orders: random; lowest p first; cluster-first (k-means, K = 20 on e, one medoid per cluster with >= 2 members,
    clusters ordered by mean intra-cluster distance, ascending). Metric: reviews until all 3 families are seen.
    200 repetitions.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.cluster import KMeans

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from trustids import conformal as C, data as D, evaluation as E  # noqa: E402
from trustids.config import Config  # noqa: E402
from tensorflow import keras  # noqa: E402

RUN = ROOT / "local_run_v52"
cfg = Config.load(RUN / "configs" / "default.json"); cfg.project_dir = str(RUN)
P = D.load_prepared(cfg.artifacts / "prepared")
X, T = P["X"], P["types"]
S = E.load_scores(cfg, 0)
ae = keras.models.load_model(cfg.artifacts / "models" / "ae_seed0.keras")
enc = keras.Model(ae.input, ae.get_layer("latent").output)
rep = {}
for sp in ["benign_cal", "benign_test", "dev_test", "heldout_test", "benign_train", "dev_val"]:
    rep[("z", sp)] = enc.predict(X[sp], batch_size=4096, verbose=0).astype(np.float64)
    rep[("e", sp)] = (X[sp] - ae.predict(X[sp], batch_size=4096, verbose=0)).astype(np.float64) ** 2
cal = S[("ae", "benign_cal")]
p = {sp: C.pvalues(cal, S[("ae", sp)], seed=0, model="ae") for sp in ["benign_test", "heldout_test", "dev_test"]}
a, b = cfg.alpha, cfg.beta
U = {sp: (p[sp] > a) & (p[sp] <= a + b) for sp in p}
A_ = {sp: p[sp] <= a for sp in p}
fams = cfg.heldout_families
out = RUN / "experiments"; out.mkdir(exist_ok=True)

# ---------------- A: cascade
rf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1, class_weight="balanced")
rf.fit(np.r_[X["benign_train"], X["dev_val"]], np.r_[np.zeros(len(X["benign_train"])), np.ones(len(X["dev_val"]))])
rowsA = []
bt = U["benign_test"]
for f in fams:
    ft = U["heldout_test"] & (T["heldout_test"] == f)
    y = np.r_[np.zeros(bt.sum()), np.ones(ft.sum())]
    for name, sc in [("AE (same score)", lambda sp: S[("ae", sp)]), ("IF", lambda sp: S[("iforest", sp)]),
                     ("latent-Mahalanobis", lambda sp: S[("latent", sp)]),
                     ("supervised RF (known families)", lambda sp: rf.predict_proba(X[sp])[:, 1])]:
        s = np.r_[sc("benign_test")[bt], sc("heldout_test")[ft]]
        rowsA.append({"family": f, "gateway": name, "n_benign_U": int(bt.sum()), "n_attack_U": int(ft.sum()),
                      "auc_inside_band": roc_auc_score(y, s)})
RA = pd.DataFrame(rowsA); RA.to_csv(out / "killtest_A_cascade.csv", index=False)
print("=== A: AUC inside the UNCERTAIN band (held-out vs benign)")
print(RA.pivot(index="gateway", columns="family", values="auc_inside_band").round(3).to_string())
print("band sizes:", RA.groupby("family")[["n_benign_U", "n_attack_U"]].first().to_dict())

# ---------------- B1: vaccination
def nn_dist(Q, R):
    d = ((Q[:, None, :] - R[None, :, :]) ** 2).sum(-1)
    return np.sqrt(d.min(1))

rng = np.random.default_rng(0)
rowsB = []
for r in ["z", "e"]:
    for f in fams:
        idxU = np.where(U["heldout_test"] & (T["heldout_test"] == f))[0]
        idxF = np.where(T["heldout_test"] == f)[0]
        for k in [1, 5, 10, 20]:
            if len(idxU) < k:
                continue
            for draw in range(50):
                lab = rng.choice(idxU, k, replace=False)
                R = rep[(r, "heldout_test")][lab]
                thr = np.quantile(nn_dist(rep[(r, "benign_cal")], R), 0.01, method="lower")
                rest = np.setdiff1d(idxF, lab)
                fire = nn_dist(rep[(r, "heldout_test")][rest], R) <= thr
                det = fire | A_["heldout_test"][rest]
                bfire = nn_dist(rep[(r, "benign_test")], R) <= thr
                others = np.where(T["heldout_test"] != f)[0]
                rowsB.append({"rep": r, "family": f, "k": k, "draw": draw,
                              "recall_before": A_["heldout_test"][rest].mean(), "recall_after": det.mean(),
                              "benign_fpr_combined": (bfire | A_["benign_test"]).mean(),
                              "vaccine_benign_fpr": bfire.mean(),
                              "fires_on_other_heldout": (nn_dist(rep[(r, "heldout_test")][others], R) <= thr).mean()})
RB = pd.DataFrame(rowsB); RB.to_csv(out / "killtest_B1_vaccination.csv", index=False)
print("=== B1: k-shot vaccination (mean over 50 draws)")
print(RB.groupby(["rep", "family", "k"])[["recall_before", "recall_after", "benign_fpr_combined",
                                         "fires_on_other_heldout"]].mean().round(3).to_string())

# ---------------- B2: discovery
bU = np.where(U["benign_test"])[0]
rowsD = []
for rep_i in range(200):
    pick = [rng.choice(np.where(U["heldout_test"] & (T["heldout_test"] == f))[0], 5, replace=False) for f in fams]
    E_ = np.r_[rep[("e", "benign_test")][bU], np.concatenate([rep[("e", "heldout_test")][x] for x in pick])]
    lab = np.r_[["normal"] * len(bU), np.repeat(fams, 5)]
    pv = np.r_[p["benign_test"][bU], np.concatenate([p["heldout_test"][x] for x in pick])]
    def reviews(order):
        seen = set()
        for i, j in enumerate(order, 1):
            if lab[j] != "normal":
                seen.add(lab[j])
            if len(seen) == 3:
                return i
        return len(order)
    km = KMeans(n_clusters=20, n_init=4, random_state=rep_i).fit(E_)
    cl = []
    for c in range(20):
        mem = np.where(km.labels_ == c)[0]
        if len(mem) < 2:
            continue
        d = np.sqrt(((E_[mem] - km.cluster_centers_[c]) ** 2).sum(1))
        cl.append((d.mean(), mem[np.argmin(d)]))
    cl_order = [m for _, m in sorted(cl)]
    rest = [j for j in rng.permutation(len(lab)) if j not in set(cl_order)]
    rowsD.append({"rep": rep_i, "pool": len(lab), "random": reviews(rng.permutation(len(lab))),
                  "lowest_p_first": reviews(np.argsort(pv, kind="stable")),
                  "cluster_first": reviews(cl_order + rest)})
RD = pd.DataFrame(rowsD); RD.to_csv(out / "killtest_B2_discovery.csv", index=False)
print("=== B2: reviews needed to see all 3 held-out families (pool size ~%d)" % RD["pool"].iloc[0])
print(RD[["random", "lowest_p_first", "cluster_first"]].describe().round(1).to_string())
