"""Two calibrated questions instead of three classes (exploratory, seed 0, after seeing C1).
Q1 (one-class AE, conformal): is the flow normal?      not-normal  <=> p_AE  <= 0.05
Q2 (supervised RF on KNOWN families, conformal on benign_cal): does it look like a known attack? <=> RF > benign 99% quantile
Cells: NORMAL (no,no) | KNOWN-ATTACK (yes,yes) | NOVEL (not-normal, not known-like) | CAMOUFLAGED (normal-looking, known-like)."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trustids import conformal as C, data as D, evaluation as E  # noqa
from trustids.config import Config  # noqa
ROOT = Path(__file__).resolve().parents[1]; RUN = ROOT / "local_run_v52"
cfg = Config.load(RUN / "configs" / "default.json"); cfg.project_dir = str(RUN)
P = D.load_prepared(cfg.artifacts / "prepared"); X, T = P["X"], P["types"]
S = E.load_scores(cfg, 0)
rf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1, class_weight="balanced")
rf.fit(np.r_[X["benign_train"], X["dev_val"]], np.r_[np.zeros(len(X["benign_train"])), np.ones(len(X["dev_val"]))])
thr = np.quantile(rf.predict_proba(X["benign_cal"])[:, 1], 0.99, method="higher")
rows = []
for sp in ["benign_test", "dev_test", "heldout_test"]:
    nn_ = C.pvalues(S[("ae", "benign_cal")], S[("ae", sp)]) <= 0.05
    kn = rf.predict_proba(X[sp])[:, 1] > thr
    for f in np.unique(T[sp]):
        m = T[sp] == f
        rows.append({"split": sp, "family": f, "n": int(m.sum()),
                     "NORMAL": np.mean(~nn_[m] & ~kn[m]), "KNOWN-ATTACK": np.mean(nn_[m] & kn[m]),
                     "NOVEL": np.mean(nn_[m] & ~kn[m]), "CAMOUFLAGED": np.mean(~nn_[m] & kn[m])})
R = pd.DataFrame(rows); R.to_csv(RUN / "experiments" / "killtest_C3_two_questions.csv", index=False)
pd.set_option("display.width", 200); print(R.round(3).to_string(index=False))
