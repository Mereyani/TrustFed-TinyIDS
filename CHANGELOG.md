# Changelog

Each version keeps the outputs of the earlier versions; nothing was overwritten. Dates are the dates of the runs.

## [Manuscript v4] 2026-11-17

### Changed
- **Repositioned as an empirical reliability and benchmarking study.** The title is *Reliability of Calibrated IoT Intrusion Detection under Federated Training, Quantization, and Host-Level Aggregation: An Empirical Study*.
- **New main text (`docs/manuscript/v4/`), about 19 pages.**
  - Rewritten: abstract, introduction, research questions and contributions.
  - A Study Design section separates marginal conformal validity from operational false-alarm budgets.
  - Results are organised by reliability dimension: nominal, federated training, quantisation and corruption, host-level aggregation.
  - New sections: a synthesis table of when and why calibration became unreliable, threats to validity, and the conclusion.
  - A related-work section on empirical NIDS reliability studies (16 new references, all verified).
- **Supplementary Material (new file).** It contains the complete detailed description, the formulation of every host-level rule and every detailed table and figure from the earlier comprehensive manuscript (S1–S4). No result was deleted.

### Unchanged
- Code, raw results and protocols. No new experiment was run.

### Preserved
- The earlier manuscripts are in `docs/manuscript/previous_versions/` (v2, v3).

## [Phase 10b] 2026-11-17

### Added
- `experiments/phase10/PROTOCOL_PHASE10B.md`: a confirmatory protocol, written before any Phase 10b run. It contains:
  - the frozen rules;
  - four settings: MAIN, SWAP, DEVICE, DEDUP;
  - pre-specified success criteria.
- `run_phase10b.py`, `analyze_phase10b.py`, `make_p10b_values.py`.
- `build_device_host_map.py`:
  - rebuilds the row-to-host map locally (it is checked to reproduce the stored Colab map exactly);
  - builds the 21-feature device-model map and the de-duplicated vector map.
- `experiments/phase10/results_10b/`: raw per-seed results for 40 runs, and the analysis.
- `docs/manuscript/previous_versions/`: the manuscript as it was before Phase 10b.

### Changed
- **Manuscript**
  - Proposition 1 and Proposition 2 now state their assumptions exactly and limit themselves to marginal, per-flow validity. No guarantee is claimed for windows, CUSUM, Shiryaev–Roberts or calibration transfer.
  - New Sections 5.7 and 6.13 report Phase 10b.
  - The abstract, contributions, Discussion 7.2, Section 8 and Section 9 are rewritten. The outdated future-work list is replaced.
- **Withdrawn:** the Phase 10 matched-cost diagnostic (`tradeoff_phase10.py`), because it set thresholds on test data. Its files are kept and marked as withdrawn.

### Outcome
- The host-conditional counter's advantage was reproduced on the original split only (MAIN). It was not reproduced in SWAP, DEVICE or DEDUP, so the pre-specified overall verdict is **"not reproduced"**.
- In SWAP and DEVICE every rule exceeded the false-escalation budget several-fold.

## [Phase 10] 2026-11-16

### Added
- **`trustids/phase10.py`: host-level evidence accumulation.**
  - **Evidence:** binned likelihood-ratio e-values for a sparse-mixture alternative, fitted on known-family dev_val p-values (held-out families are never used), and the Vovk–Wang mixture calibrator.
  - **Window rules:** e-value sum, Fisher, truncated product, min-p and Higher Criticism.
  - **Sequential rules:** e-CUSUM, e-Shiryaev–Roberts, leaky e-CUSUM, adaptive e-SR, Bernoulli CUSUM and EWMA charts. They are numba kernels.
  - **Calibration helpers.**
- **`experiments/phase10/`**
  - a runner with a validation stage (selection) and a test stage (frozen);
  - the pre-specified protocol (`PROTOCOL_PHASE10.md`), the selection script, the analysis script (Wilcoxon with Holm correction, bootstrap CIs, figures) and an overhead benchmark.
- **Host-conditional (Mondrian) p-values,** p′ = max(p_pooled, p_host). They are cross-fitted on benign_val, and low-traffic hosts share one fallback reference.
- **`tests/test_phase10.py`:** e-value validity, isotonic monotonicity, equivalence with the existing count threshold, and kernels against plain-Python references.
- **English manuscript** (`docs/manuscript/`), the verified reference list, and the repository documents (README, CHANGELOG, REPRODUCIBILITY, DATA_AVAILABILITY, RESULTS_SUMMARY).
- **Post-test analyses,** labelled exploratory:
  - `host_heterogeneity.py`;
  - `analyze_extra_phase10.py` (the host-conditional counter);
  - `tradeoff_phase10.py`, a matched-cost diagnostic whose thresholds are tuned on benign_test, so it is an oracle and not deployable.

### Outcome
- The pre-specified P10 configuration improved detection but exceeded the false-escalation budget on benign_test. The primary hypothesis is not supported.
- See `RESULTS_SUMMARY.md` and the protocol's section 9.

### Unchanged
- The autoencoder, the conformal calibration, α = 0.01, β = 0.04, federated training and TinyML conversion. Phase 10 reuses the saved per-seed scores and retrains nothing.

### Fixed during Phase 10 (before the test stage; see the protocol's Deviations section)
- **Sequential threshold calibration.** It now counts alarms with restart instead of using a first-passage estimate that assumed homogeneous hosts.
- **Two degenerate cases in threshold and bin construction.** These cases do not occur with the real data.

## [Final, phases 5–9] 2026-11-10 to 2026-11-12

All runs were on Google Colab, Tesla T4, TensorFlow 2.21.0.

### Notebooks
- **F1:** diagnosis of the gap between the federated and the central model (seed 0).
- **F2:** leave-one-family-out, pre-registered, seeds 10–19.
- **F3:** phases 5–9 with 10 seeds.
  - **FL:** four FedAvg/FedProx protocols, IID and Dirichlet 1.0/0.1, pooled versus per-client calibration, local-only models.
  - **TinyML:** INT8 TFLite with three threshold rules.
  - **Robustness:** noise, missing and corrupted features.
  - **Ablations** and **risk–coverage** for all models.
- **F4:** the 21-feature device model through the same pipeline.
- **F5:** the existing host counter under sparse attacks (simulation, exploratory).

### Analysis and fixes
- `tools/val_hist_analizi.py`: shows that every federated run stopped at the 1,500-epoch cap was still improving.
- Fixed: float64 FedAvg weight averaging.

### Report
- The Turkish course report (`docs/previous_versions/final_report_tr/`).

## [Midterm v5.2] 2026-11-04

### Phases 1–4
- data preparation and leakage removal;
- benign-only autoencoder and Isolation Forest;
- the conformal three-way decision and its guarantee test;
- risk–coverage;
- resolution of UNCERTAIN with a per-host counter and a supervised gateway baseline.

### Code
- The `legacy/midterm_v5.2/` package uses a constant learning rate and a plateau stopping rule.
- Phases 1–4 were also rerun on Colab as part of the final runs (`results/colab_runs/*_midterm_phase4*`).
