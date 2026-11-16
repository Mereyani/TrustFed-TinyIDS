# TrustFed-TinyIDS

**A trust-aware, uncertainty-calibrated intrusion detection framework for IoT.**

The framework detects unseen attacks on IoT networks with an autoencoder trained on benign traffic only. It comes with conformal false-alarm control, federated training, an INT8 TinyML deployment path, and host-level evidence accumulation for sparse attacks (Phase 10).

> **Status.** This is research code accompanying an MSc project at Siirt University (2026) and a journal manuscript in preparation. All host-level experiments are **simulations** on a dataset without timestamps. Nothing in this repository has been validated in a real deployment.

## What the framework does

1. **Benign-only detector.** A 53-32-16-8 autoencoder (4,829 parameters) is trained on benign TON_IoT flows only. A 21-feature device variant has 2,749 parameters.
2. **Conformal three-way decision.** Each flow receives a conformal p-value against held-out benign calibration scores:
   - **ANOMALY** if p ≤ α (α = 0.01);
   - **UNCERTAIN** if α < p ≤ α + β (β = 0.04);
   - **NORMAL** otherwise.

   The false-alarm guarantee holds for benign traffic that is exchangeable with the calibration data. **Nothing is guaranteed about attacks.**
3. **UNCERTAIN is never a dead end.** Flows in the UNCERTAIN band are resolved at host level. An optional supervised gateway is reported as a baseline.
4. **Federated learning** with FedAvg and FedProx under IID and Dirichlet non-IID splits. The analysis covers why the federated model can lag behind the central one, and global versus per-client calibration.
5. **TinyML.** INT8 TFLite conversion, a study of which conformal thresholds survive quantisation, input corruption and ablations.
6. **Phase 10: host-level evidence accumulation.** Flow p-values are turned into likelihood-ratio e-values and accumulated per host:
   - with window sums, CUSUM, Shiryaev–Roberts, evidence decay and adaptive mixtures;
   - with optional host-conditional (Mondrian) p-values;
   - all calibrated to the same operational budget of 1 false escalation per host per week.

## Repository layout

```
trustids/                 Python package (data, models, conformal, FL, TinyML, LOFO, sparse, phase10)
notebooks/                Colab notebooks 00–04b (phases 1–4) and F1–F5 (phases 5–9 and the final analyses)
experiments/phase10/      Phase 10 runner, selection, analysis, overhead benchmark, protocol and all results
results/colab_runs/       Outputs of every Colab run (CSV/JSON/figures, environment.json, config_used.json)
results/executed_notebooks/  The 11 notebooks with their outputs
results/artifacts/        Models, per-seed scores, raw per-seed results, host map (no dataset features)
results/analysis_extra/   Extra analyses (validation-loss histories of the federated runs)
tests/                    Unit tests (conformal rule, host counter, Phase 10)
tools/                    Notebook builder, smoke test, packaging script
docs/manuscript/          English manuscript (Word) and the verified reference list
docs/previous_versions/   Earlier course report (Turkish) and its value extractor
legacy/midterm_v5.2/      Code of the earlier midterm version (phases 1–4), kept for provenance
```

## Installation

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

- **Phases 1–9** need TensorFlow. They were run on Google Colab (TF 2.21.0, Tesla T4).
- **Phase 10** needs only NumPy, pandas, SciPy, numba and matplotlib, and runs on a CPU.

## Quick start

- **Phase 10, from the saved scores.** No dataset is needed. See `REPRODUCIBILITY.md` for the full commands.

  ```bash
  python -I experiments/phase10/run_phase10.py --stage test --seeds 0 --rho0 0.01 --F 1000 --tag demo
  ```

- **Phases 1–9.** Obtain the TON_IoT `train_test_network.csv` (see `DATA_AVAILABILITY.md`), then run the notebooks in order on Colab.

## Main results

The tables and figures are in `docs/manuscript/` and `experiments/phase10/results/`. A short summary, with the numbers as reported in the manuscript, is in `RESULTS_SUMMARY.md`.

## Documentation

- `CHANGELOG.md`: version history from the midterm version to Phase 10.
- `REPRODUCIBILITY.md`: environments, seeds and commands.
- `DATA_AVAILABILITY.md`: the dataset and what is or is not included.
- `experiments/phase10/PROTOCOL_PHASE10.md`: the pre-specified Phase 10 protocol and its deviations.
- `docs/manuscript/references/`: the reference list, each entry checked against Crossref, OpenAlex, arXiv or the publisher.
- `docs/manuscript/en/`: the scripts that generated the manuscript, from `p10_values.json` and the earlier `values.json`. They are included for transparency and were run in the original project layout, where the reference list and `values.json` sit two folders up. To rebuild, adjust the paths at the top of `_head_en.js`.
- `SCIENTIFIC_ASSESSMENT.md`: a critical assessment of the Phase 10 results and of how ready the manuscript is.

## Citation

If you use this code, please cite the manuscript once it is published. Until then, cite this repository and its author: Mohamed Mereyani, Siirt University.

## License

No license file has been chosen yet. Until the author adds one, all rights are reserved by default.
