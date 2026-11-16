"""English figures for the manuscript.
Copy of the figure part of rapor/make_final_values.py with every label translated.
Reads ONLY the Colab output files in colab_sonuclari/ (same inputs, same computations) and writes
manuscript/en/figs/*.png with the same file names. It does not write values.json.
Run:  python -I make_figs_en.py
"""
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]                       # .../Final_Asama
R = ROOT / "colab_sonuclari" / "runs"; A = ROOT / "colab_sonuclari" / "artifacts"
FIG = Path(__file__).resolve().parent / "figs"; FIG.mkdir(parents=True, exist_ok=True)
RUN = {"F1": "20261110-222358_final_F1_fl_teshis", "04": "20261111-042106_midterm_phase4",
       "04b": "20261111-055215_midterm_phase4b_resolution", "F2": "20261111-060847_final_F2_lofo",
       "F5": "20261111-064904_final_F5_seyrek_saldiri", "F3": "20261112-060216_final_F3_asama5_9",
       "F4": "20261112-120717_final_F4_cihaz_modeli"}
rd = lambda k, f, **kw: pd.read_csv(R / RUN[k] / f, **kw)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
SCN = ["IID", "Dirichlet=1.0", "Dirichlet=0.1"]
SCN_LAB = ["IID", "Dirichlet 1.0", "Dirichlet 0.1"]
PROT = ["orijinal", "orijinal_kucuk_yigin", "yakinsama_kalici", "fedprox_kalici"]
PLAB = {"orijinal": "P1 · 40 rounds × 5 epochs, Adam reset", "orijinal_kucuk_yigin": "P2 · equal steps (small batch)",
        "yakinsama_kalici": "P3 · until cap, Adam persistent", "fedprox_kalici": "P4 · FedProx μ = 0.01"}

# ------------------------------------------------------------------ inputs needed by the figures (same code as the source)
curves = {}
for setn, key in [("final_f3", "F3"), ("final_f4", "F4")]:
    for f in sorted((A / setn).glob("s*_*.json")):
        m = re.match(r"s(\d+)_(IID|Dirichlet1\.0|Dirichlet0\.1)_(orijinal_kucuk_yigin|orijinal|yakinsama_kalici|fedprox_kalici)_", f.name)
        if not m: continue
        d = json.loads(f.read_text(encoding="utf-8")); h = np.asarray(d.get("val_hist") or [], float)
        if len(h) == 0: continue
        b = np.minimum.accumulate(h)
        curves[(key, m[2], m[3], int(m[1]))] = b
t5 = rd("F5", "F5_tespit_grup.csv")
P4 = R / RUN["04"]
e3 = pd.read_csv(P4 / "E3_per_family_all_seeds.csv")
E3 = {f: {c: float(g[c].mean()) for c in ["anomaly_rate", "uncertain_rate", "normal_rate"]}
      for f, g in e3.groupby(e3["group"] + "|" + e3["family"])}

# ================================================================== figures
C = {"merk": "#1F3A5F", "orijinal": "#D64545", "orijinal_kucuk_yigin": "#EDA100", "yakinsama_kalici": "#2A78D6", "fedprox_kalici": "#2E9E6B"}
# Fig A: FL vs central, unseen ANOMALY, pooled calibration, 53 and 21 features
fig, axs = plt.subplots(1, 2, figsize=(10, 3.9), sharey=True)
for ax, k, ttl in [(axs[0], "F3", "53 features"), (axs[1], "F4", "21-feature device model")]:
    d = rd(k, f"{k}_fl_tum_tohumlar.csv"); d = d[d.kalibrasyon == "havuz skor"]
    x = np.arange(3); w = 0.16
    for j, (m, lab, col) in enumerate([("Merkezi (yakınsama)", "central", C["merk"])] + [(f"FedAvg · {p}", PLAB[p], C[p]) for p in PROT]):
        vals = [d[(d.senaryo == s) & (d.model == m)]["görülmemiş_ANOMALY"] * 100 for s in SCN]
        xs = x + (j - 2) * w
        ax.bar(xs, [v.mean() for v in vals], w, color=col, label=lab, alpha=0.9)
        for xi, v in zip(xs, vals): ax.plot(np.full(len(v), xi), v, ".", color="black", ms=2.5, alpha=0.6)
    ax.set_xticks(x); ax.set_xticklabels(SCN_LAB); ax.set_title(ttl, fontsize=10)
