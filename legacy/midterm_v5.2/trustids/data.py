"""Phase 1: TON_IoT network data loading, audit, de-duplication, splits and preprocessing.

Rules enforced here (proposal v4, §3):
* identifier / leakage columns are never model features;
* de-duplication is GLOBAL and happens BEFORE the final random split, so benign cal and test
  stay exchangeable (committee round 3, R3-N5):
    1. exact duplicates on the input feature columns are merged (row multiplicity is kept);
    2. a frozen preprocessor (fit on a provisional benign split) defines the model feature
       vector; rows with identical vectors are merged globally;
    3. a vector seen with both benign and attack labels keeps ONE benign copy and ONE attack copy
       (the attack copy is flagged as a collision). Dropping the benign copy would let attack labels,
       including held-out ones, shape the benign data (round-4 R1-N4). Recall is reported as is,
       excluding collisions, and with collisions counted as missed (primary pessimistic view);
* the final split is random; every fitted transform is then re-fit on benign-train only;
* held-out attack families never enter any split other than the final test.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder

from .config import Config

SPLITS = ["benign_train", "benign_val", "benign_cal", "benign_test", "dev_val", "dev_test", "heldout_test"]


# --------------------------------------------------------------------------- loading
def load_raw(path, cfg: Config | None = None) -> pd.DataFrame:
    """Load a flow CSV and normalise the class column to 'type' with benign = 'normal'.

    TON_IoT works with the defaults. Other datasets (e.g. Edge-IIoTset, column 'Attack_type',
    benign value 'Normal') are handled through cfg.type_column / cfg.normal_value.
    """
    # utf-8-sig removes a byte-order mark; the Hugging Face mirror's first column is '﻿src_ip',
    # which would otherwise escape the leakage-column drop list
    df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    df.columns = [c.strip().lstrip("﻿") for c in df.columns]
    tcol = cfg.type_column if cfg is not None else "type"
    normal = (cfg.normal_value if cfg is not None else "normal").strip().lower()
    if tcol not in df.columns:
        raise ValueError(f"Class column '{tcol}' not found. Set cfg.type_column for this dataset.")
    t = df[tcol].astype(str).str.strip().str.lower()
    if tcol != "type":
        df = df.drop(columns=[c for c in [tcol, "type"] if c in df.columns])
    df["type"] = t.replace({normal: "normal"}).to_numpy()
    return df.reset_index(drop=True)


def detect_version(df: pd.DataFrame) -> dict:
    n = len(df)
    if "ts" in df.columns and abs(n - 461_043) < 1000:
        version = "A (461,043 rows, with ts)"
    elif "ts" not in df.columns and abs(n - 211_043) < 1000:
        version = "B (211,043 rows, no ts)"
    else:
        version = "unknown: document it in the report"
    return {"version": version, "rows": n, "columns": len(df.columns), "has_ts": "ts" in df.columns}


def audit(df: pd.DataFrame) -> dict:
    out = {"class_counts": df["type"].value_counts().to_dict()}
    if "label" in df.columns:
        lab = pd.to_numeric(df["label"], errors="coerce")
        out["label_type_mismatch"] = int(((lab == 0) != (df["type"] == "normal")).sum())
    obj = df.select_dtypes(include=["object", "string"])
    out["dash_missing_per_column"] = {c: int((obj[c] == "-").sum()) for c in obj.columns if (obj[c] == "-").any()}
    out["exact_duplicate_rows"] = int(df.duplicated().sum())
    return out


# --------------------------------------------------------------------------- columns
def feature_columns(df: pd.DataFrame, cfg: Config, include_leakage: bool = False,
                    feature_set: str = "all") -> list:
    """'all' = every non-identifier column; 'device' = flow counters an IoT device can compute
    itself without deep packet inspection (professor's Phase 1 requirement)."""
    if feature_set == "device":
        return [c for c in cfg.device_feature_columns if c in df.columns]
    drop = set(cfg.drop_columns) | {"label", "type"}
    if include_leakage:
        drop -= set(cfg.leakage_columns)
    return [c for c in df.columns if c not in drop]


def _as_numeric(s: pd.Series) -> pd.Series | None:
    """Return the numeric version of a column if >= 99% of its non-missing values parse."""
    if pd.api.types.is_numeric_dtype(s):
        return s
    clean = s.replace("-", np.nan)
    num = pd.to_numeric(clean, errors="coerce")
    nonmissing = clean.notna().sum()
    if nonmissing == 0 or num.notna().sum() / nonmissing >= 0.99:
        return num
    return None


# --------------------------------------------------------------------------- splits
def make_splits(df: pd.DataFrame, cfg: Config, seed: int | None = None) -> dict:
    """Return {split_name: np.ndarray of df index labels}. Random and deterministic given the seed."""
    cfg.check()
    rng = np.random.default_rng(cfg.split_seed if seed is None else seed)
    present = set(df["type"].unique())
    missing = (set(cfg.dev_families) | set(cfg.heldout_families)) - present
    if missing:
        raise ValueError(f"Families not found in data: {missing}")
    unassigned = present - set(cfg.dev_families) - set(cfg.heldout_families) - {cfg.normal_label}
    if unassigned:
        raise ValueError(f"Families with no role in the config: {unassigned}")

    splits = {}
    benign = rng.permutation(df.index[df["type"] == cfg.normal_label].to_numpy())
    fr = cfg.benign_split
    cuts = np.cumsum([int(round(fr[k] * len(benign))) for k in ["train", "val", "cal"]])
    splits["benign_train"], splits["benign_val"], splits["benign_cal"], splits["benign_test"] = np.split(benign, cuts)
    dev_val, dev_test = [], []
    for fam in cfg.dev_families:
        idx = rng.permutation(df.index[df["type"] == fam].to_numpy())
        k = int(round(cfg.dev_attack_val_fraction * len(idx)))
        dev_val.append(idx[:k])
        dev_test.append(idx[k:])
    splits["dev_val"] = np.concatenate(dev_val)
    splits["dev_test"] = np.concatenate(dev_test)
    splits["heldout_test"] = df.index[df["type"].isin(cfg.heldout_families)].to_numpy()
    return splits


# --------------------------------------------------------------------------- preprocessing
@dataclass
class Preprocessor:
    """Fit on benign-train only. Numeric: signed log1p then MinMax. Categorical: one-hot."""
    max_card: int = 30
    corr_threshold: float = 0.98
    numeric_cols_: list = field(default_factory=list)
    categorical_cols_: list = field(default_factory=list)
    dropped_cols_: dict = field(default_factory=dict)
    medians_: dict = field(default_factory=dict)
    encoder_: OneHotEncoder | None = None
    scaler_: MinMaxScaler | None = None
    keep_mask_: np.ndarray | None = None
    feature_names_: list = field(default_factory=list)
    groups_: dict = field(default_factory=dict)

    def fit(self, df_train: pd.DataFrame, cols: list) -> "Preprocessor":
        num, cat = {}, []
        for c in cols:
            s = _as_numeric(df_train[c])
            if s is not None:
                num[c] = s
            else:
                cat.append(c)
        self.numeric_cols_ = list(num.keys())
        self.medians_ = pd.DataFrame(num, index=df_train.index).median().fillna(0).to_dict()
        self.categorical_cols_, self.dropped_cols_ = [], {}
        for c in cat:
            card = df_train[c].replace("-", np.nan).nunique(dropna=True)
            if card <= self.max_card:
                self.categorical_cols_.append(c)
            else:
                self.dropped_cols_[c] = f"cardinality {card} > {self.max_card}"
        self.encoder_ = None
        if self.categorical_cols_:
            self.encoder_ = OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.float32)
            self.encoder_.fit(self._cat_frame(df_train))
        raw = self._raw_matrix(df_train)
        self.scaler_ = MinMaxScaler().fit(raw)
        z = self.scaler_.transform(raw)
        names = self._raw_names()
        keep = z.std(axis=0) > 1e-8
        for i in np.where(~keep)[0]:
            self.dropped_cols_[names[i]] = "zero variance on benign-train"
        kept_idx = np.where(keep)[0]
        if len(kept_idx) > 1:
            corr = np.corrcoef(z[:, kept_idx], rowvar=False)
            drop_corr = set()
            for a in range(len(kept_idx)):
                if a in drop_corr:
                    continue
                for b in range(a + 1, len(kept_idx)):
                    if b not in drop_corr and abs(corr[a, b]) > self.corr_threshold:
                        drop_corr.add(b)
                        self.dropped_cols_[names[kept_idx[b]]] = f"|corr|>{self.corr_threshold} with {names[kept_idx[a]]}"
            for b in drop_corr:
                keep[kept_idx[b]] = False
        self.keep_mask_ = keep
        self.feature_names_ = [n for n, k in zip(names, keep) if k]
        self.groups_ = {}
        for j, n in enumerate(self.feature_names_):
            self.groups_.setdefault(n.split("=", 1)[0], []).append(j)
        return self

    def _cat_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[self.categorical_cols_].astype(str).replace({"-": "missing", "nan": "missing"})

    def _raw_names(self) -> list:
        names = list(self.numeric_cols_)
        if self.encoder_ is not None:
            for c, cats in zip(self.categorical_cols_, self.encoder_.categories_):
                names += [f"{c}={v}" for v in cats]
        return names

    def _raw_matrix(self, df: pd.DataFrame) -> np.ndarray:
        parts = []
        if self.numeric_cols_:
            # columns typed as numeric at fit time are always coerced value-by-value here; the
            # 99% parse rule is applied only at fit time, never per split (R3-B3)
            num = pd.DataFrame({c: pd.to_numeric(df[c].replace("-", np.nan), errors="coerce")
                                for c in self.numeric_cols_}, index=df.index)
            num = num.astype(float).fillna(self.medians_).to_numpy()
            parts.append(np.sign(num) * np.log1p(np.abs(num)))
        if self.encoder_ is not None:
            parts.append(self.encoder_.transform(self._cat_frame(df)))
        return np.hstack(parts).astype(np.float64)

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        z = self.scaler_.transform(self._raw_matrix(df))
        return z[:, self.keep_mask_].astype(np.float32)

    def save(self, path) -> None:
        joblib.dump(self, path)

    @staticmethod
    def load(path) -> "Preprocessor":
        return joblib.load(path)


