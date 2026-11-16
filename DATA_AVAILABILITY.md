# Data availability

## Dataset

All experiments use the **TON_IoT network dataset**, specifically the "train_test_network" file (`train_test_network.csv`), which is the version without timestamps (version B). It was released by the UNSW Canberra Cyber Range and IoT Labs:

- N. Moustafa, "A new distributed architecture for evaluating AI-based security systems at the edge: Network TON_IoT datasets," *Sustainable Cities and Society*, vol. 72, 102994, 2021. doi:10.1016/j.scs.2021.102994

**The dataset is not included in this repository.** It is distributed by its authors under their own terms.

**How to obtain it.** Download `train_test_network.csv` from the official TON_IoT page of UNSW, then place it at:

- `data/train_test_network.csv` (for local runs);
- `MyDrive/TrustFed-TinyIDS-Final/data/train_test_network.csv` (for the Colab notebooks).

**Checking the file.** `results/artifacts/data_file_info.json` records the file used in every reported run, so a downloaded copy can be checked before use. That file is version B, with 211,043 rows and 44 columns, and its SHA-256 is `26ddc513552de36de6428b2e578efaed2b57504c716dfba847cc0109a64e1974`.

## What the repository does contain

Every number in the reports and the manuscript can be traced to the files below.

- `results/colab_runs/` holds the output folder of every notebook run on Google Colab (Tesla T4). Each folder contains:
  - the CSV and JSON outputs and the figures;
  - `environment.json`;
  - `config_used.json`.
- `results/executed_notebooks/` holds the 11 notebooks together with their outputs.
- `results/artifacts/` holds:
  - trained models (Keras and TFLite FP32/INT8);
  - per-seed anomaly scores of every split (`scores/seed*.npz`, `scores/device_seed*.npz`);
  - per-seed raw results and per-round validation losses;
  - the flow-to-host map (`resolution/host_rows.csv.gz`);
  - the preprocessing reports.

  The feature matrices derived from the dataset (`prepared*.npz`) are **not** included, because they would amount to redistributing the dataset. The notebooks regenerate them from the CSV. Phase 10 needs only the labels and multiplicities of the dev_val split, and these are provided in `results/artifacts/prepared/dev_val_meta.npz`.
- `experiments/phase10/results/` holds every Phase 10 output: the validation and test runs, the selection file, the analysis tables, figures and overhead measurements.

## Reproducing Phase 10 without the dataset

The Phase 10 experiments use only the saved anomaly scores and the host map. They can therefore be rerun from this repository alone (see `REPRODUCIBILITY.md`). Reproducing phases 1–9 requires the dataset and, for the reported timings, a GPU runtime such as Colab.

## Note on host identifiers

`host_rows.csv.gz` contains the source IP addresses that appear in TON_IoT. These are addresses of the dataset's testbed network, not personal data collected by this project.
