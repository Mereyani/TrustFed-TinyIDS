# Reproducibility

## Environments actually used

| Part | Where it ran | Software |
|---|---|---|
| Phases 1–9 (notebooks `00`–`04b`, `F1`–`F5`) | Google Colab, Tesla T4 GPU | Python 3.13.16, TensorFlow 2.21.0 (see each run's `environment.json`) |
| Phase 10 (`experiments/phase10/`) | Local Windows 11 laptop, CPU only | Python 3.12.1, NumPy 1.26.2, pandas 2.1.4, SciPy 1.11.4, numba, matplotlib 3.8.2 (recorded in each `config_phase10.json`) |
| Midterm version 5.2 (`legacy/midterm_v5.2/`) | Local machine | See `legacy/midterm_v5.2/README.md` |

## Seeds

**Training and evaluation seeds** for phases 2–9 and Phase 10 are 0–9 (`train_seeds` in `config_used.json`). The data split uses a fixed seed: `split_seed` = 2027.

**Leave-one-family-out (F2)** uses seeds 10–19.

**Phase 10 random number streams.** Phase 10 derives every stream from the seed:

| Stream | Value |
|---|---|
| Split of the dev_val likelihood-ratio data | 1,000,000 + seed |
| Simulation streams | 2,000,000 + seed |
| Host-reference folds | 3,000,000 + seed |
| Benign evaluation streams | 90,000 + 1000·seed + F |

## Reproducing phases 1–9

1. Obtain the dataset (see `DATA_AVAILABILITY.md`).
2. Upload `trustids/`, `notebooks/` and `configs/` to `MyDrive/TrustFed-TinyIDS-Final/`. Place the CSV in `data/`.
3. Run the notebooks in this order: `00` → `01` → `02` → `03` → `04` → `04b` → `F1` → `F2` → `F3` → `F4` → `F5`.
   - Every notebook resumes from saved progress if a Colab session ends.
   - Quick mode (`TRUSTIDS_QUICK=1`) is for code testing only.
4. Compare the new outputs with `results/colab_runs/`.
   - Small differences can come from GPU non-determinism and from the TensorFlow version.

## Reproducing Phase 10 (no dataset needed)

```bash
pip install -r requirements.txt
python -I experiments/phase10/run_phase10.py --stage validation --seeds 0-9 --F 1000 \
    --methods W_COUNT_AU,W_EVID,W_HC,W_FISHER,BCUSUM,E_CUSUM,E_SR,E_SR_ADAPT,E_CUSUM_LEAKY
python -I experiments/phase10/select_phase10.py
python -I experiments/phase10/run_phase10.py --stage test --seeds 0-9 --rho0 0.01
python -I experiments/phase10/analyze_phase10.py experiments/phase10/results/<test folders>
python -I experiments/phase10/overhead_phase10.py
```

**What the commands read.** They use `results/artifacts/scores/seed*.npz`, `results/artifacts/resolution/host_rows.csv.gz` and `results/artifacts/prepared/dev_val_meta.npz`.

**What was run for the reported results.** One process per seed (`--seeds k --tag sk`), 10 processes in parallel. The console logs are in `experiments/phase10/logs_console/`.

**Order and selection.** The selection rule and the order of the stages are fixed in `experiments/phase10/PROTOCOL_PHASE10.md`. That file also lists every deviation.

## Checking that the saved scores reproduce the earlier sparse-attack results

`experiments/phase10/check_f5_reproduction.py` reruns the F5 module (`trustids/sparse.py`) on the saved scores for seeds 0–9 and compares the output with the stored F5 per-seed files.

- The largest absolute difference in any numeric column is 5.7e-14.
- The result is saved in `experiments/phase10/results/f5_reproduction_check.csv`.

A rerun of the Phase 10 test stage for seed 0 inside the packaged repository layout (rules W_COUNT_AU and W_EVID, both references, both traffic levels) gave exactly the stored detections.

## Tests

```bash
python -m pytest tests
```

**What the tests cover**
- the conformal three-way rule;
- the host counter;
- the Phase 10 e-values, thresholds and accumulators. These are checked against plain-Python reference implementations.

`tools/smoke_test_final.py` runs every notebook end to end on **synthetic** data. Its numbers have no meaning.
