"""Phases 5-6 (final): federated learning with ONE training code path.

Professor's feedback, item 2: "find out why the federated model is clearly worse than the central one and
compare again under equivalent training conditions".

Midterm protocol (kept as 'orijinal' for comparison): FedAvg, 40 rounds x 5 local epochs, Keras Adam
re-created at every local fit (its state is lost every round), central baseline 200 epochs.
Measured on seed 0: unseen ANOMALY 47.0% (central) vs 13.7% (FedAvg-IID).

Two candidate causes are tested here, not assumed:
  H1 too few optimisation steps: with 5 IID clients each client runs ~4 batches per epoch, so 40 x 5 local
     epochs give ~800 local steps per client, against ~3,400 steps for 200 central epochs. Averaging client
     updates does not add their steps up.
     (The midterm comparison was equal in EPOCHS, i.e. passes over the data, but not in update steps.)
     'orijinal_kucuk_yigin' tests H1 from the FL side: same rounds and epochs, local batch = batch / K.
  H2 the optimiser state (Adam moments) is reset at every round.
  H3 client drift under non-IID data (FedProx is the standard remedy).

All models below use the same optimiser (Adam), learning rate, batch size, loss and, where stated, the same
convergence rule as the central model (proposal v5.2): stop when the best benign-val loss improves by less
than conv_rel_tol over conv_window epochs, or after `patience` epochs without improvement, or at the epoch
cap; the best weights are restored. For FL one round of E local epochs counts as E epochs, so the window,
patience and cap are converted to rounds with ceil(epochs / E). The FL validation loss is the loss on the
union of the clients' benign-val parts (= the size-weighted mean of the client losses).
"""
from __future__ import annotations

import math

import numpy as np

# name -> settings. 'rounds': None = convergence rule; an int = fixed number of rounds.
PROTOCOLS = {
    "orijinal":          {"rounds": "orig", "optimizer_state": "reset",      "mu": 0.0,
                          "aciklama": "ara dönem protokolü: 40 tur x 5 yerel epoch, Adam her turda sıfırlanır"},
    "orijinal_kucuk_yigin": {"rounds": "orig", "optimizer_state": "reset",   "mu": 0.0, "batch": "div_K",
                          "aciklama": "ara dönem protokolü, ama yerel yığın = yığın/K (istemci adım sayısı ≈ merkezi adım sayısı)"},
    "yakinsama_reset":   {"rounds": None,   "optimizer_state": "reset",      "mu": 0.0,
                          "aciklama": "yakınsama kuralına kadar, Adam her turda sıfırlanır"},
    "yakinsama_kalici":  {"rounds": None,   "optimizer_state": "persistent", "mu": 0.0,
                          "aciklama": "yakınsama kuralına kadar, her istemci Adam durumunu korur"},
    "fedprox_kalici":    {"rounds": None,   "optimizer_state": "persistent", "mu": "cfg",
                          "aciklama": "FedProx (μ = cfg.fl_fedprox_mu), yakınsama kuralına kadar, Adam korunur"},
}


# --------------------------------------------------------------------------- clients
def service_categories(X: np.ndarray, feature_names: list) -> np.ndarray:
    """Category of each benign vector = its one-hot 'service' value (non-IID partition key)."""
    svc = [i for i, f in enumerate(feature_names) if f.startswith("service=")]
    if not svc:
        return np.array(["tümü"] * len(X), dtype=object)
    lab = np.array([feature_names[svc[i]] for i in X[:, svc].argmax(1)], dtype=object)
    lab[X[:, svc].max(1) < 0.5] = "service=diğer"
    return lab


