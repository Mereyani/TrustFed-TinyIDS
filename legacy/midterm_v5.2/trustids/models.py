"""Phase 2: Isolation Forest reference model and the lightweight Autoencoder.

Both produce an anomaly score s(x) where larger means more anomalous. Thresholds are
NOT chosen here: the trust-aware decision (Phase 3) turns scores into decisions.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest


# --------------------------------------------------------------------------- Isolation Forest
def fit_iforest(X_train: np.ndarray, n_estimators: int, seed: int) -> IsolationForest:
    return IsolationForest(n_estimators=n_estimators, random_state=seed, n_jobs=-1).fit(X_train)


def iforest_score(model: IsolationForest, X: np.ndarray) -> np.ndarray:
    return -model.score_samples(X)


# --------------------------------------------------------------------------- Autoencoder
def build_autoencoder(input_dim: int, hidden=(32, 16, 8), dropout: float = 0.0, lr: float = 1e-3):
    """Professor's starting architecture: Input -> 32 -> 16 -> 8 -> 16 -> 32 -> Input."""
    import tensorflow as tf
    from tensorflow import keras

    inp = keras.Input(shape=(input_dim,), name="features")
    x = inp
    for i, h in enumerate(hidden[:-1]):
        x = keras.layers.Dense(h, activation="relu", name=f"enc_{i}")(x)
        if dropout:
            x = keras.layers.Dropout(dropout)(x)
    z = keras.layers.Dense(hidden[-1], activation="relu", name="latent")(x)
    x = z
    for i, h in enumerate(reversed(hidden[:-1])):
        x = keras.layers.Dense(h, activation="relu", name=f"dec_{i}")(x)
        if dropout:
            x = keras.layers.Dropout(dropout)(x)
    out = keras.layers.Dense(input_dim, activation="linear", name="reconstruction")(x)
    model = keras.Model(inp, out, name="ae_" + "_".join(map(str, hidden)))
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=lr), loss="mse")
    return model


def plateau_reached(best_hist: list, window: int, rel_tol: float) -> bool:
    """Convergence test on the running BEST benign-val loss: True when it improved by less than
    rel_tol (relative) over the last `window` epochs. Pure function, unit-tested."""
    if len(best_hist) <= window:
        return False
    old, new = best_hist[-window - 1], best_hist[-1]
    return old > 0 and (old - new) / old < rel_tol


def _relative_plateau_callback(window: int, rel_tol: float):
    from tensorflow import keras

    class RelativePlateau(keras.callbacks.Callback):
        def __init__(self):
            super().__init__()
            self.best_hist, self.stopped_epoch, self.best_w = [], None, None

        def on_epoch_end(self, epoch, logs=None):
            v = float(logs["val_loss"])
            if not self.best_hist or v < self.best_hist[-1]:
                self.best_w = self.model.get_weights()
            self.best_hist.append(min(v, self.best_hist[-1]) if self.best_hist else v)
            if plateau_reached(self.best_hist, window, rel_tol):
                self.stopped_epoch = epoch + 1
                self.model.stop_training = True

        def on_train_end(self, logs=None):
            # always end on the best benign-val weights, whichever rule stopped training
            if self.best_w is not None:
                self.model.set_weights(self.best_w)

    return RelativePlateau()


def train_autoencoder(model, X_train, X_val, epochs: int, batch_size: int, patience: int, verbose: int = 0,
                      conv_window: int = 50, conv_rel_tol: float = 0.005):
    """Train on benign-train with a CONSTANT learning rate; every stopping decision uses benign-val
    loss only (no attack data, no calibration data). Convergence rule (proposal v5.2):
      * stop when the best val loss improves < conv_rel_tol (0.5%) over conv_window (50) epochs,
        or by early stopping (patience), or at the epoch cap; the best weights are restored.
    No learning-rate scheduler: an earlier ReduceLROnPlateau version shrank the rate to its floor
    within ~150 epochs, so the plateau test fired because the optimiser had slowed down, not because
    the model had converged (superpowers code review, C1). Measured on seed 0 (real data): the rule
    fires at epoch 1021 with best val loss 0.000864 vs 0.000858 at 1500 epochs.
    The returned history contains 'stopped_by', 'epochs_run' and 'best_epoch'."""
    from tensorflow import keras

    plateau = _relative_plateau_callback(conv_window, conv_rel_tol)
    es = keras.callbacks.EarlyStopping(monitor="val_loss", patience=patience, restore_best_weights=False)
    hist = model.fit(X_train, X_train, validation_data=(X_val, X_val), epochs=epochs,
                     batch_size=batch_size, shuffle=True, callbacks=[es, plateau], verbose=verbose)
    h = {k: [float(x) for x in v] for k, v in hist.history.items()}
    if plateau.stopped_epoch is not None:
        h["stopped_by"] = "relative_plateau"
    elif es.stopped_epoch:
        h["stopped_by"] = "early_stopping"
    else:
        h["stopped_by"] = "epoch_cap"
    h["epochs_run"] = len(h["val_loss"])
    h["best_epoch"] = int(np.argmin(h["val_loss"])) + 1
    return h


def ae_score(model, X: np.ndarray, batch_size: int = 4096) -> np.ndarray:
    """Per-sample mean squared reconstruction error."""
    rec = model.predict(X, batch_size=batch_size, verbose=0)
    # float64 accumulation: float32 MSE produced ~0.4% tied scores at n=60k, which silently
    # switched the AE to randomized p-values (committee round 4, R4-B1)
    return np.mean((X.astype(np.float64) - rec.astype(np.float64)) ** 2, axis=1)


def ae_feature_errors(model, X: np.ndarray, batch_size: int = 4096) -> np.ndarray:
    """Per-feature squared error (used later for explanations; not part of the midterm)."""
    rec = model.predict(X, batch_size=batch_size, verbose=0)
    return (X.astype(np.float64) - rec.astype(np.float64)) ** 2


class LatentMahalanobis:
    """Alternative score for E2 (baseline B5): Mahalanobis distance of the AE latent code,
    with mean and (Ledoit-Wolf) covariance fit on benign-train only."""

    def __init__(self, ae_model, layer_name: str = "latent"):
        from tensorflow import keras
        self.encoder = keras.Model(ae_model.input, ae_model.get_layer(layer_name).output)

    def fit(self, X_train: np.ndarray) -> "LatentMahalanobis":
        from sklearn.covariance import LedoitWolf
        z = self.encoder.predict(X_train, batch_size=4096, verbose=0).astype(np.float64)
        self.cov_ = LedoitWolf().fit(z)
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        z = self.encoder.predict(X, batch_size=4096, verbose=0).astype(np.float64)
        return self.cov_.mahalanobis(z)


def count_parameters(model) -> int:
    return int(model.count_params())