axs[0].set_ylabel("ANOMALY on unseen attacks (%)")
h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, fontsize=7, frameon=False, ncol=5, loc="lower center")
fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig(FIG / "fl_merkezi.png", dpi=170); plt.close(fig)

# Fig B: val_hist curves (cap-hit protocols)
fig, axs = plt.subplots(1, 2, figsize=(10, 3.4), sharey=False)
for ax, k, ttl in [(axs[0], "F3", "53 features · IID"), (axs[1], "F4", "21 features · IID")]:
    for p in ["yakinsama_kalici", "fedprox_kalici"]:
        for i, ((kk, s, pp, sd), b) in enumerate([(kk, v) for kk, v in curves.items() if kk[0] == k and kk[1] == "IID" and kk[2] == p]):
            ax.plot(np.arange(1, len(b) + 1) * 5, b, color=C[p], lw=0.7, alpha=0.75, label=PLAB[p] if i == 0 else None)
    ax.set_yscale("log"); ax.set_xlabel("epoch equivalent (rounds × 5 local epochs)"); ax.set_title(ttl, fontsize=10)
axs[0].set_ylabel("best validation loss (log)"); axs[0].legend(fontsize=7, frameon=False)
fig.tight_layout(); fig.savefig(FIG / "val_hist.png", dpi=170); plt.close(fig)

# Fig C: LOFO per family at W=50, F=1000
o = rd("F2", "F2_olcut_W50_F1000.csv")
fig, ax = plt.subplots(figsize=(10, 3.3)); x = np.arange(len(o)); w = 0.27
ax.bar(x - w, o["AE_ANOMALY"] * 100, w, color="#D64545", label="AE · ANOMALY (single flow)")
ax.bar(x, o["RF_tek_recall_α"] * 100, w, color="#8A8F98", label="RF only (single flow, trained on the other 8 families)")
ax.bar(x + w, o["karisik_ρ=1.00"] * 100, w, color="#2A78D6", label="AE + host counter (ρ = 1)")
ax.set_xticks(x); ax.set_xticklabels(o["aile"], rotation=0); ax.set_ylabel("detection on the left-out family (%)")
ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.13)); ax.set_ylim(0, 105)
fig.tight_layout(); fig.savefig(FIG / "lofo.png", dpi=170); plt.close(fig)

# Fig D: sparse attacks, unseen, F=1000, W 20-200 (W=500 excluded: invalid calibration)
t = t5[(t5.F == 1000) & (t5.grup == "görülmemiş") & (t5.W <= 200)]
fig, ax = plt.subplots(figsize=(6.4, 3.4))
for W, col in zip([20, 50, 100, 200], ["#EDA100", "#2E9E6B", "#2A78D6", "#1F3A5F"]):
    for cnt, ls in [("ANOMALY+UNCERTAIN", "-"), ("yalnız ANOMALY", ":")]:
        q = t[(t["sayaç"] == cnt) & (t.W == W)].sort_values("ρ")
        ax.plot(q["ρ"], q["pencere_tespit_mean"] * 100, ls, marker="o", ms=3, color=col, lw=1.3,
                label=f"W = {W}" if cnt == "ANOMALY+UNCERTAIN" else None)
ax.set_xscale("log"); ax.set_xlabel("share of attack flows in the window ρ (log)"); ax.set_ylabel("window-level detection (%)")
ax.legend(fontsize=7, frameon=False, title="solid: ANOMALY+UNCERTAIN\ndotted: ANOMALY only", title_fontsize=7)
fig.tight_layout(); fig.savefig(FIG / "seyrek.png", dpi=170); plt.close(fig)