# --------------------------------------------------------------------------- global de-duplication
def _row_hashes(X: np.ndarray) -> np.ndarray:
    Xc = np.ascontiguousarray(np.round(X.astype(np.float64), 6))
    return pd.util.hash_array(Xc.view(np.dtype((np.void, Xc.dtype.itemsize * Xc.shape[1]))).ravel())


def global_dedup(df: pd.DataFrame, cols: list, cfg: Config, max_card: int) -> tuple[pd.DataFrame, dict]:
    """Global, split-independent de-duplication (see module docstring)."""
    before = df["type"].value_counts()
    # stage 1: exact duplicates on input columns (+type), keep multiplicity
    key = pd.util.hash_pandas_object(df[cols + ["type"]], index=False)
    mult1 = key.map(key.value_counts())
    d1 = df.loc[~key.duplicated()].copy()
    d1["_mult"] = mult1.loc[d1.index].to_numpy()
    # stage 2: frozen feature vector from a provisional benign split
    prov = make_splits(d1, cfg, seed=cfg.split_seed + 7919)
    frozen = Preprocessor(max_card=max_card, corr_threshold=cfg.correlation_threshold).fit(d1.loc[prov["benign_train"]], cols)
    h = _row_hashes(frozen.transform(d1))
    is_attack = (d1["type"] != cfg.normal_label).to_numpy()
    tab = pd.DataFrame({"h": h, "attack": is_attack, "type": d1["type"].to_numpy(),
                        "mult": d1["_mult"].to_numpy(), "pos": np.arange(len(d1))})
    grp = tab.groupby("h")
    has_benign = ~grp["attack"].transform("all")
    has_attack = grp["attack"].transform("any")
    tab["collision_benign_attack"] = has_benign & has_attack
    n_attack_types = tab[tab["attack"]].groupby("h")["type"].nunique()
    tab["collision_attack_families"] = tab["attack"] & tab["h"].map(n_attack_types).fillna(0).gt(1).to_numpy()
    # one copy is kept PER LABEL (round-4 R1-N4, R4-B7): dropping the benign copy of a benign/attack
    # collision would let attack labels shape the benign data, and keeping only one attack copy
    # could move a held-out vector into a dev family. Multiplicity is summed per (vector, label).
    tab["mult_total"] = tab.groupby(["h", "type"])["mult"].transform("sum")
    keep_pos = np.sort(tab.sort_values(["h", "type", "pos"]).drop_duplicates(["h", "type"])["pos"].to_numpy())
    d2 = d1.iloc[keep_pos].copy()
    kept = tab.set_index("pos").loc[keep_pos]
    d2["_mult"] = kept["mult_total"].to_numpy()
    d2["_collision"] = (kept["collision_benign_attack"] & kept["attack"]).to_numpy()   # flagged on the attack copy
    d2["_collision_family"] = kept["collision_attack_families"].to_numpy()
    after = d2["type"].value_counts()
    stage1 = d1["type"].value_counts()
    report = {
        "rows_before": int(len(df)),
        "after_stage1_exact_input_columns": int(len(d1)),
        "after_stage2_final_vectors": int(len(d2)),
        "benign_attack_collision_vectors": int(d2["_collision"].sum()),
        "attack_family_collision_vectors": int(d2["_collision_family"].sum()),
        "collisions_by_kept_type": d2.loc[d2["_collision"], "type"].value_counts().to_dict(),
        # three levels (committee round 5): rows -> distinct records once identifier columns are
        # removed (stage 1) -> distinct MODEL vectors (stage 2; also merges records that differ
        # only in columns the benign-train filters drop, e.g. dst_ip_bytes ~ dst_bytes)
        "per_type": {t: {"before": int(before.get(t, 0)), "after_stage1": int(stage1.get(t, 0)),
                         "after": int(after.get(t, 0))} for t in before.index},
    }
    return d2, report


