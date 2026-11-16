"""Reproducibility helpers: seeding, run folders, JSON saving, environment capture."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import sys
from datetime import datetime
from pathlib import Path

import numpy as np


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
        tf.keras.utils.set_random_seed(seed)
    except ImportError:
        pass


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def new_run_dir(root: str | Path, tag: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    d = Path(root) / f"{stamp}_{tag}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(type(o))


def save_json(obj, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, default=_default), encoding="utf-8")


def load_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def environment_info() -> dict:
    info = {"python": sys.version.split()[0], "platform": platform.platform()}
    for name in ["numpy", "pandas", "sklearn", "scipy", "tensorflow", "matplotlib"]:
        try:
            info[name] = __import__(name).__version__
        except ImportError:
            info[name] = None
    return info


# --------------------------------------------------------------------------- checkpoint / resume (Colab)
TRAINING_KEYS = ["dataset_name", "split_seed", "dev_families", "heldout_families", "benign_split", "drop_columns",
                 "device_feature_columns", "ae_variants", "ae_default", "epochs", "batch_size", "learning_rate",
                 "patience", "conv_window", "conv_rel_tol", "iforest_estimators"]


def config_fingerprint(cfg) -> str:
    """Hash of every setting that changes trained models or scores. Checkpoints are reused only when it matches."""
    from dataclasses import asdict
    d = asdict(cfg)
    blob = json.dumps({k: d.get(k) for k in TRAINING_KEYS}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def fingerprint(cfg, keys: list) -> str:
    """Hash of the given settings plus TRAINING_KEYS (final-phase caches: FL, LOFO)."""
    from dataclasses import asdict
    d = asdict(cfg)
    blob = json.dumps({k: d.get(k) for k in sorted(set(TRAINING_KEYS) | set(keys))}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:12]


def checkpoint_ok(art: str | Path, cfg, resume: bool = True) -> bool:
    """True if checkpoints in `art` were produced with the same training settings (safe to skip work).
    Writes the fingerprint when none exists. A mismatch disables resuming and says why."""
    p = Path(art) / "checkpoint_fingerprint.json"
    fp = config_fingerprint(cfg)
    if not p.exists():
        save_json({"fingerprint": fp}, p)
        return resume
    old = load_json(p).get("fingerprint")
    if old != fp:
        print(f"UYARI: kayıtlı ara sonuçlar farklı ayarlarla üretilmiş ({old} != {fp}); yeniden eğitilecek.")
        save_json({"fingerprint": fp}, p)
        return False
    return resume


def progress(cfg) -> dict:
    """What is already saved on Drive (so a new Colab session knows where to continue)."""
    art = Path(cfg.project_dir) / cfg.artifacts_dir
    seeds_done = [s for s in cfg.train_seeds if (art / "scores" / f"seed{s}.npz").exists()
                  and (art / "training" / f"seed{s}.json").exists()]
    return {
        "01_hazirlanan_veri": (art / "prepared" / "prepared.npz").exists(),
        "02_tohumlar_tamam": seeds_done,
        "02_oznitelik_karsilastirma_tohumlari": sorted(int(p.stem.replace("seed", "")) for p in (art / "featcmp").glob("seed*.json")) if (art / "featcmp").exists() else [],
        "03_kararlar": sorted(int(p.stem.replace("seed", "")) for p in (art / "decisions").glob("seed*.npz")) if (art / "decisions").exists() else [],
        "04b_host_eslesmesi": (art / "resolution" / "host_rows.csv.gz").exists(),
    }