# Fig E: risk-coverage (test set), selected models, 53 and 21 features
fig, axs = plt.subplots(1, 2, figsize=(10, 3.5), sharey=True)
for ax, k in [(axs[0], "F3"), (axs[1], "F4")]:
    r = rd(k, f"{k}_risk_kapsama_ozet.csv"); r = r[r["yaygınlık"] == "test kümesi"]
    sel = [("Isolation Forest", "Isolation Forest", "#8A8F98", "-"), ("AE merkezi", "AE central (FP32)", C["merk"], "-"),
           ("AE merkezi INT8", "AE central (INT8)", C["merk"], "--"), ("Federe AE · orijinal", PLAB["orijinal"], C["orijinal"], "-"),
           ("Federe AE · orijinal_kucuk_yigin", PLAB["orijinal_kucuk_yigin"], C["orijinal_kucuk_yigin"], "-"),
           ("Federe AE · yakinsama_kalici", PLAB["yakinsama_kalici"], C["yakinsama_kalici"], "-"),
           ("Federe AE · fedprox_kalici", PLAB["fedprox_kalici"], C["fedprox_kalici"], "-")]
    for m, lab, col, ls in sel:
        q = r[r.model == m].sort_values("kapsama")
        if len(q): ax.plot(q.kapsama, q["mean"], ls, color=col, lw=1.4, label=lab)
    ax.set_xlabel("coverage (share of automatic decisions)"); ax.set_title("53 features" if k == "F3" else "21 features", fontsize=10)
axs[0].set_ylabel("selective risk (test set)"); axs[0].legend(fontsize=7, frameon=False)
fig.tight_layout(); fig.savefig(FIG / "risk_kapsama.png", dpi=170); plt.close(fig)

# Fig F: INT8 threshold validity, normal UNCERTAIN per seed, central model 53 vs 21 features
fig, ax = plt.subplots(figsize=(7.5, 3.2))
rules = ["FP32 skor + FP32 eşik", "INT8 skor + devralınan FP32 eşik", "INT8 skor + INT8 yeniden kalibrasyon"]   # data keys
rl = ["FP32 + FP32 threshold", "INT8 + inherited FP32 threshold", "INT8 + recalibration"]
for off, k, col in [(-0.15, "F3", "#2A78D6"), (0.15, "F4", "#D64545")]:
    i = rd(k, f"{k}_int8_tum_tohumlar.csv"); i = i[i.model == "Merkezi AE"]
    for j, rr in enumerate(rules):
        v = i[i.kural == rr].normal_UNCERTAIN * 100
        ax.plot(np.full(len(v), j + off), v, "o", ms=4, color=col, alpha=0.7, label=("53 features" if k == "F3" else "21 features") if j == 0 else None)
ax.axhline(4, color="black", lw=0.8, ls="--"); ax.text(0.55, 4.4, "β = 4%", fontsize=7)  # moved right of the y-axis label (layout only)
ax.set_xticks(range(3)); ax.set_xticklabels(rl); ax.set_yscale("log"); ax.set_ylabel("UNCERTAIN on normal traffic (%, log)")
ax.legend(fontsize=7, frameon=False); fig.tight_layout(); fig.savefig(FIG / "int8_esik.png", dpi=170); plt.close(fig)

# Fig G: per-family three-way decisions (10 seeds)
fams = [("known", f) for f in ["backdoor", "ddos", "dos", "injection", "password", "scanning"]] + [("held-out", f) for f in ["ransomware", "xss", "mitm"]]
fig, ax = plt.subplots(figsize=(9.5, 3.4)); x = np.arange(len(fams) + 1)
labs = ["normal"] + [f + ("*" if g == "held-out" else "") for g, f in fams]
rows = [E3["normal|normal"]] + [E3[f"{g}|{f}"] for g, f in fams]
a = np.array([[r["anomaly_rate"], r["uncertain_rate"], r["normal_rate"]] for r in rows]) * 100
ax.bar(x, a[:, 0], color="#D64545", label="ANOMALY"); ax.bar(x, a[:, 1], bottom=a[:, 0], color="#EDA100", label="UNCERTAIN")
ax.bar(x, a[:, 2], bottom=a[:, 0] + a[:, 1], color="#8A8F98", label="NORMAL")
ax.set_xticks(x); ax.set_xticklabels(labs); ax.set_ylabel("share of decisions (%)"); ax.set_ylim(0, 100)
ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.12))
fig.tight_layout(); fig.savefig(FIG / "aile_kararlari.png", dpi=170); plt.close(fig)
print("written:", sorted(p.name for p in FIG.glob("*.png")))
