"""Resolving UNCERTAIN (proposal v6, §7a): UNCERTAIN must never be a silent dead end.

The decision ladder after the three-way flow decision:
  Rung 0 (device, immediate): UNCERTAIN -> reversible hold (monitor / rate-limit), never silence.
  Rung 2 (device, central):   per-host counter K = #flows with p <= alpha + beta in a window of W flows;
                              escalate the host if K >= k*, else release the hold.
                              k* is a split-conformal threshold on benign windows, with the per-window budget
                              derived from an OPERATIONAL budget (false escalations per device per week).
  Rung 1 (gateway, optional): a supervised head on known families; reported mainly as a baseline.

Version B of TON_IoT has no timestamps, so host windows are random draws (a simulated stream); this is
stated wherever the numbers are reported.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config


# --------------------------------------------------------------------------- operational budget
def window_budget(budget_per_week: float, W: int, flows_per_day: float) -> float:
    """Per-window false-escalation budget so that a device with `flows_per_day` flows, split into
    windows of W flows, has at most `budget_per_week` false escalations per week (in expectation)."""
    windows_per_week = 7.0 * flows_per_day / W
    return min(1.0, budget_per_week / windows_per_week)


def per_week(rate_per_window: float, W: int, flows_per_day: float) -> float:
    """Convert a per-window false-escalation rate into false escalations per device per week."""
    return rate_per_window * 7.0 * flows_per_day / W


# --------------------------------------------------------------------------- calibrated threshold
def k_threshold(K_cal: np.ndarray, a: float) -> int:
    """Smallest k with (1 + #{K_cal >= k}) / (n + 1) <= a  (split-conformal; ties counted against us).
    Returns W+1-like 'never' value (max+1) when the budget cannot be met with n calibration windows."""
    K_cal = np.asarray(K_cal)
    n = len(K_cal)
    if n == 0:
        return 10 ** 9                              # no calibration windows: never escalate (disclosed as such)
    counts = np.bincount(K_cal.astype(int))
    tail = np.cumsum(counts[::-1])[::-1]          # tail[k] = #{K >= k}
    for k in range(len(counts) + 1):
        ge = tail[k] if k < len(tail) else 0
        if (1 + ge) / (n + 1) <= a:
            return k
    return int(K_cal.max()) + 1


def min_cal_windows(a: float) -> int:
    """Calibration windows needed before any threshold can meet budget a: (n + 1) * a >= 1."""
    return int(np.ceil(1.0 / a - 1.0))


# --------------------------------------------------------------------------- windows
def sample_windows(groups: dict, W: int, n_windows: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Subsampled windows: `groups` maps host -> array of row ids. Hosts are drawn proportional to their
    number of rows (only hosts with >= W rows); each window draws W distinct rows of one host.
    Windows may overlap (subsampling), so guarantees built on them are approximate (disclosed).
    Returns (windows, host per window)."""
    hosts = [h for h, ix in groups.items() if len(ix) >= W]
    if not hosts:
        return np.empty((0, W), dtype=int), np.array([], dtype=object)
    sizes = np.array([len(groups[h]) for h in hosts], dtype=float)
    pick = rng.choice(len(hosts), size=n_windows, p=sizes / sizes.sum())
    out = np.empty((n_windows, W), dtype=int)
    for i, h in enumerate(pick):
        out[i] = rng.choice(groups[hosts[h]], W, replace=False)
    return out, np.array([hosts[h] for h in pick], dtype=object)


def disjoint_windows(groups: dict, W: int, rng) -> tuple[np.ndarray, np.ndarray]:
    """Non-overlapping random windows per host (remainder dropped). Returns (windows, host per window)."""
    wins, hs = [], []
    for h, ix in groups.items():
        perm = rng.permutation(ix)
        for j in range(len(perm) // W):
            wins.append(perm[j * W:(j + 1) * W]); hs.append(h)
    if not wins:
        return np.empty((0, W), dtype=int), np.array([], dtype=object)
    return np.vstack(wins), np.array(hs, dtype=object)


def mixed_windows(attack_ix: np.ndarray, benign_ix: np.ndarray, W: int, rho: float, n_windows: int, rng) -> np.ndarray:
    """Windows of a host whose traffic is a share rho of attack flows and 1 - rho benign flows."""
    na = int(round(rho * W))
    out = np.empty((n_windows, W), dtype=int)
    for i in range(n_windows):
        out[i] = np.r_[rng.choice(attack_ix, na, replace=False), rng.choice(benign_ix, W - na, replace=False)]
    return out


def counts(flag: np.ndarray, windows: np.ndarray) -> np.ndarray:
    """K per window: number of flagged flows (flag = p <= alpha + beta)."""
    if len(windows) == 0:
        return np.array([], dtype=int)
    return flag[windows].sum(axis=1)


# --------------------------------------------------------------------------- raw rows -> model vectors
def map_rows(df: pd.DataFrame, prepared: dict, cfg: Config, splits=("benign_val", "benign_test", "dev_test", "heldout_test")) -> pd.DataFrame:
    """Map every raw row to the model vector (split, position) it became after de-duplication, using the
    fitted preprocessor. Rows whose vector is in another split (e.g. benign_train) are left unmapped.
    Returns columns: host, type, split, pos."""
    from .data import _row_hashes
    pre = prepared["preprocessor"]
    h_all = _row_hashes(pre.transform(df))
    look = {}
    for sp in splits:
        hs = _row_hashes(prepared["X"][sp])
        for i, (h, t) in enumerate(zip(hs, prepared["types"][sp])):
            look.setdefault((h, t), (sp, i))
    types = df["type"].astype(str).to_numpy()          # load_raw already normalised the class column
    hit = [look.get((h, t)) for h, t in zip(h_all, types)]
    return pd.DataFrame({"host": df[cfg.host_column].astype(str).to_numpy(), "type": types,
                         "split": [x[0] if x else None for x in hit],
                         "pos": np.array([x[1] if x else -1 for x in hit], dtype=int)})


def row_values(rows: pd.DataFrame, per_split: dict) -> np.ndarray:
    """Give every mapped row the value (p-value, flag, ...) of its model vector."""
    out = np.full(len(rows), np.nan)
    for sp, v in per_split.items():
        m = (rows["split"] == sp).to_numpy()
        out[m] = np.asarray(v, dtype=float)[rows.loc[m, "pos"].to_numpy()]
    return out


def host_groups(rows: pd.DataFrame, mask: np.ndarray) -> dict:
    """host -> array of row ids (positions in `rows`) for the rows selected by mask."""
    sub = rows[mask]
    return {h: g.index.to_numpy() for h, g in sub.groupby("host")}