# --------------------------------------------------------------------------- end-to-end
def prepare(df: pd.DataFrame, cfg: Config, include_leakage: bool = False, feature_set: str = "all") -> dict:
    """Global de-duplication -> random split -> preprocessor fit on benign-train -> transform."""
    cols = feature_columns(df, cfg, include_leakage=include_leakage, feature_set=feature_set)
    max_card = cfg.max_categorical_cardinality if not include_leakage else 100
    dd, dedup_report = global_dedup(df, cols, cfg, max_card)
    splits = make_splits(dd, cfg)
    pre = Preprocessor(max_card=max_card, corr_threshold=cfg.correlation_threshold).fit(dd.loc[splits["benign_train"]], cols)
    X = {k: pre.transform(dd.loc[v]) for k, v in splits.items()}
    types = {k: dd.loc[v, "type"].to_numpy() for k, v in splits.items()}
    mult = {k: dd.loc[v, "_mult"].to_numpy() for k, v in splits.items()}
    coll = {k: dd.loc[v, "_collision"].to_numpy() for k, v in splits.items()}
    # residual identical vectors across splits after re-fitting (expected ~0; reported, not removed)
    hs = {k: set(_row_hashes(X[k])) for k in SPLITS}
    residual = {f"{a}&{b}": len(hs[a] & hs[b]) for i, a in enumerate(SPLITS) for b in SPLITS[i + 1:] if hs[a] & hs[b]}
    sizes = {k: int(len(v)) for k, v in splits.items()}
    by_type = {k: pd.Series(types[k]).value_counts().to_dict() for k in splits}
    return {"X": X, "types": types, "index": splits, "multiplicity": mult, "collision": coll, "preprocessor": pre,
            "report": {"dedup": dedup_report, "residual_cross_split_identical_vectors": residual,
                       "split_sizes": sizes, "split_by_type": by_type, "feature_set": feature_set,
                       "n_features": len(pre.feature_names_), "dropped_columns": pre.dropped_cols_,
                       "input_columns": cols}}


