"""Final report: reads ONLY the Colab output files in colab_sonuclari/ and writes
rapor/values.json (every number the report prints) and rapor/figs/*.png.
Nothing is trained or recomputed from models; tests marked 'own' are paired Wilcoxon tests computed here
from the per-seed CSVs (no Holm correction) and are labelled as such in the report."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import wilcoxon
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "colab_sonuclari" / "runs"; A = ROOT / "colab_sonuclari" / "artifacts"
OUT = ROOT / "rapor"; FIG = OUT / "figs"; FIG.mkdir(parents=True, exist_ok=True)
RUN = {"F1": "20261110-222358_final_F1_fl_teshis", "04": "20261111-042106_midterm_phase4",
       "04b": "20261111-055215_midterm_phase4b_resolution", "F2": "20261111-060847_final_F2_lofo",
       "F5": "20261111-064904_final_F5_seyrek_saldiri", "F3": "20261112-060216_final_F3_asama5_9",
       "F4": "20261112-120717_final_F4_cihaz_modeli"}
rd = lambda k, f, **kw: pd.read_csv(R / RUN[k] / f, **kw)
V = {"runs": RUN}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
SCN = ["IID", "Dirichlet=1.0", "Dirichlet=0.1"]
PROT = ["orijinal", "orijinal_kucuk_yigin", "yakinsama_kalici", "fedprox_kalici"]
PLAB = {"orijinal": "P1 · 40 tur × 5 epoch, Adam sıfırlanır", "orijinal_kucuk_yigin": "P2 · eşit adım (küçük yığın)",
        "yakinsama_kalici": "P3 · tavana kadar, Adam korunur", "fedprox_kalici": "P4 · FedProx μ=0,01"}

def own_test(a, b):
    d = np.asarray(a) - np.asarray(b)
    return {"fark": float(d.mean()), "a_buyuk": int((d > 0).sum()), "p": float(wilcoxon(d).pvalue)}

# ------------------------------------------------------------------ F1 (seed 0)
f1 = rd("F1", "F1_sonuclar.csv"); f1p = f1[f1.kalibrasyon == "havuz skor"]
def f1row(model, split="IID"):
    r = f1p[(f1p.model == model) & (f1p["istemci_bölmesi"] == split)].iloc[0]
    return {"ano": r["görülmemiş_ANOMALY"], "kac": r["görülmemiş_kaçan"]}
eg1 = rd("F1", "F1_egitim_bilgisi.csv")
V["F1"] = {k: f1row(m) for k, m in [("M_yak", "M_yakinsama"), ("M_200", "M_200"), ("M_esit", "M_esit_adim"),
                                     ("FL_orj", "FL_IID_orijinal"), ("FL_kucuk", "FL_IID_orijinal_kucuk_yigin"),
                                     ("FL_reset", "FL_IID_yakinsama_reset"), ("FL_kalici", "FL_IID_yakinsama_kalici"),
                                     ("FL_prox", "FL_IID_fedprox_kalici"), ("K1_kalici", "K1_orijinal_kalici"),
                                     ("M_flkod", "M_fl_kodu")]}
V["F1"]["D01_kalici"] = f1row("FL_Dirichlet0.1_yakinsama_kalici", "Dirichlet=0.1")
V["F1"]["steps"] = {r["model"]: float(r.get("local_steps_mean", np.nan)) for _, r in eg1.iterrows()} if "local_steps_mean" in eg1 else {}

# ------------------------------------------------------------------ F3 / F4 FL
def fl_block(k):
    d = rd(k, f"{k}_fl_tum_tohumlar.csv"); out = {}
    for cal in ["havuz skor", "istemci başına"]:
        x = d[d.kalibrasyon == cal]
        for (s, m), g in x.groupby(["senaryo", "model"]):
            out[f"{cal}|{s}|{m}"] = {"ano": g["görülmemiş_ANOMALY"].mean(), "ano_sd": g["görülmemiş_ANOMALY"].std(),
                                     "kac": g["görülmemiş_kaçan"].mean(), "bil": g["bilinen_ANOMALY"].mean(),
                                     "fpr_w": g["istemci_FPR_ağırlıklı"].mean(), "fpr_worst": g["istemci_FPR_en_kötü"].mean(),
                                     "fpr_worst_max": g["istemci_FPR_en_kötü"].max(), "n": int(len(g)), "kac_sd": g["görülmemiş_kaçan"].std(),
                                     "cov": g["coverage"].mean(), "sr": g["selective_risk"].mean(), "f1": g["f1_görülmemiş"].mean()}
    t = rd(k, f"{k}_fl_testler.csv")
    tests = {f"{r['a']}||{r['b']}||{r['metrik']}": {"fark": r["ortalama_fark_a-b"], "a_buyuk": int(r["a_daha_büyük_tohum"]),
                                                   "p_holm": r["p_holm"]} for _, r in t.iterrows()}
    own = {}
    p = d[d.kalibrasyon == "havuz skor"]
    piv = lambda s, m, c: p[(p.senaryo == s) & (p.model == m)].set_index("tohum")[c].sort_index()
    for s in SCN:
        for pr in PROT:
            own[f"kac|{s}|{pr}"] = own_test(piv(s, f"FedAvg · {pr}", "görülmemiş_kaçan"), piv(s, "Merkezi (yakınsama)", "görülmemiş_kaçan"))
        own[f"H1|{s}"] = own_test(piv(s, "FedAvg · orijinal_kucuk_yigin", "görülmemiş_ANOMALY"), piv(s, "FedAvg · orijinal", "görülmemiş_ANOMALY"))
        own[f"prox|{s}"] = own_test(piv(s, "FedAvg · fedprox_kalici", "görülmemiş_ANOMALY"), piv(s, "FedAvg · yakinsama_kalici", "görülmemiş_ANOMALY"))
    q = d[d.kalibrasyon == "istemci başına"]
    pq = lambda s, m, c: q[(q.senaryo == s) & (q.model == m)].set_index("tohum")[c].sort_index()
    for s in ["IID", "Dirichlet=0.1"]:
        for c in ["görülmemiş_ANOMALY", "görülmemiş_kaçan"]:
            own[f"yerel|{s}|{c}"] = own_test(pq(s, "Yalnız yerel (yakınsama)", c), pq(s, "FedAvg · yakinsama_kalici", c))
    e = rd(k, f"{k}_egitim_tum_tohumlar.csv")
    stops = {f"{s}|{pr}": e[(e.senaryo == s) & (e.protokol == pr)].stopped_by.value_counts().to_dict() for s in SCN for pr in PROT}
    steps = {f"{s}|{pr}": float(e[(e.senaryo == s) & (e.protokol == pr)].local_steps_mean.mean()) for s in SCN for pr in PROT}
    vl = {f"{s}|{pr}": float(e[(e.senaryo == s) & (e.protokol == pr)].val_loss_best.mean()) for s in SCN for pr in PROT}
    rounds = {f"{s}|{pr}": float(e[(e.senaryo == s) & (e.protokol == pr)].rounds_run.mean()) for s in SCN for pr in PROT}
    comm = {f"{s}|{pr}": float(e[(e.senaryo == s) & (e.protokol == pr)].comm_MB.mean()) for s in SCN for pr in PROT}
    return {"tab": out, "tests": tests, "own": own, "stops": stops, "steps": steps, "val_loss": vl, "rounds": rounds, "comm": comm}
V["F3"] = fl_block("F3"); V["F4"] = fl_block("F4")

# ------------------------------------------------------------------ val_hist (artifacts)
import re
vh = []
curves = {}
for setn, key in [("final_f3", "F3"), ("final_f4", "F4")]:
    for f in sorted((A / setn).glob("s*_*.json")):
        m = re.match(r"s(\d+)_(IID|Dirichlet1\.0|Dirichlet0\.1)_(orijinal_kucuk_yigin|orijinal|yakinsama_kalici|fedprox_kalici)_", f.name)
        if not m: continue
        d = json.loads(f.read_text(encoding="utf-8")); h = np.asarray(d.get("val_hist") or [], float)
        if len(h) == 0: continue
        b = np.minimum.accumulate(h); n = len(b)
        vh.append({"k": key, "s": m[2], "p": m[3], "seed": int(m[1]), "stop": d["stopped_by"],
                   "r10": (b[n - 11] - b[-1]) / b[n - 11] if n > 10 else np.nan,
                   "r50": (b[n - 51] - b[-1]) / b[n - 51] if n > 50 else np.nan})
        curves[(key, m[2], m[3], int(m[1]))] = b
VH = pd.DataFrame(vh); cap = VH[VH.stop == "epoch_cap"]
V["valhist"] = {f"{k}|{s}|{p}": {"n": int(len(g)), "r10_min": g.r10.min(), "r10_max": g.r10.max(), "r50_mean": g.r50.mean(),
                                 "below": int((g.r10 < 0.005).sum())} for (k, s, p), g in cap.groupby(["k", "s", "p"])}
V["valhist_all_cap"] = {"n": int(len(cap)), "below": int((cap.r10 < 0.005).sum()), "r10_min": cap.r10.min()}

# ------------------------------------------------------------------ ablation / INT8 / tiny / robustness / RC
def abl(k):
    a = rd(k, f"{k}_ablasyon_ozet.csv")
    return {f"{r['yapılandırma']}|{r['metrik']}": {"m": r["ortalama"], "sd": r["std"]} for _, r in a.iterrows()}
def int8(k):
    i = rd(k, f"{k}_int8_tum_tohumlar.csv")
    return {f"{m}|{r}": {"fpr": g.normal_FPR.mean(), "fpr_max": g.normal_FPR.max(), "unc": g.normal_UNCERTAIN.mean(),
                         "unc_min": g.normal_UNCERTAIN.min(), "unc_max": g.normal_UNCERTAIN.max(),
                         "ano": g["görülmemiş_ANOMALY"].mean()} for (m, r), g in i.groupby(["model", "kural"])}
def tiny(k):
    t = rd(k, f"{k}_tiny_tum_tohumlar.csv")
    return {m: {c: float(g[c].mean()) for c in ["parametre", "tflite_fp32_KB", "tflite_int8_KB", "tahmini_RAM_KB_int8",
                                               "gecikme_fp32_µs_colab", "gecikme_int8_µs_colab", "Spearman_FP32_INT8"]}
            | {"sp_min": float(g.Spearman_FP32_INT8.min()), "sp_max": float(g.Spearman_FP32_INT8.max())}
            for m, g in t.groupby("model")}
def rob(k):
    r = rd(k, f"{k}_rob_tum_tohumlar.csv")
    return {f"{b}|{l}|{p}": {"fpr": g.normal_FPR.mean(), "fpr_max": g.normal_FPR.max(), "unc": g.normal_UNCERTAIN.mean(),
                             "ano": g["görülmemiş_ANOMALY"].mean(), "kac": g["görülmemiş_kaçan"].mean(),
                             "f1": g["f1_görülmemiş"].mean(), "cov": g["coverage"].mean(), "sr": g["selective_risk"].mean(), "sr1": g["selective_risk_π=%1"].mean()}
            for (b, l, p), g in r.groupby(["bozulma", "düzey", "politika"])}
def rc(k):
    r = rd(k, f"{k}_risk_kapsama_ozet.csv")
    return {f"{m}|{y}|{c:.2f}": v for (m, y, c), v in r.set_index(["model", "yaygınlık", "kapsama"])["mean"].items()}
for k in ["F3", "F4"]:
    V[k] |= {"abl": abl(k), "int8": int8(k), "tiny": tiny(k), "rob": rob(k), "rc": rc(k)}
    t = rd(k, f"{k}_ablasyon_testler.csv")
    V[k]["abl_tests"] = {f"{r['a']}||{r['b']}||{r['metrik']}": {"fark": r["ortalama_fark_a-b"], "a_buyuk": int(r["a_daha_büyük_tohum"]),
                                                               "p_holm": r["p_holm"]} for _, r in t.iterrows()}
a3 = rd("F3", "F3_abl_tum_tohumlar.csv"); a4 = rd("F4", "F4_abl_tum_tohumlar.csv")
g3 = a3[a3["yapılandırma"] == "A3 · AE + seçici"].set_index("tohum").sort_index()
g4 = a4[a4["yapılandırma"] == "A3 · AE + seçici"].set_index("tohum").sort_index()
q4 = a4[a4["yapılandırma"] == "A3q · INT8 AE + seçici (merkezi)"].set_index("tohum").sort_index()
V["own_device"] = {"kac_cihaz_eksi_tumu": own_test(g4["görülmemiş_kaçan"], g3["görülmemiş_kaçan"]),
                   "kac_int8_eksi_fp32_cihaz": own_test(q4["görülmemiş_kaçan"], g4["görülmemiş_kaçan"])}
cm = rd("F4", "F4_cihaz_eksi_tumu_testler.csv")
V["F4"]["cihaz_tumu"] = {f"{r['a']}||{r['metrik']}": {"fark": r["ortalama_fark_a-b"], "a_buyuk": int(r["a_daha_büyük_tohum"]),
                                                     "p_holm": r["p_holm"]} for _, r in cm.iterrows()}
V["F4"]["seen"] = json.loads((R / RUN["F4"] / "F4_cihaz_oznitelikleri.json").read_text(encoding="utf-8"))["eğitimde_birebir_görülmüş_pay"]
V["F3"]["iforest_fpr"] = {"min": float(a3[a3["yapılandırma"].str.startswith("A1")].normal_FPR.min()),
                          "max": float(a3[a3["yapılandırma"].str.startswith("A1")].normal_FPR.max())}

# ------------------------------------------------------------------ F2 LOFO
cr = rd("F2", "F2_on_kayitli_olcutler.csv")
V["F2"] = {"olcut": cr.to_dict(orient="records"), "aile_W50_F1000": rd("F2", "F2_olcut_W50_F1000.csv").to_dict(orient="records"),
           "aile_W50_F5000": rd("F2", "F2_olcut_W50_F5000.csv").to_dict(orient="records")}
ae2 = rd("F2", "F2_ae_egitim.csv"); V["F2"]["ae_epoch"] = [int(ae2.epoch.min()), int(ae2.epoch.max())]
V["F2"]["ae_stop"] = ae2.durma_nedeni.value_counts().to_dict()
hk = rd("F2", "F2_host_katman_ozet.csv")
V["F2"]["host"] = hk.to_dict(orient="records")

# ------------------------------------------------------------------ F5 sparse
t5 = rd("F5", "F5_tespit_grup.csv"); c5 = rd("F5", "F5_normal_maliyet.csv")
V["F5"] = {"tespit": t5[(t5["sayaç"] == "ANOMALY+UNCERTAIN") & (t5.F == 1000)][["W", "grup", "ρ", "pencere_tespit_mean"]].to_dict(orient="records"),
           "tespit_anom": t5[(t5["sayaç"] == "yalnız ANOMALY") & (t5.F == 1000)][["W", "grup", "ρ", "pencere_tespit_mean"]].to_dict(orient="records"),
           "maliyet": c5.to_dict(orient="records")}
s5 = rd("F5", "F5_tum_tohumlar.csv")
s5 = s5[(s5.durum == "tamam") & (s5["sayaç"] == "ANOMALY+UNCERTAIN") & (s5.F == 1000)].drop_duplicates(["tohum", "W"])
V["F5"]["en_kotu_host"] = {int(W): g.set_index("tohum")["normal_haftalik_en_kotu_host"].round(2).to_dict() for W, g in s5.groupby("W")}

json.dump(V, open(OUT / "values.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1,
          default=lambda o: o.item() if hasattr(o, "item") else str(o))

# ================================================================== figures
C = {"merk": "#1F3A5F", "orijinal": "#D64545", "orijinal_kucuk_yigin": "#EDA100", "yakinsama_kalici": "#2A78D6", "fedprox_kalici": "#2E9E6B"}
# Fig A: FL vs central, unseen ANOMALY, pooled calibration, F3 and F4
fig, axs = plt.subplots(1, 2, figsize=(10, 3.9), sharey=True)
for ax, k, ttl in [(axs[0], "F3", "53 öznitelik (F3)"), (axs[1], "F4", "21 öznitelikli cihaz modeli (F4)")]:
    d = rd(k, f"{k}_fl_tum_tohumlar.csv"); d = d[d.kalibrasyon == "havuz skor"]
    x = np.arange(3); w = 0.16
    for j, (m, lab, col) in enumerate([("Merkezi (yakınsama)", "merkezi", C["merk"])] + [(f"FedAvg · {p}", PLAB[p], C[p]) for p in PROT]):
        vals = [d[(d.senaryo == s) & (d.model == m)]["görülmemiş_ANOMALY"] * 100 for s in SCN]
        xs = x + (j - 2) * w
        ax.bar(xs, [v.mean() for v in vals], w, color=col, label=lab, alpha=0.9)
        for xi, v in zip(xs, vals): ax.plot(np.full(len(v), xi), v, ".", color="black", ms=2.5, alpha=0.6)
    ax.set_xticks(x); ax.set_xticklabels(SCN); ax.set_title(ttl, fontsize=10)
axs[0].set_ylabel("görülmemiş saldırılarda ANOMALY (%)")
h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, fontsize=7, frameon=False, ncol=5, loc="lower center")
fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig(FIG / "fl_merkezi.png", dpi=170); plt.close(fig)

# Fig B: val_hist curves (cap-hit protocols)
fig, axs = plt.subplots(1, 2, figsize=(10, 3.4), sharey=False)
for ax, k, ttl in [(axs[0], "F3", "53 öznitelik · IID"), (axs[1], "F4", "21 öznitelik · IID")]:
    for p in ["yakinsama_kalici", "fedprox_kalici"]:
        for i, ((kk, s, pp, sd), b) in enumerate([(kk, v) for kk, v in curves.items() if kk[0] == k and kk[1] == "IID" and kk[2] == p]):
            ax.plot(np.arange(1, len(b) + 1) * 5, b, color=C[p], lw=0.7, alpha=0.75, label=PLAB[p] if i == 0 else None)
    ax.set_yscale("log"); ax.set_xlabel("epoch eşdeğeri (tur × 5 yerel epoch)"); ax.set_title(ttl, fontsize=10)
axs[0].set_ylabel("en iyi doğrulama kaybı (log)"); axs[0].legend(fontsize=7, frameon=False)
fig.tight_layout(); fig.savefig(FIG / "val_hist.png", dpi=170); plt.close(fig)

# Fig C: LOFO per family at W=50, F=1000
o = rd("F2", "F2_olcut_W50_F1000.csv")
fig, ax = plt.subplots(figsize=(10, 3.3)); x = np.arange(len(o)); w = 0.27
ax.bar(x - w, o["AE_ANOMALY"] * 100, w, color="#D64545", label="AE · ANOMALY (tek akış)")
ax.bar(x, o["RF_tek_recall_α"] * 100, w, color="#8A8F98", label="yalnız RF (tek akış, diğer 8 aileyle eğitildi)")
ax.bar(x + w, o["karisik_ρ=1.00"] * 100, w, color="#2A78D6", label="AE + host sayacı (ρ = 1)")
ax.set_xticks(x); ax.set_xticklabels(o["aile"], rotation=0); ax.set_ylabel("dışarıda bırakılan ailede tespit (%)")
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
ax.set_xscale("log"); ax.set_xlabel("penceredeki saldırı akışı payı ρ (log)"); ax.set_ylabel("pencere düzeyinde tespit (%)")
ax.legend(fontsize=7, frameon=False, title="düz: ANOMALY+UNCERTAIN\nnoktalı: yalnız ANOMALY", title_fontsize=7)
fig.tight_layout(); fig.savefig(FIG / "seyrek.png", dpi=170); plt.close(fig)

# Fig E: risk-coverage (test set), selected models, F3 and F4
fig, axs = plt.subplots(1, 2, figsize=(10, 3.5), sharey=True)
for ax, k in [(axs[0], "F3"), (axs[1], "F4")]:
    r = rd(k, f"{k}_risk_kapsama_ozet.csv"); r = r[r["yaygınlık"] == "test kümesi"]
    sel = [("Isolation Forest", "Isolation Forest", "#8A8F98", "-"), ("AE merkezi", "AE merkezi (FP32)", C["merk"], "-"),
           ("AE merkezi INT8", "AE merkezi (INT8)", C["merk"], "--"), ("Federe AE · orijinal", PLAB["orijinal"], C["orijinal"], "-"),
           ("Federe AE · orijinal_kucuk_yigin", PLAB["orijinal_kucuk_yigin"], C["orijinal_kucuk_yigin"], "-"),
           ("Federe AE · yakinsama_kalici", PLAB["yakinsama_kalici"], C["yakinsama_kalici"], "-"),
           ("Federe AE · fedprox_kalici", PLAB["fedprox_kalici"], C["fedprox_kalici"], "-")]
    for m, lab, col, ls in sel:
        q = r[r.model == m].sort_values("kapsama")
        if len(q): ax.plot(q.kapsama, q["mean"], ls, color=col, lw=1.4, label=lab)
    ax.set_xlabel("kapsama (otomatik karar payı)"); ax.set_title("53 öznitelik (F3)" if k == "F3" else "21 öznitelik (F4)", fontsize=10)
axs[0].set_ylabel("seçici risk (test kümesi)"); axs[0].legend(fontsize=7, frameon=False)
fig.tight_layout(); fig.savefig(FIG / "risk_kapsama.png", dpi=170); plt.close(fig)

# Fig F: INT8 threshold validity, normal UNCERTAIN per seed, central model F3 vs F4
fig, ax = plt.subplots(figsize=(7.5, 3.2))
rules = ["FP32 skor + FP32 eşik", "INT8 skor + devralınan FP32 eşik", "INT8 skor + INT8 yeniden kalibrasyon"]
rl = ["FP32 + FP32 eşiği", "INT8 + devralınan FP32 eşiği", "INT8 + yeniden kalibrasyon"]
for off, k, col in [(-0.15, "F3", "#2A78D6"), (0.15, "F4", "#D64545")]:
    i = rd(k, f"{k}_int8_tum_tohumlar.csv"); i = i[i.model == "Merkezi AE"]
    for j, rr in enumerate(rules):
        v = i[i.kural == rr].normal_UNCERTAIN * 100
        ax.plot(np.full(len(v), j + off), v, "o", ms=4, color=col, alpha=0.7, label=("53 öznitelik" if k == "F3" else "21 öznitelik") if j == 0 else None)
ax.axhline(4, color="black", lw=0.8, ls="--"); ax.text(-0.45, 4.4, "β = %4", fontsize=7)
ax.set_xticks(range(3)); ax.set_xticklabels(rl); ax.set_yscale("log"); ax.set_ylabel("normal trafikte UNCERTAIN (%, log)")
ax.legend(fontsize=7, frameon=False); fig.tight_layout(); fig.savefig(FIG / "int8_esik.png", dpi=170); plt.close(fig)
print("yazıldı:", OUT / "values.json", sorted(p.name for p in FIG.glob("*.png")))

# ================================================================== Aşama 1–4 (Colab çalıştırmaları 04 ve 04b)
P4 = R / RUN["04"]; P4b = R / RUN["04b"]
pr = json.loads((P4 / "prepare_report.json").read_text(encoding="utf-8"))
ts = json.loads((P4 / "training_summary.json").read_text(encoding="utf-8"))
sel = json.loads((P4 / "ae_selection.json").read_text(encoding="utf-8"))
dfi = json.loads((P4 / "data_file_info.json").read_text(encoding="utf-8"))
b2 = pd.read_csv(P4 / "figures/02_binary_B2_10seeds.csv")
fs = pd.read_csv(P4 / "figures/02_feature_sets_10seeds.csv"); fst = pd.read_csv(P4 / "figures/02_feature_sets_tests.csv")
ep = pd.read_csv(P4 / "figures/02_recall_vs_epochs_seed0.csv")
e3 = pd.read_csv(P4 / "E3_per_family_all_seeds.csv")
tier = pd.read_csv(P4 / "tiering_vs_binary_10seeds.csv"); e2 = pd.read_csv(P4 / "E2_statistics.csv")
ms = json.loads((P4 / "midterm_summary.json").read_text(encoding="utf-8"))
gw = pd.read_csv(P4b / "04b_gateway_baseline.csv", header=[0, 1], index_col=0)
P14 = {
    "data": {"rows": dfi["rows"], "cols": dfi["columns"], "after1": pr["dedup"]["after_stage1_exact_input_columns"],
             "after2": pr["dedup"]["after_stage2_final_vectors"], "per_type": pr["dedup"]["per_type"],
             "splits": pr["split_sizes"], "split_by_type": pr["split_by_type"], "n_feat": pr["n_features"],
             "benign_attack_coll": pr["dedup"]["benign_attack_collision_vectors"]},
    "train": {"epochs": [t["epoch"] for t in ts], "stops": [t["durma_nedeni"] for t in ts]},
    "sel": sel["comparison"],
    "b2": {f"{m}|{g}": {c: float(x[c].mean()) for c in ["precision", "recall", "fpr", "pr_auc", "roc_auc"]}
           for (m, g), x in b2.groupby(["model", "saldırılar"])},
    "fs": {f"{o}|{g}": float(x["recall_fpr_1%"].mean()) for (o, g), x in fs.groupby(["öznitelik", "saldırılar"])},
    "fs_tests": fst.to_dict(orient="records"),
    "epochs_seed0": ep.to_dict(orient="records"),
    "E1": ms["E1_gecerlilik_tohum_ortalamasi"], "B3": ms["B3_yanlis_alarm_10_tohum"],
    "E3": {f: {c: float(g[c].mean()) for c in ["anomaly_rate", "uncertain_rate", "normal_rate"]} | {"group": g["group"].iloc[0]}
           for f, g in e3.groupby(e3["group"] + "|" + e3["family"])},
    "tier": {f"{r}|{y}|{s}": {c: float(g[c].mean()) for c in ["benign_immediate_alarm", "benign_review", "attack_immediate_alarm", "attack_review",
                                                               "attack_missed", "precision_alarm_tier", "precision_review_tier", "alarms_per_flows", "reviews_per_flows"]}
             for (r, y, s), g in tier.groupby(["rule", "yaygınlık", "saldırılar"])},
    "E2": e2.to_dict(orient="records"),
    "gw": {fam: {"ae": float(gw.loc[fam, ("AE_ANOMALY", "mean")]), "rf": float(gw.loc[fam, ("RF_tek_basina_recall", "mean")]),
                 "auc": (None if pd.isna(gw.loc[fam, ("RF_AUC_UNCERTAIN_bandinda", "mean")]) else float(gw.loc[fam, ("RF_AUC_UNCERTAIN_bandinda", "mean")])),
                 "ae_gw": float(gw.loc[fam, ("AE+ağ_geçidi_recall", "mean")])}
           for fam in ["mitm", "ransomware", "xss", "normal (yanlış alarm)"]},
}
V["P14"] = P14
json.dump(V, open(OUT / "values.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1,
          default=lambda o: o.item() if hasattr(o, "item") else str(o))

# Fig G: per-family three-way decisions (10 seeds)
fams = [("known", f) for f in ["backdoor", "ddos", "dos", "injection", "password", "scanning"]] + [("held-out", f) for f in ["ransomware", "xss", "mitm"]]
fig, ax = plt.subplots(figsize=(9.5, 3.4)); x = np.arange(len(fams) + 1)
labs = ["normal"] + [f + ("*" if g == "held-out" else "") for g, f in fams]
rows = [P14["E3"]["normal|normal"]] + [P14["E3"][f"{g}|{f}"] for g, f in fams]
a = np.array([[r["anomaly_rate"], r["uncertain_rate"], r["normal_rate"]] for r in rows]) * 100
ax.bar(x, a[:, 0], color="#D64545", label="ANOMALY"); ax.bar(x, a[:, 1], bottom=a[:, 0], color="#EDA100", label="UNCERTAIN")
ax.bar(x, a[:, 2], bottom=a[:, 0] + a[:, 1], color="#8A8F98", label="NORMAL")
ax.set_xticks(x); ax.set_xticklabels(labs); ax.set_ylabel("karar payı (%)"); ax.set_ylim(0, 100)
ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.12))
fig.tight_layout(); fig.savefig(FIG / "aile_kararlari.png", dpi=170); plt.close(fig)
print("Aşama 1–4 değerleri eklendi")
