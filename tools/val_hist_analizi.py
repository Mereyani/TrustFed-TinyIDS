"""Reads val_hist from the F3/F4 FL training files (artifacts/final_f3, final_f4) and measures how much the
best validation loss was still improving when a run stopped. Window = 10 rounds (= 50 epochs, the convergence
rule's window); also over the last 50 rounds. Writes a CSV summary and a figure. Nothing is retrained."""
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ART = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(exist_ok=True)
rows, curves = [], {}
for set_name in ["final_f3", "final_f4"]:
    for f in sorted((ART / set_name).glob("s*_*.json")):
        m = re.match(r"s(\d+)_(IID|Dirichlet1\.0|Dirichlet0\.1)_(orijinal_kucuk_yigin|orijinal|yakinsama_kalici|fedprox_kalici)_", f.name)
        if not m: continue
        d = json.loads(f.read_text(encoding="utf-8")); h = np.asarray(d.get("val_hist") or [], float)
        if len(h) == 0: rows.append({"küme": set_name, "tohum": int(m[1]), "senaryo": m[2], "protokol": m[3], "tur": d["rounds_run"], "durma": d["stopped_by"], "val_hist_yok": True}); continue
        best = np.minimum.accumulate(h); n = len(best)
        rel = lambda k: (best[n - 1 - k] - best[-1]) / best[n - 1 - k] if n > k else np.nan
        rows.append({"küme": "F3 (53)" if set_name == "final_f3" else "F4 (21)", "tohum": int(m[1]), "senaryo": m[2],
                     "protokol": m[3], "tur": n, "durma": d["stopped_by"], "val_loss_en_iyi": best[-1],
                     "son_10_tur_göreli_iyileşme": rel(10), "son_50_tur_göreli_iyileşme": rel(50)})
        curves[(set_name, m[2], m[3], int(m[1]))] = best
R = pd.DataFrame(rows); R.to_csv(OUT / "val_hist_ozet_tum.csv", index=False)
cap = R[R["durma"] == "epoch_cap"]
S = (cap.groupby(["küme", "senaryo", "protokol"])
        .agg(n=("tohum", "count"), son10_ort=("son_10_tur_göreli_iyileşme", "mean"),
             son10_min=("son_10_tur_göreli_iyileşme", "min"), son10_max=("son_10_tur_göreli_iyileşme", "max"),
             son50_ort=("son_50_tur_göreli_iyileşme", "mean"),
             esik_alti=("son_10_tur_göreli_iyileşme", lambda v: int((v < 0.005).sum()))))
S.to_csv(OUT / "val_hist_tavan_ozet.csv"); print(S.round(4).to_string())
fig, axs = plt.subplots(2, 3, figsize=(13, 7), sharex=True)
for i, s in enumerate(["final_f3", "final_f4"]):
    for j, sc in enumerate(["IID", "Dirichlet1.0", "Dirichlet0.1"]):
        ax = axs[i, j]
        for prot, c in [("yakinsama_kalici", "C0"), ("fedprox_kalici", "C3")]:
            for k, (key, b) in enumerate([(k, v) for k, v in curves.items() if k[0] == s and k[1] == sc and k[2] == prot]):
                ax.plot(np.arange(1, len(b) + 1) * 5, b, color=c, lw=0.7, alpha=0.7, label=prot if k == 0 else None)
        ax.set_yscale("log"); ax.set_title(f"{'F3 · 53' if s == 'final_f3' else 'F4 · 21'} öznitelik · {sc}", fontsize=9)
        if i == 1: ax.set_xlabel("epoch eşdeğeri (tur × 5)")
        if j == 0: ax.set_ylabel("en iyi doğrulama kaybı (log)")
axs[0, 0].legend(fontsize=7)
fig.suptitle("FL doğrulama kaybı, 10 tohum (her çizgi bir tohum)"); fig.tight_layout(); fig.savefig(OUT / "val_hist_egrileri.png", dpi=140)