def calibration_rule(n_cal: int, alpha: float, alpha_grid: list) -> dict:
    """n_cal rule (proposal §3): require (n_cal + 1) * alpha >= 20, else raise alpha."""
    ok = (n_cal + 1) * alpha >= 20
    eff = alpha
    if not ok:
        bigger = [a for a in sorted(alpha_grid) if (n_cal + 1) * a >= 20]
        eff = bigger[0] if bigger else max(alpha_grid)
    return {"n_cal": n_cal, "alpha_requested": alpha, "alpha_effective": eff, "rule_satisfied": ok}


def save_prepared(bundle: dict, out_dir) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "prepared.npz",
                        **{f"X_{k}": v for k, v in bundle["X"].items()},
                        **{f"type_{k}": v.astype(str) for k, v in bundle["types"].items()},
                        **{f"idx_{k}": v for k, v in bundle["index"].items()},
                        **{f"mult_{k}": v for k, v in bundle["multiplicity"].items()},
                        **{f"coll_{k}": v for k, v in bundle["collision"].items()})
    bundle["preprocessor"].save(out / "preprocessor.joblib")


def load_prepared(out_dir) -> dict:
    z = np.load(Path(out_dir) / "prepared.npz", allow_pickle=False)
    return {"X": {k: z[f"X_{k}"] for k in SPLITS}, "types": {k: z[f"type_{k}"] for k in SPLITS},
            "index": {k: z[f"idx_{k}"] for k in SPLITS}, "multiplicity": {k: z[f"mult_{k}"] for k in SPLITS},
            "collision": {k: z[f"coll_{k}"] for k in SPLITS},
            "preprocessor": Preprocessor.load(Path(out_dir) / "preprocessor.joblib")}
