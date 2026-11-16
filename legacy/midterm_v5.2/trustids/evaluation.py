"""Helpers that assemble evaluation sets from cached scores, so notebooks 03 and 04 stay short.

Scores are cached per seed in artifacts/scores/seed{S}.npz with keys '{model}__{split}'.
Evaluation set = benign_test + dev_test (known attacks) + heldout_test (unseen attacks).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import Config

MODELS = ["ae", "iforest", "latent"]
EVAL_SPLITS = ["benign_test", "dev_test", "heldout_test"]


def scores_path(cfg: Config, seed: int) -> Path:
    p = cfg.artifacts / "scores"
    p.mkdir(parents=True, exist_ok=True)
    return p / f"seed{seed}.npz"


def save_scores(cfg: Config, seed: int, scores: dict) -> None:
    np.savez_compressed(scores_path(cfg, seed), **{f"{m}__{s}": v for (m, s), v in scores.items()})


def load_scores(cfg: Config, seed: int) -> dict:
    z = np.load(scores_path(cfg, seed))
    out = {}
    for k in z.files:
        m, s = k.split("__", 1)
        out[(m, s)] = z[k]
    return out


def available_seeds(cfg: Config) -> list:
    return [s for s in cfg.train_seeds if scores_path(cfg, s).exists()]


def eval_set(prepared: dict, scores: dict, model: str) -> dict:
    """Concatenate the three evaluation splits for one model."""
    s = np.concatenate([scores[(model, k)] for k in EVAL_SPLITS])
    t = np.concatenate([prepared["types"][k] for k in EVAL_SPLITS])
    split = np.concatenate([[k] * len(prepared["types"][k]) for k in EVAL_SPLITS])
    mult = np.concatenate([prepared["multiplicity"][k] for k in EVAL_SPLITS])
    coll = np.concatenate([prepared["collision"][k] for k in EVAL_SPLITS])
    return {"scores": s, "types": t, "split": split, "y_attack": t != "normal",
            "multiplicity": mult, "collision": coll, "cal": scores[(model, "benign_cal")],
            "train": scores[(model, "benign_train")]}


def family_groups(cfg: Config) -> dict:
    return {"normal": [cfg.normal_label], "known": list(cfg.dev_families),
            "held-out": list(cfg.heldout_families)}


def group_of(types: np.ndarray, cfg: Config) -> np.ndarray:
    g = np.full(len(types), "held-out", dtype=object)
    g[types == cfg.normal_label] = "normal"
    g[np.isin(types, cfg.dev_families)] = "known"
    return g