def partition(cats: dict, K: int, kind: str, seed: int) -> dict:
    """Same partition as the midterm notebook 05. cats: split -> category per vector.
    IID: every category split evenly; 'Dirichlet=a': per-category client shares ~ Dir(a).
    The same per-category shares are applied to every benign split (train/val/cal/test)."""
    rng = np.random.default_rng(seed)
    all_cats = sorted(set(np.concatenate(list(cats.values()))))
    if kind == "IID":
        props = {c: np.full(K, 1 / K) for c in all_cats}
    else:
        a = float(kind.split("=")[1])
        props = {c: rng.dirichlet([a] * K) for c in all_cats}
    parts = {}
    for sp, lab in cats.items():
        assign = np.empty(len(lab), dtype=int)
        for c in all_cats:
            idx = rng.permutation(np.where(lab == c)[0])
            cuts = (np.cumsum(props[c])[:-1] * len(idx)).astype(int)
            for k, chunk in enumerate(np.split(idx, cuts)):
                assign[chunk] = k
        parts[sp] = [np.where(assign == k)[0] for k in range(K)]
    return parts


# --------------------------------------------------------------------------- training
def _reset_optimizer(opt) -> None:
    """Equivalent to a freshly created Adam: zero moments, velocities and the step counter
    (the learning rate is left untouched)."""
    import tensorflow as tf
    for v in opt.variables:
        name = getattr(v, "path", None) or v.name
        if name.endswith("learning_rate"):
            continue
        v.assign(tf.zeros(v.shape, dtype=v.dtype))


def _make_step(model, opt, mu: float):
    import tensorflow as tf

    @tf.function(reduce_retracing=True)
    def step(xb, w_ref):
        with tf.GradientTape() as tape:
            rec = model(xb, training=True)
            loss = tf.reduce_mean(tf.square(xb - rec))           # = Keras 'mse' on the AE
            total = loss
            if mu > 0:
                prox = tf.add_n([tf.reduce_sum(tf.square(v - tf.cast(r, v.dtype))) for v, r in zip(model.trainable_variables, w_ref)])
                total = loss + tf.cast(0.5 * mu, loss.dtype) * tf.cast(prox, loss.dtype)
        g = tape.gradient(total, model.trainable_variables)
        opt.apply_gradients(zip(g, model.trainable_variables))
        return loss
    return step


def _mse(model, X: np.ndarray, batch: int = 8192) -> float:
    out = []
    for i in range(0, len(X), batch):
        xb = X[i:i + batch]
        rec = model(xb, training=False).numpy()
        out.append(np.sum(np.mean((xb.astype(np.float64) - rec) ** 2, axis=1)))
    return float(np.sum(out) / len(X))


def _set(model, weights) -> None:
    for v, w in zip(model.trainable_variables, weights):
        v.assign(w)


