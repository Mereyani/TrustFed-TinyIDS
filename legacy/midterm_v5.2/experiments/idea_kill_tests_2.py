"""Follow-up checks (after seeing idea_kill_tests results; exploratory, seed 0).
C1: does the supervised RF alone (known families) already detect held-out families at 1% benign FPR?
C2: cross-host transfer of the k-shot vaccine: label k UNCERTAIN vectors whose representative row comes from one
    source host, evaluate on vectors of the same family from OTHER source hosts (proxy for site A -> site B in FL)."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trustids import conformal as C, data as D, evaluation as E  # noqa
from trustids.config import Config  # noqa
from tensorflow import keras  # noqa
ROOT = Path(__file__).resolve().parents[1]; RUN = ROOT / "local_run_v52"
cfg = Config.load(RUN / "configs" / "default.json"); cfg.project_dir = str(RUN)
P = D.load_prepared(cfg.artifacts / "prepared"); X, T, I = P["X"], P["types"], P["index"]
S = E.load_scores(cfg, 0)
raw = D.load_raw(ROOT / "data" / "train_test_network.csv", cfg)
host = raw["src_ip"].astype(str).to_numpy()[I["heldout_test"]]
rf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1, class_weight="balanced")
rf.fit(np.r_[X["benign_train"], X["dev_val"]], np.r_[np.zeros(len(X["benign_train"])), np.ones(len(X["dev_val"]))])
cal_rf = rf.predict_proba(X["benign_cal"])[:, 1]
thr = np.quantile(cal_rf, 0.99, method="higher")
print("C1: RF alone, threshold = benign_cal 99% quantile")
print("  benign_test FPR", round(float((rf.predict_proba(X["benign_test"])[:, 1] > thr).mean()), 4))
hs = rf.predict_proba(X["heldout_test"])[:, 1]
for f in cfg.heldout_families:
    m = T["heldout_test"] == f
    print(f"  {f}: RF recall {np.mean(hs[m] > thr):.3f}   AE ANOMALY {np.mean(C.pvalues(S[('ae','benign_cal')], S[('ae','heldout_test')][m]) <= 0.01):.3f}")
ae = keras.models.load_model(cfg.artifacts / "models" / "ae_seed0.keras")
enc = keras.Model(ae.input, ae.get_layer("latent").output)
Z = {sp: enc.predict(X[sp], batch_size=4096, verbose=0).astype(np.float64) for sp in ["benign_cal", "benign_test", "heldout_test"]}
p = C.pvalues(S[("ae", "benign_cal")], S[("ae", "heldout_test")])
U = (p > 0.01) & (p <= 0.05); A = p <= 0.01
def nn(Q, R): return np.sqrt(((Q[:, None, :] - R[None]) ** 2).sum(-1).min(1))
rng = np.random.default_rng(1); rows = []
for f in cfg.heldout_families:
    m = T["heldout_test"] == f
    hosts = pd.Series(host[m]).value_counts()
    print(f"C2 {f}: hosts {hosts.to_dict()}")
    for h in hosts.index:
        src = np.where(m & U & (host == h))[0]; tgt = np.where(m & (host != h))[0]
        if len(src) < 5 or len(tgt) < 20: continue
        for k in [1, 5]:
            for d in range(30):
                R = Z["heldout_test"][rng.choice(src, k, replace=False)]
                t = np.quantile(nn(Z["benign_cal"], R), 0.01, method="lower")
                det = (nn(Z["heldout_test"][tgt], R) <= t) | A[tgt]
                rows.append({"family": f, "src_host": h, "k": k, "n_target": len(tgt),
                             "recall_before": A[tgt].mean(), "recall_after": det.mean(),
                             "benign_fpr_vaccine": (nn(Z["benign_test"], R) <= t).mean()})
R = pd.DataFrame(rows); R.to_csv(RUN / "experiments" / "killtest_C2_cross_host.csv", index=False)
print(R.groupby(["family", "src_host", "k"])[["n_target", "recall_before", "recall_after", "benign_fpr_vaccine"]].mean().round(3).to_string())
