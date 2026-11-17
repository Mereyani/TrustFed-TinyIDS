"""Map raw TON_IoT rows to host and model vector for a prepared bundle (used for the 21-feature device model).
Validation: the same procedure applied to the 53-feature bundle must reproduce the stored Colab map exactly.
Usage: python -I phase10/build_device_host_map.py"""
import sys, warnings, time
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
FA = HERE.parent
sys.path.insert(0, str(FA / "TrustFed-TinyIDS-Final"))
warnings.filterwarnings("ignore")
from trustids.config import Config
from trustids import data as D, resolution as R
ART = FA / "colab_sonuclari" / "artifacts"
cfg = Config.load(FA / "colab_sonuclari" / "20261111-064904_final_F5_seyrek_saldiri" / "config_used.json")
cfg.project_dir = str(FA / "TrustFed-TinyIDS-Final")
raw = D.load_raw(cfg.data_path, cfg)
sys.stdout.reconfigure(encoding="utf-8")
for name, out in [("prepared", HERE / "results" / "host_rows_53_rebuilt.csv.gz"),
                  ("prepared_device", HERE / "results" / "host_rows_device.csv.gz")]:
    t = time.time()
    P = D.load_prepared(ART / name)
    rows = R.map_rows(raw, P, cfg)
    rows.to_csv(out, index=False)
    print(name, rows.shape, rows["split"].value_counts(dropna=False).to_dict(), f"{time.time()-t:.0f}s", flush=True)
ref = pd.read_csv(ART / "resolution" / "host_rows.csv.gz", keep_default_na=False)
new = pd.read_csv(HERE / "results" / "host_rows_53_rebuilt.csv.gz", keep_default_na=False)
same = (ref.astype(str).values == new.astype(str).values).all()
print("53-feature rebuilt map identical to the stored Colab map:", bool(same))

# ---- de-duplicated (vector-level) host map for the 53-feature model: one row per distinct vector,
#      host = host of the vector's representative raw row (prepared idx_*), multiplicity ignored.
P = D.load_prepared(ART / "prepared")
parts = []
for sp in ["benign_val", "benign_test", "dev_test", "heldout_test"]:
    idx = P["index"][sp]
    sub = raw.loc[idx]
    assert (sub["type"].astype(str).to_numpy() == np.asarray(P["types"][sp]).astype(str)).all(), sp
    parts.append(pd.DataFrame({"host": sub[cfg.host_column].astype(str).to_numpy(), "type": sub["type"].astype(str).to_numpy(),
                               "split": sp, "pos": np.arange(len(idx))}))
vec = pd.concat(parts, ignore_index=True)
vec.to_csv(HERE / "results" / "host_rows_dedup.csv.gz", index=False)
print("dedup vector map", vec.shape, vec["split"].value_counts().to_dict())