def train_federated(build_model, X_train: np.ndarray, parts_train: list, X_val: np.ndarray, *,
                    rounds: int | None, local_epochs: int, lr: float, batch_size: int, seed: int,
                    optimizer_state: str = "reset", mu: float = 0.0,
                    conv_window: int = 50, conv_rel_tol: float = 0.005, patience: int = 40, epoch_cap: int = 1500,
                    verbose: bool = False):
    """FedAvg (mu = 0) or FedProx (mu > 0) with size-weighted averaging.

    rounds=int  -> exactly that many rounds (the midterm protocol);
    rounds=None -> convergence rule on the federated benign-val loss (see module docstring).
    Returns (global_model, info). K = 1 with the full training set is central training on this code path."""
    import tensorflow as tf
    from . import utils

    utils.set_seed(seed)
    g = build_model()
    local = build_model()
    assert len(g.trainable_variables) == len(g.get_weights()), "AE has non-trainable weights; averaging would skip them"
    w = [v.numpy().astype(np.float32) for v in g.trainable_variables]
    K = len(parts_train)
    n = np.array([len(p) for p in parts_train], dtype=float)
    opts = [tf.keras.optimizers.Adam(learning_rate=lr) for _ in range(K)]
    for o in opts:
        o.build(local.trainable_variables)
    steps = [_make_step(local, o, mu) for o in opts]
    rng = np.random.default_rng(seed)
    E = local_epochs
    if rounds is None:
        r_window, r_pat, r_cap = math.ceil(conv_window / E), math.ceil(patience / E), math.ceil(epoch_cap / E)
    else:
        r_window = r_pat = None
        r_cap = rounds
    best_hist, val_hist, best_w, best_round, since_best = [], [], None, 0, 0
    stopped_by = "fixed_rounds" if rounds is not None else "epoch_cap"
    local_steps = np.zeros(K, dtype=int)
    for r in range(r_cap):
        new = []
        w_ref = [tf.constant(x) for x in w]
        for k in range(K):
            if n[k] == 0:
                new.append([x.copy() for x in w]); continue
            _set(local, w)
            if optimizer_state == "reset":
                _reset_optimizer(opts[k])
            Xk = X_train[parts_train[k]]
            for _ in range(E):
                perm = rng.permutation(len(Xk))
                for i in range(0, len(Xk), batch_size):
                    steps[k](tf.constant(Xk[perm[i:i + batch_size]]), w_ref)
                    local_steps[k] += 1
            new.append([v.numpy() for v in local.trainable_variables])
        # keep float32: averaging with float64 client sizes would silently turn the weights into float64
        w = [(sum(n[k] * new[k][j] for k in range(K)) / n.sum()).astype(np.float32) for j in range(len(w))]
        if rounds is None:
            _set(g, w)
            v = _mse(g, X_val)
            val_hist.append(v)
            if not best_hist or v < best_hist[-1]:
                best_w, best_round, since_best = [x.copy() for x in w], r + 1, 0
            else:
                since_best += 1
            best_hist.append(min(v, best_hist[-1]) if best_hist else v)
            if verbose and (r + 1) % 10 == 0:
                print(f"  tur {r + 1}: doğrulama kaybı {v:.6f} (en iyi {best_hist[-1]:.6f})", flush=True)
            if len(best_hist) > r_window:
                old, cur = best_hist[-r_window - 1], best_hist[-1]
                if old > 0 and (old - cur) / old < conv_rel_tol:
                    stopped_by = "relative_plateau"; break
            if since_best >= r_pat:
                stopped_by = "early_stopping"; break
    rounds_run = (r + 1)
    _set(g, best_w if (rounds is None and best_w is not None) else w)
    n_par = int(sum(np.prod(x.shape) for x in w))
    info = {"rounds_run": rounds_run, "best_round": best_round if rounds is None else rounds_run,
            "stopped_by": stopped_by, "epochs_equivalent": rounds_run * E,
            "local_steps_mean": float(local_steps.mean()), "local_steps_max": int(local_steps.max()),
            "val_loss_best": float(min(val_hist)) if val_hist else _mse(g, X_val),
            "comm_MB": n_par * 4 * 2 * K * rounds_run / 1e6, "clients": K, "local_epochs": E,
            "optimizer_state": optimizer_state, "mu": mu, "val_hist": [float(x) for x in val_hist]}
    return g, info


def run_protocol(name: str, cfg, build_model, X_train, parts_train, X_val, seed: int, verbose: bool = False):
    p = PROTOCOLS[name]
    rounds = cfg.fl_orig_rounds if p["rounds"] == "orig" else p["rounds"]
    mu = cfg.fl_fedprox_mu if p["mu"] == "cfg" else p["mu"]
    bs = max(1, math.ceil(cfg.batch_size / len(parts_train))) if p.get("batch") == "div_K" else cfg.batch_size
    return train_federated(build_model, X_train, parts_train, X_val, rounds=rounds, local_epochs=cfg.fl_local_epochs,
                           lr=cfg.learning_rate, batch_size=bs, seed=seed,
                           optimizer_state=p["optimizer_state"], mu=mu, conv_window=cfg.conv_window,
                           conv_rel_tol=cfg.conv_rel_tol, patience=cfg.patience, epoch_cap=cfg.epochs, verbose=verbose)


