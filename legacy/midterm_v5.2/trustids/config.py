"""Experiment configuration for TrustFed-TinyIDS.

Every notebook loads the same configuration, so splits, seeds and budgets are
identical across phases. Change values here (or in configs/default.json), never
inside individual notebooks.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Config:
    # ---- dataset (TON_IoT by default; see configs/edge_iiotset.json for the replication) ----
    dataset_name: str = "TON_IoT_network"
    type_column: str = "type"          # column holding the class name (normal / attack family)
    normal_value: str = "normal"       # value of type_column for benign traffic (case-insensitive)

    # ---- paths -----------------------------------------------------------
    project_dir: str = "/content/drive/MyDrive/TrustFed-TinyIDS"
    data_file: str = "data/train_test_network.csv"
    artifacts_dir: str = "artifacts"
    figures_dir: str = "figures"
    runs_dir: str = "runs"

    # ---- reproducibility ---------------------------------------------------
    split_seed: int = 2027
    train_seeds: list = field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    # ---- attack roles (pre-registered; do not change after seeing results) ----
    dev_families: list = field(default_factory=lambda: [
        "backdoor", "ddos", "dos", "injection", "password", "scanning"])
    heldout_families: list = field(default_factory=lambda: ["ransomware", "xss", "mitm"])
    normal_label: str = "normal"

    # ---- splits ------------------------------------------------------------
    benign_split: dict = field(default_factory=lambda: {
        "train": 0.50, "val": 0.10, "cal": 0.20, "test": 0.20})
    dev_attack_val_fraction: float = 0.50

    # ---- features ----------------------------------------------------------
    drop_columns: list = field(default_factory=lambda: [
        "ts", "src_ip", "dst_ip", "src_port", "dst_port",
        "dns_query", "ssl_subject", "ssl_issuer", "http_uri", "http_referrer",
        "http_user_agent", "http_orig_mime_types", "http_resp_mime_types",
        "weird_name", "weird_addl", "label", "type"])
    # identifier columns re-admitted only in the leakage check (dataset-specific)
    leakage_columns: list = field(default_factory=lambda: ["ts", "src_ip", "dst_ip", "src_port", "dst_port"])
    # flow counters an IoT device can compute itself (no deep packet inspection);
    # used for the 'device' feature set (professor's Phase 1 requirement)
    device_feature_columns: list = field(default_factory=lambda: [
        "proto", "duration", "src_bytes", "dst_bytes", "conn_state", "missed_bytes",
        "src_pkts", "src_ip_bytes", "dst_pkts", "dst_ip_bytes"])
    max_categorical_cardinality: int = 30
    correlation_threshold: float = 0.98

    # ---- models ------------------------------------------------------------
    ae_variants: dict = field(default_factory=lambda: {
        "ae_32_16_8": {"hidden": [32, 16, 8], "dropout": 0.0},
        "ae_16_8_4": {"hidden": [16, 8, 4], "dropout": 0.0},
        "ae_32_16_8_do": {"hidden": [32, 16, 8], "dropout": 0.1},
    })
    ae_default: str = "ae_32_16_8"
    epochs: int = 1500          # cap; the convergence rule below normally stops earlier
    batch_size: int = 512
    learning_rate: float = 1e-3
    patience: int = 40
    conv_window: int = 50        # pre-registered convergence rule: stop when best val loss
    conv_rel_tol: float = 0.005  #   improves < 0.5% over 50 epochs (constant learning rate)
    iforest_estimators: int = 200

    # ---- trust-aware decision (pre-registered budgets) ----------------------
    alpha: float = 0.01
    beta: float = 0.04
    alpha_grid: list = field(default_factory=lambda: [0.005, 0.01, 0.02, 0.05])
    beta_grid: list = field(default_factory=lambda: [0.01, 0.02, 0.04, 0.08])
    heuristic_k: list = field(default_factory=lambda: [2.0, 3.0])

    # ---- evaluation ----------------------------------------------------------
    validity_resplits: int = 200
    prevalence_grid: list = field(default_factory=lambda: [0.001, 0.01, 0.1])
    random_control_repeats: int = 50
    bootstrap_repeats: int = 1000
    pvalue_bins: list = field(default_factory=lambda: [0, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0])

    # ---- UNCERTAIN resolution (proposal v6, §7a; pre-registered before the confirmatory runs) ----
    host_column: str = "src_ip"          # grouping key only, never a model feature
    resolution_windows: list = field(default_factory=lambda: [20, 50, 100])        # W: flows per host window
    resolution_flows_per_day: list = field(default_factory=lambda: [1000, 5000])   # F: device traffic levels
    resolution_budget_per_week: float = 1.0   # B: false host escalations per device per week
    resolution_cal_windows: int = 5000        # subsampled benign_val windows used to calibrate k*
    resolution_eval_windows: int = 5000       # subsampled benign_test windows used to estimate the rate
    resolution_rho: list = field(default_factory=lambda: [0.10, 0.25, 0.50, 1.00])  # attack share in a host window

    # ---- helpers -------------------------------------------------------------
    @property
    def project(self) -> Path:
        return Path(self.project_dir)

    @property
    def data_path(self) -> Path:
        return self.project / self.data_file

    @property
    def artifacts(self) -> Path:
        p = self.project / self.artifacts_dir
        p.mkdir(parents=True, exist_ok=True)
        return p

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        return cls(**json.loads(Path(path).read_text(encoding="utf-8")))

    def check(self) -> None:
        """Fail early on inconsistent settings."""
        overlap = set(self.dev_families) & set(self.heldout_families)
        assert not overlap, f"Families cannot be both dev and held-out: {overlap}"
        assert abs(sum(self.benign_split.values()) - 1.0) < 1e-9, "Benign split must sum to 1"
        assert 0 < self.alpha < 1 and 0 < self.beta < 1 and self.alpha + self.beta < 1
        assert self.ae_default in self.ae_variants
