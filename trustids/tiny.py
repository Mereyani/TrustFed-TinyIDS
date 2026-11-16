"""Phase 7 (TinyML) and Phase 8 (robustness) helpers, shared by the final notebooks.

Latency is measured with the TFLite interpreter on the machine that runs the notebook (Colab CPU).
It is a reference number only, NOT a microcontroller measurement (professor: "Colab sonuçlarını
doğrudan ESP32 performansı olarak sunmamalısın").
"""
from __future__ import annotations

import time

import numpy as np


def representative(X_train: np.ndarray, n: int = 500, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return X_train[rng.choice(len(X_train), min(n, len(X_train)), replace=False)].astype(np.float32)


def convert(model, rep: np.ndarray, int8: bool) -> bytes:
    import contextlib, io
    import tensorflow as tf
    cv = tf.lite.TFLiteConverter.from_keras_model(model)
    if int8:
        cv.optimizations = [tf.lite.Optimize.DEFAULT]
        cv.representative_dataset = lambda: ([r[None, :]] for r in rep)
        cv.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    with contextlib.redirect_stdout(io.StringIO()):     # the converter prints a long export summary per model
        return cv.convert()


def _interpreter(blob: bytes):
    """TFLite interpreter. Newer TensorFlow releases move it to the LiteRT package (ai-edge-litert)."""
    import tensorflow as tf
    if hasattr(tf.lite, "Interpreter"):
        return tf.lite.Interpreter(model_content=blob)
    from ai_edge_litert.interpreter import Interpreter
    return Interpreter(model_content=blob)


def self_test() -> str:
    """Convert and run a tiny model, so a missing converter / interpreter is found BEFORE hours of training."""
    import tensorflow as tf
    m = tf.keras.Sequential([tf.keras.Input((4,)), tf.keras.layers.Dense(3, activation="relu"), tf.keras.layers.Dense(4)])
    x = np.random.default_rng(0).random((20, 4)).astype(np.float32)
    try:
        for int8 in (False, True):
            s = tflite_score(convert(m, x, int8), x)
            assert s.shape == (20,) and np.all(np.isfinite(s))
    except Exception as e:                                        # stop early with a clear instruction
        raise RuntimeError("TFLite dönüştürücü / yorumlayıcı bu ortamda çalışmadı (" + repr(e) + "). "
                           "Colab'da yeni bir hücrede `!pip install ai-edge-litert` çalıştırıp defteri yeniden başlatın; "
                           "sorun sürerse çıktıyı gönderin.") from e
    return "TFLite dönüştürme ve INT8 çalıştırma testi geçti (TensorFlow " + tf.__version__ + ")"


def tflite_score(blob: bytes, X: np.ndarray) -> np.ndarray:
    it = _interpreter(blob)
    inp, out = it.get_input_details()[0], it.get_output_details()[0]
    it.resize_tensor_input(inp["index"], [len(X), X.shape[1]])
    it.allocate_tensors()
    it.set_tensor(inp["index"], X.astype(np.float32))
    it.invoke()
    R = it.get_tensor(out["index"])
    return np.mean((X.astype(np.float64) - R.astype(np.float64)) ** 2, axis=1)


def latency_us(blob: bytes, x: np.ndarray, n: int = 2000) -> float:
    """Mean single-sample invoke time (µs) on THIS machine (Colab CPU): a reference, not an MCU number."""
    it = _interpreter(blob)
    inp = it.get_input_details()[0]
    it.allocate_tensors()
    it.set_tensor(inp["index"], x[None, :].astype(np.float32))
    t0 = time.perf_counter()
    for _ in range(n):
        it.invoke()
    return (time.perf_counter() - t0) / n * 1e6


def ram_estimate_kb(model) -> float:
    """Rough INT8 estimate: (parameters + activations of all Dense layers) x 1 byte.
    Excludes the TFLite-Micro arena overhead, biases stored as int32 and the input buffer."""
    acts = sum(int(l.units) for l in model.layers if hasattr(l, "units"))
    return (model.count_params() + acts) / 1024


def corrupt(X: np.ndarray, kind: str, level: float, rng, median: np.ndarray, cols=None) -> np.ndarray:
    """Phase 8 corruptions in the scaled feature space (labels are never changed).
    'gürültü'       Gaussian noise with standard deviation `level` on every feature;
    'eksik'         a share `level` of the values is missing -> filled with the benign-train median;
    'bozuk özellik' the values of the feature columns `cols` are shuffled across the samples of the split,
                    so each corrupted feature keeps its distribution but no longer matches the rest of the flow."""
    if kind == "temiz":
        return X
    if kind == "gürültü":
        return X + rng.normal(0, level, X.shape)
    if kind == "eksik":
        Z = X.copy()
        mask = rng.random(X.shape) < level
        Z[mask] = np.broadcast_to(median, X.shape)[mask]
        return Z
    if kind == "bozuk özellik":
        Z = X.copy()
        for c in cols:
            Z[:, c] = Z[rng.permutation(len(Z)), c]
        return Z
    raise ValueError(kind)


# level: noise std / missing share / number of corrupted features
CORRUPTIONS = [("temiz", [0.0]), ("gürültü", [0.01, 0.05, 0.10]), ("eksik", [0.05, 0.10, 0.20]), ("bozuk özellik", [1, 3, 5])]