# --------------------------------------------------------------------------- evaluation
def evaluate(score_fn, parts: dict, X: dict, cfg, seed: int, per_client_models: bool = False, detail: list | None = None) -> list:
    """Evaluate one FL configuration.

    score_fn(k, split) -> scores of client k's model on X[split] (all rows of that split).
    Calibration modes:
      'istemci başına'  each client calibrates on its own benign_cal part (deployable as is);
      'havuz skor'      clients send their benign_cal SCORES (not data) to the server, which pools them
                        (deployable only if sharing scalar scores is acceptable; reported as such).
    False alarms are measured on each client's own benign_test part; attack rates on the shared
    known (dev_test) and unseen (heldout_test) sets. Per-client numbers are averaged; the worst client is kept.
    If `detail` is a list, one row per client (and calibration mode) is appended to it."""
    from . import conformal as C, metrics as MT
    K = len(parts["benign_cal"])
    cache = {}

    def S(k, sp):
        key = (k if per_client_models else 0, sp)
        if key not in cache:
            cache[key] = score_fn(key[0], sp)
        return cache[key]

    modes = ["istemci başına"] + ([] if per_client_models else ["havuz skor"])
    pooled = None if per_client_models else np.concatenate([S(0, "benign_cal")[parts["benign_cal"][k]] for k in range(K)])
    rows = []
    for mode in modes:
        per, skipped = [], 0
        for k in range(K):
            ci, ti = parts["benign_cal"][k], parts["benign_test"][k]
            s_cal = S(k, "benign_cal")
            # a client with no model, no benign test data or (per-client mode) no calibration data cannot be evaluated
            if s_cal is None or len(ti) == 0 or (mode == "istemci başına" and len(ci) == 0):
                skipped += 1
                continue
            cal = s_cal[ci] if mode == "istemci başına" else pooled
            bt = S(k, "benign_test")[ti]
            ho, kn = S(k, "heldout_test"), S(k, "dev_test")
            pb, ph, pk = (C.pvalues(cal, x, seed=seed, model="ae") for x in (bt, ho, kn))
            db, dh, dk = (C.decide(p, cfg.alpha, cfg.beta) for p in (pb, ph, pk))
            # one evaluation set per client: its own benign test + the shared attack sets
            y = np.r_[np.zeros(len(db)), np.ones(len(dk) + len(dh))].astype(bool)
            d_all = np.r_[db, dk, dh]
            bm = MT.binary_metrics(np.r_[np.zeros(len(db)), np.ones(len(dh))], np.r_[-pb, -ph], np.r_[db, dh] == C.ANOMALY)
            sm = MT.selective_metrics(y, d_all)
            per.append({"kalibrasyon": mode, "istemci": k, "n_cal": len(cal), "n_test": len(bt), "FPR": np.mean(db == C.ANOMALY),
                        "normal_UNCERTAIN": np.mean(db == C.UNCERTAIN),
                        "görülmemiş_ANOMALY": np.mean(dh == C.ANOMALY), "görülmemiş_UNCERTAIN": np.mean(dh == C.UNCERTAIN),
                        "görülmemiş_kaçan": np.mean(dh == C.NORMAL), "bilinen_ANOMALY": np.mean(dk == C.ANOMALY),
                        "precision_görülmemiş": bm["precision"], "recall_görülmemiş": bm["recall"], "f1_görülmemiş": bm["f1"],
                        "coverage": sm["coverage"], "selective_risk": sm["selective_risk"]})
        if not per:
            continue
        if detail is not None:
            detail.extend(per)
        P = __import__("pandas").DataFrame(per)
        # the worst client can be a very small one (few benign test vectors), so the size-weighted rate is given too
        row = {"kalibrasyon": mode, "istemci_FPR_ort": P["FPR"].mean(), "istemci_FPR_en_kötü": P["FPR"].max(),
               "istemci_FPR_ağırlıklı": float(np.average(P["FPR"], weights=P["n_test"])),
               "en_kötü_istemci_n_test": int(P.loc[P["FPR"].idxmax(), "n_test"]),
               "en_küçük_n_cal": int(P["n_cal"].min()), "atlanan_istemci": skipped}
        for c in ["normal_UNCERTAIN", "görülmemiş_ANOMALY", "görülmemiş_UNCERTAIN", "görülmemiş_kaçan", "bilinen_ANOMALY",
                  "precision_görülmemiş", "recall_görülmemiş", "f1_görülmemiş", "coverage", "selective_risk"]:
            row[c] = P[c].mean()
        rows.append(row)
    return rows
