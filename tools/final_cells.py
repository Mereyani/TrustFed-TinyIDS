# Final-phase notebook cell definitions (F1, F2, F3). Imported by build_final_notebooks.py.
# Language of notebooks: Turkish (as the midterm notebooks).

def define(NB, md, code, SETUP, FLUSH):
    # =========================================================================== F1
    NB["F1_fl_teshis.ipynb"] = [
        md(r"""
# F1 · Madde 2 — Federe model neden merkezi modelden zayıf? (teşhis, tohum 0)
**Profesörün notu:** *Federated modelin merkezi modele göre neden belirgin şekilde düşük performans gösterdiğini araştır ve
eşdeğer eğitim koşullarında yeniden karşılaştır.*

Ara dönemde (tohum 0): görülmemiş ANOMALY merkezi %47,0, FedAvg-IID %13,7, yalnız yerel %13,9. O protokolde
FedAvg 40 tur × 5 yerel epoch, Keras Adam her yerel eğitimde yeniden oluşturuluyordu; merkezi model 200 epoch eğitildi.

**Sınanan hipotezler (sonuç varsayılmaz, ölçülür):**

| | Hipotez | Bu defterdeki test |
|---|---|---|
| H1 | **Adım sayısı eşit değil.** Ara dönem karşılaştırması epoch sayısında eşitti (200 epoch), ama güncelleme adımında değil: 5 IID istemcide istemci başına ~4 yığın/epoch → 40×5 yerel epoch ≈ 800 adım; merkezi 200 epoch ≈ 3.400 adım. Ağırlık ortalaması adımları toplamaz. | merkezi model FedAvg-IID ile **aynı adım sayısında**; FedAvg aynı tur/epoch ama **yığın/K** ile (adım sayısı ≈ merkezi); FedAvg **yakınsama kuralına kadar** |
| H2 | **Adam durumu her turda sıfırlanıyor.** | K = 1 istemcide Adam korunur / sıfırlanır; yakınsamada korunur / sıfırlanır |
| H3 | **Non-IID istemci sapması (client drift).** | FedProx (μ = `cfg.fl_fedprox_mu`) |
| — | **Kod yolu kontrolü.** FL kodu K = 1 iken merkezi eğitime denk olmalı. | FL kodu K = 1 (Adam korunur) ↔ Keras merkezi |

**Eşdeğer eğitim koşulu (bu çalışmadaki tanım):** aynı model, optimizer (Adam), öğrenme oranı, yığın boyutu ve **aynı
yakınsama kuralı** (en iyi doğrulama kaybı 50 epoch'ta %0,5'ten az iyileşince dur; 40 epoch sabır; en fazla 1.500 epoch;
en iyi ağırlıklar geri yüklenir). FL'de bir tur = E yerel epoch sayılır. Doğrulama kaybı = istemcilerin normal-doğrulama
parçalarının birleşimindeki kayıp.

**Kalibrasyon:** *istemci başına* (her istemci kendi normal-kalibrasyon parçası; doğrudan uygulanabilir) ve *havuz skor*
(istemciler veri değil yalnız kalibrasyon **skorlarını** sunucuya gönderir; bu paylaşımın kabul edilebilir olması gerekir).

**Not:** Bu defter teşhis içindir (tek tohum). Sonuçlar F3'te 10 tohumla tekrarlanır; buradan kesin sonuç çıkarılmaz.
"""),
        code(SETUP),
        code(r'''
import math, tensorflow as tf
from trustids import data as D, models as M, conformal as C, fl as FL
P = D.load_prepared(ART / "prepared"); X = P["X"]
FNAMES = P["preprocessor"].feature_names_
CHOSEN = utils.load_json(ART / "ae_selection.json")["chosen"]; spec = cfg.ae_variants[CHOSEN]
SEED, K, E_LOC = cfg.train_seeds[0], cfg.fl_clients, cfg.fl_local_epochs
DIAG = ART / "fl_diag"; DIAG.mkdir(exist_ok=True)
FP = utils.fingerprint(cfg, ["fl_clients", "fl_scenarios", "fl_orig_rounds", "fl_local_epochs", "fl_fedprox_mu"])
RUN = utils.new_run_dir(Path(PROJECT_DIR) / cfg.runs_dir, "final_F1_fl_teshis")
utils.save_json(utils.environment_info(), RUN / "environment.json"); cfg.save(RUN / "config_used.json")
d_in = X["benign_train"].shape[1]
def build(): return M.build_autoencoder(d_in, spec["hidden"], spec["dropout"], cfg.learning_rate)
CAT = {sp: FL.service_categories(X[sp], FNAMES) for sp in ["benign_train", "benign_val", "benign_cal", "benign_test"]}
PARTS = {s: FL.partition(CAT, K, s, SEED) for s in cfg.fl_scenarios}
SIZES = pd.DataFrame([{"senaryo": s, "istemci": k, **{sp: len(PARTS[s][sp][k]) for sp in CAT}}
                      for s in cfg.fl_scenarios for k in range(K)])
SIZES.to_csv(RUN / "F1_istemci_boyutlari.csv", index=False)
assert (SIZES[["benign_train", "benign_val", "benign_cal", "benign_test"]] > 0).all().all(), "boş istemci parçası var"
print("AE:", CHOSEN, "| tohum", SEED, "| istemci", K, "| yerel epoch", E_LOC, "| parmak izi", FP, "| sonuç klasörü:", RUN)
SIZES.pivot(index="istemci", columns="senaryo", values="benign_train")'''),
        md("## H1 · Güncelleme adımı hesabı (eğitimden önce, yalnız aritmetik)"),
        code(r'''
bs, n_tr = cfg.batch_size, len(X["benign_train"])
c_ep = math.ceil(n_tr / bs)
rows = [{"eğitim": f"merkezi, {cfg.fl_orig_rounds * E_LOC} epoch (ara dönem)", "güncelleme_adımı": c_ep * cfg.fl_orig_rounds * E_LOC}]
for s in cfg.fl_scenarios:
    st = [cfg.fl_orig_rounds * E_LOC * math.ceil(len(p) / bs) for p in PARTS[s]["benign_train"]]
    rows.append({"eğitim": f"FedAvg {s}, {cfg.fl_orig_rounds} tur × {E_LOC} yerel epoch — istemci başına ortalama",
                 "güncelleme_adımı": float(np.mean(st))})
STEPS = pd.DataFrame(rows); STEPS.to_csv(RUN / "F1_adim_hesabi.csv", index=False)
EQ_EPOCHS = max(1, int(round(STEPS.iloc[1]["güncelleme_adımı"] / c_ep)))
print("merkezi epoch başına adım:", c_ep, "| FedAvg-IID istemci adımına eşit merkezi epoch:", EQ_EPOCHS)
STEPS'''),
        md("## Eğitimler (her model Drive'a kaydedilir; oturum kapanırsa devam modunda atlanır)"),
        code(r'''
ALL = np.arange(n_tr)
def cached(key, train_fn):
    mf, jf = DIAG / f"{key}_{FP}.keras", DIAG / f"{key}_{FP}.json"
    if RESUME and mf.exists() and jf.exists():
        print("kayıtlı, atlanıyor:", key); return tf.keras.models.load_model(mf, compile=False), utils.load_json(jf)
    print("eğitiliyor:", key, flush=True)
    m, info = train_fn(); m.save(mf); utils.save_json(info, jf); return m, info

def keras_fixed(epochs):
    def f():
        utils.set_seed(SEED); m = build()
        m.fit(X["benign_train"], X["benign_train"], epochs=epochs, batch_size=bs, shuffle=True, verbose=0)
        return m, {"epochs_equivalent": epochs, "stopped_by": "fixed_epochs", "local_steps_mean": epochs * c_ep, "comm_MB": 0.0}
    return f

def keras_conv():
    p = ART / "models" / f"ae_seed{SEED}.keras"
    if p.exists():                                   # 02 defterinde aynı kuralla eğitilen ana model
        tr = utils.load_json(ART / "training" / f"seed{SEED}.json")
        return tf.keras.models.load_model(p, compile=False), {"epochs_equivalent": tr["epoch"], "stopped_by": tr["durma_nedeni"],
                                                              "local_steps_mean": tr["epoch"] * c_ep, "comm_MB": 0.0}
    utils.set_seed(SEED); m = build()
    h = M.train_autoencoder(m, X["benign_train"], X["benign_val"], cfg.epochs, bs, cfg.patience,
                            conv_window=cfg.conv_window, conv_rel_tol=cfg.conv_rel_tol)
    return m, {"epochs_equivalent": h["epochs_run"], "stopped_by": h["stopped_by"], "local_steps_mean": h["epochs_run"] * c_ep, "comm_MB": 0.0}

def fl_run(parts, rounds, opt_state, mu, Xtr=None, Xval=None, seed=SEED):
    def f():
        return FL.train_federated(build, X["benign_train"] if Xtr is None else Xtr, parts,
                                  X["benign_val"] if Xval is None else Xval, rounds=rounds, local_epochs=E_LOC,
                                  lr=cfg.learning_rate, batch_size=bs, seed=seed, optimizer_state=opt_state, mu=mu,
                                  conv_window=cfg.conv_window, conv_rel_tol=cfg.conv_rel_tol, patience=cfg.patience,
                                  epoch_cap=cfg.epochs, verbose=True)
    return f

MODELS, INFO = {}, {}
def add(key, desc, scen, fn):
    m, info = cached(key, fn); MODELS[key] = m; INFO[key] = {**info, "açıklama": desc, "senaryo": scen}

R0 = cfg.fl_orig_rounds
add("M_yakinsama", "Merkezi, yakınsama kuralı (ana model)", "merkezi", keras_conv)
add("M_200", f"Merkezi, {R0 * E_LOC} epoch (ara dönem karşılaştırması)", "merkezi", keras_fixed(R0 * E_LOC))
add("M_esit_adim", f"Merkezi, {EQ_EPOCHS} epoch (= FedAvg-IID istemci adım sayısı)", "merkezi", keras_fixed(EQ_EPOCHS))
add("M_fl_kodu", "Merkezi, FL kodu (K=1), yakınsama, Adam korunur", "merkezi", fl_run([ALL], None, "persistent", 0.0))
add("K1_orijinal_kalici", f"FL kodu K=1, {R0}×{E_LOC}, Adam korunur (≈ M_200 olmalı)", "merkezi", fl_run([ALL], R0, "persistent", 0.0))
add("K1_orijinal_reset", f"FL kodu K=1, {R0}×{E_LOC}, Adam her tur sıfırlanır (H2 tek başına)", "merkezi", fl_run([ALL], R0, "reset", 0.0))
for s in cfg.fl_scenarios:
    for prot, pz in FL.PROTOCOLS.items():
        add(f"FL_{s.replace('=', '')}_{prot}", f"{s}: {pz['aciklama']}", s,
            lambda s=s, prot=prot: FL.run_protocol(prot, cfg, build, X["benign_train"], PARTS[s]["benign_train"], X["benign_val"], SEED, verbose=True))
LOCAL = {}
for s in [cfg.fl_scenarios[0], cfg.fl_scenarios[-1]]:
    ms = []
    for k in range(K):
        tr, va = PARTS[s]["benign_train"][k], PARTS[s]["benign_val"][k]
        m, info = cached(f"YEREL_{s.replace('=', '')}_k{k}",
                         fl_run([np.arange(len(tr))], None, "persistent", 0.0, Xtr=X["benign_train"][tr], Xval=X["benign_val"][va], seed=SEED + k))
        ms.append(m); INFO[f"YEREL_{s.replace('=', '')}_k{k}"] = {**info, "açıklama": f"yalnız yerel {s}, istemci {k}", "senaryo": s}
    LOCAL[s] = ms
print("tüm eğitimler tamam")'''),
        md("## Değerlendirme: her model × istemci bölmesi × kalibrasyon"),
        code(r'''
ROWS = []
for key, m in MODELS.items():
    scen = cfg.fl_scenarios if INFO[key]["senaryo"] == "merkezi" else [INFO[key]["senaryo"]]
    sc = {sp: M.ae_score(m, X[sp]) for sp in ["benign_cal", "benign_test", "dev_test", "heldout_test"]}
    for s in scen:
        for r in FL.evaluate(lambda k, sp, sc=sc: sc[sp], PARTS[s], X, cfg, SEED):
            ROWS.append({"model": key, "açıklama": INFO[key]["açıklama"], "istemci_bölmesi": s, **r})
for s, ms in LOCAL.items():
    for r in FL.evaluate(lambda k, sp, ms=ms: M.ae_score(ms[k], X[sp]), PARTS[s], X, cfg, SEED, per_client_models=True):
        ROWS.append({"model": f"YEREL_{s.replace('=', '')}", "açıklama": f"Yalnız yerel eğitim ({s}), yakınsama", "istemci_bölmesi": s, **r})
RES = pd.DataFrame(ROWS); RES.to_csv(RUN / "F1_sonuclar.csv", index=False)
TR = pd.DataFrame([{"model": k, **{a: b for a, b in i.items() if a != "val_hist"}} for k, i in INFO.items()])
TR.to_csv(RUN / "F1_egitim_bilgisi.csv", index=False)
display(TR[["model", "açıklama", "stopped_by", "epochs_equivalent", "local_steps_mean", "comm_MB"]].round(2))
RES[RES["kalibrasyon"] == "havuz skor"][["model", "istemci_bölmesi", "istemci_FPR_ort", "istemci_FPR_en_kötü",
     "görülmemiş_ANOMALY", "görülmemiş_UNCERTAIN", "bilinen_ANOMALY", "f1_görülmemiş", "selective_risk"]].round(4)'''),
        code(r'''
RES[RES["kalibrasyon"] == "istemci başına"][["model", "istemci_bölmesi", "en_küçük_n_cal", "istemci_FPR_ort", "istemci_FPR_en_kötü",
     "görülmemiş_ANOMALY", "görülmemiş_UNCERTAIN", "bilinen_ANOMALY", "selective_risk"]].round(4)'''),
        md("## Hipotez tablosu (tohum 0; yalnız fark gösterilir, sonuç F3'teki 10 tohumla verilir)"),
        code(r'''
def v(model, scen, cal="havuz skor", col="görülmemiş_ANOMALY"):
    q = RES[(RES["model"] == model) & (RES["istemci_bölmesi"] == scen) & (RES["kalibrasyon"] == cal)]
    return float(q[col].iloc[0]) if len(q) else np.nan
s0 = cfg.fl_scenarios[0]; t0 = s0.replace("=", "")
H = [("Ara dönem farkı: merkezi 200 epoch − FedAvg-IID orijinal", v("M_200", s0), v(f"FL_{t0}_orijinal", s0)),
     ("H1: merkezi (FedAvg-IID adım sayısında) − FedAvg-IID orijinal", v("M_esit_adim", s0), v(f"FL_{t0}_orijinal", s0)),
     ("H1: FedAvg-IID küçük yığın (≈ merkezi adım sayısı) − FedAvg-IID orijinal", v(f"FL_{t0}_orijinal_kucuk_yigin", s0), v(f"FL_{t0}_orijinal", s0)),
     ("H1: merkezi 200 epoch − FedAvg-IID küçük yığın", v("M_200", s0), v(f"FL_{t0}_orijinal_kucuk_yigin", s0)),
     ("Kod yolu: Keras merkezi 200 epoch − FL kodu K=1 Adam korunur", v("M_200", s0), v("K1_orijinal_kalici", s0)),
     ("H2: K=1 Adam korunur − K=1 Adam sıfırlanır", v("K1_orijinal_kalici", s0), v("K1_orijinal_reset", s0)),
     ("Kod yolu: merkezi yakınsama (Keras) − merkezi yakınsama (FL kodu)", v("M_yakinsama", s0), v("M_fl_kodu", s0))]
for s in cfg.fl_scenarios:
    t = s.replace("=", "")
    H += [(f"{s}: FedAvg yakınsama Adam korunur − FedAvg orijinal", v(f"FL_{t}_yakinsama_kalici", s), v(f"FL_{t}_orijinal", s)),
          (f"{s}: FedAvg yakınsama Adam korunur − Adam sıfırlanır (H2)", v(f"FL_{t}_yakinsama_kalici", s), v(f"FL_{t}_yakinsama_reset", s)),
          (f"{s}: FedProx − FedAvg yakınsama (H3)", v(f"FL_{t}_fedprox_kalici", s), v(f"FL_{t}_yakinsama_kalici", s)),
          (f"{s}: EŞDEĞER KOŞUL merkezi yakınsama − FedAvg yakınsama Adam korunur", v("M_yakinsama", s), v(f"FL_{t}_yakinsama_kalici", s))]
HT = pd.DataFrame(H, columns=["karşılaştırma (görülmemiş ANOMALY, havuz skor kalibrasyonu)", "a", "b"])
HT["a − b (puan)"] = 100 * (HT["a"] - HT["b"])
HT.to_csv(RUN / "F1_hipotez_tablosu.csv", index=False); HT.round(4)'''),
        code(r'''
fig, ax = plt.subplots(figsize=(7.5, 4))
for key, i in INFO.items():
    if i.get("val_hist") and key.startswith("FL_"):
        e = np.arange(1, len(i["val_hist"]) + 1) * E_LOC
        ax.plot(e, i["val_hist"], lw=1, label=key.replace("FL_", ""))
ax.set_yscale("log"); ax.set_xlabel("epoch eşdeğeri (tur × yerel epoch)"); ax.set_ylabel("federe doğrulama kaybı")
ax.set_title(f"FedAvg / FedProx yakınsaması (tohum {SEED})"); ax.legend(fontsize=6, ncol=2)
fig.tight_layout(); fig.savefig(RUN / "F1_yakinsama.png", dpi=150)
sub = RES[(RES["kalibrasyon"] == "havuz skor") & (RES["istemci_bölmesi"] == s0)]
fig, ax = plt.subplots(figsize=(8, 4))
ax.barh(sub["model"], 100 * sub["görülmemiş_ANOMALY"], color="#2a78d6")
ax.set_xlabel("görülmemiş saldırılar: ANOMALY (%)"); ax.set_title(f"{s0} bölmesi, havuz skor kalibrasyonu (tohum {SEED})")
fig.tight_layout(); fig.savefig(RUN / "F1_gorulmemis_anomaly.png", dpi=150)
print("Sonuçlar:", RUN)'''),
        code(FLUSH),
    ]

    # =========================================================================== F2
    NB["F2_lofo.ipynb"] = [
        md(r"""
# F2 · Madde 3 — Her saldırı ailesi sırayla dışarıda (leave-one-family-out, LOFO)
**Profesörün notu:** *Her saldırı ailesini sırayla dışarıda bırakarak unseen-attack değerlendirmesini gerçekleştir.*

Bu protokol öneri v6 §7a.3'te (E7) **ilk doğrulayıcı çalıştırmadan önce** kaydedildi:
* 9 katman (fold): her saldırı ailesi bir kez görülmemiş; diğer 8 aile bilinen (geliştirme) aile;
* **yeni eğitim tohumları 10–19**; veri bölme tohumu değişmez; AE boyutu 32-16-8 sabit (katman başına seçim yok);
* karşılaştırma kümesi: AE (üç karar, akış düzeyi) · AE + Basamak 2 (host sayacı) · AE + Basamak 1 + Basamak 2 ·
  **yalnız RF** (8 bilinen aileyle eğitilir) eşleştirilmiş yanlış alarmda;
* W ∈ {20, 50, 100}, F ∈ {1.000, 5.000}, ρ ∈ {0,10; 0,25; 0,50; 1,00}. Sürüm B'de zaman damgası olmadığı için host
  pencereleri **simülasyondur**.

**Başarı ölçütü (§7a.3):** AE + Basamak 2, ρ = 1,0'da görülmemiş ailenin kaçan + ertelenen oranını **en az 30 puan**
azaltmalı ve en kötü hostun yanlış yükseltmesi bütçe içinde (haftada ≤ 1) kalmalı; bu **9 katmanın en az 6'sında** sağlanmalı.
**Başarısızlık ölçütü:** bilinenlere *benzemeyen* ailelerde (bu katmanda yalnız-RF recall < 0,50) yalnız RF, AE + Basamak 2'ye
yetişirse (≥ AE + Basamak 2 − 0,05), "yalnız normal veriyle" iddiası TON_IoT için geri çekilir ve veri kümesi bulgusu olarak raporlanır.
(< 0,50 ve 0,05 eşikleri öneride açık bırakılmıştı; bu defter çalıştırılmadan önce `configs/default.json`'da sabitlendi.)

**Neden AE her katmanda yeniden eğitilmiyor?** AE yalnız normal-eğitim verisini görür ve normal bölme saldırı aileleri
atanmadan önce çekilir; normal veri her katmanda aynıdır. Defter bunu varsaymaz, **assert** ile doğrular.
**Öneriden sapma (açıkça):** §7a.3 istemci başına (Mondrian) k\* kalibrasyonu yazar; bu merkezi LOFO'da istemci olmadığı için
k\* ara dönemdeki gibi normal-doğrulama pencerelerinden hesaplanır.
"""),
        code(SETUP),
        code(r'''
import tensorflow as tf
from trustids import data as D, models as M, conformal as C, resolution as R, lofo as L
raw = D.load_raw(cfg.data_path, cfg)
P0 = D.load_prepared(ART / "prepared")
spec = cfg.ae_variants[cfg.ae_default]            # önceden kaydedildiği gibi sabit: 32-16-8
LDIR = ART / "lofo"; (LDIR / "models").mkdir(parents=True, exist_ok=True)
FP = utils.fingerprint(cfg, ["lofo_seeds", "lofo_rf_trees", "resolution_windows", "resolution_flows_per_day",
                             "resolution_budget_per_week", "resolution_cal_windows", "resolution_eval_windows", "resolution_rho",
                             "alpha", "beta"])
FAMS = L.all_families(cfg)
RUN = utils.new_run_dir(Path(PROJECT_DIR) / cfg.runs_dir, "final_F2_lofo")
utils.save_json(utils.environment_info(), RUN / "environment.json"); cfg.save(RUN / "config_used.json")
print("katmanlar:", FAMS, "| tohumlar:", cfg.lofo_seeds, "| AE:", spec, "| parmak izi:", FP)'''),
        md("## 1 · LOFO tohumları için AE eğitimi (yalnız normal veri; her tohum bir kez, Drive'a kaydedilir)"),
        code(r'''
X0 = P0["X"]
for seed in cfg.lofo_seeds:
    mf, jf = LDIR / "models" / f"ae_seed{seed}.keras", LDIR / "models" / f"ae_seed{seed}.json"
    if RESUME and mf.exists() and jf.exists():
        print("tohum", seed, "Drive'da kayıtlı, atlanıyor (devam modu)"); continue
    utils.set_seed(seed)
    m = M.build_autoencoder(X0["benign_train"].shape[1], spec["hidden"], spec["dropout"], cfg.learning_rate)
    h = M.train_autoencoder(m, X0["benign_train"], X0["benign_val"], cfg.epochs, cfg.batch_size, cfg.patience,
                            conv_window=cfg.conv_window, conv_rel_tol=cfg.conv_rel_tol)
    m.save(mf)
    utils.save_json({"tohum": seed, "epoch": h["epochs_run"], "durma_nedeni": h["stopped_by"], "en_iyi_epoch": h["best_epoch"],
                     "en_iyi_dogrulama_kaybi": float(min(h["val_loss"]))}, jf)
    print("tohum", seed, "tamam:", h["epochs_run"], "epoch,", h["stopped_by"], flush=True)
TRS = pd.DataFrame([utils.load_json(LDIR / "models" / f"ae_seed{s}.json") for s in cfg.lofo_seeds])
TRS.to_csv(RUN / "F2_ae_egitim.csv", index=False); TRS'''),
        md("## 2 · Katmanlar: hazırlama, normal-veri kontrolü, host eşlemesi ve değerlendirme (her katman × tohum Drive'a kaydedilir)"),
        code(r'''
import json
SPL = ["benign_train", "benign_val", "benign_cal", "benign_test", "dev_test", "heldout_test"]
for fi, fam in enumerate(FAMS):
    fdir = LDIR / f"katman_{fam}"; fdir.mkdir(exist_ok=True)
    cfg_f = L.fold_config(cfg, fam)
    todo = [s for s in cfg.lofo_seeds if not (RESUME and (fdir / f"seed{s}_{FP}.json").exists())]
    if not todo:
        print(f"[{fam}] tüm tohumlar kayıtlı, atlanıyor"); continue
    if (fdir / "prepared" / "prepared.npz").exists():
        Pf = D.load_prepared(fdir / "prepared")
    else:
        print(f"[{fam}] hazırlanıyor...", flush=True)
        Pf = D.prepare(raw, cfg_f); D.save_prepared(Pf, fdir / "prepared")
        utils.save_json(Pf["report"], fdir / "prepare_report.json")
    assert L.same_benign(Pf, P0), f"{fam}: normal veri ana bölmeden farklı; AE yeniden kullanılamaz"
    hm = fdir / "host_rows.csv.gz"
    if hm.exists():
        ROWS = pd.read_csv(hm, keep_default_na=False); ROWS["split"] = ROWS["split"].replace({"": None})
    else:
        ROWS = R.map_rows(raw, Pf, cfg_f); ROWS.to_csv(hm, index=False)
    ROWS = ROWS[ROWS["split"].isin(["benign_val", "benign_test", "dev_test", "heldout_test"])].reset_index(drop=True)
    for seed in todo:
        ae = tf.keras.models.load_model(LDIR / "models" / f"ae_seed{seed}.keras", compile=False)
        S = {sp: M.ae_score(ae, Pf["X"][sp]) for sp in SPL}
        rf, thr = L.fit_rf(Pf, cfg_f, seed)
        flow = L.flow_level(Pf, S, rf, thr, cfg_f, fam, seed)
        host = L.host_level(ROWS, Pf, S, rf, thr, cfg_f, fam, seed, np.random.default_rng(10_000 + 100 * fi + seed))
        utils.save_json({"flow": flow, "host": host}, fdir / f"seed{seed}_{FP}.json")
        print(f"[{fam}] tohum {seed} tamam: AE ANOMALY {flow['AE_ANOMALY']:.3f} | RF {flow['RF_tek_recall_α']:.3f}", flush=True)
print("tüm katmanlar tamam")'''),
        md("## 3 · Akış düzeyi: her katmanda görülmemiş aile (tohum ortalaması ± std)"),
        code(r'''
FLOW, HOST = [], []
for fam in FAMS:
    for s in cfg.lofo_seeds:
        z = utils.load_json(LDIR / f"katman_{fam}" / f"seed{s}_{FP}.json")
        FLOW.append(z["flow"]); HOST += z["host"]
FLOW, HOST = pd.DataFrame(FLOW), pd.DataFrame(HOST)
FLOW.to_csv(RUN / "F2_akis_tum_tohumlar.csv", index=False); HOST.to_csv(RUN / "F2_host_tum_tohumlar.csv", index=False)
fcols = ["AE_ANOMALY", "AE_UNCERTAIN", "AE_kaçan", "AE_ANOMALY_çakışma_kaçmış", "RF_tek_recall_α", "RF_tek_recall_α+β",
         "AE+Basamak1_recall", "normal_AE_ANOMALY", "normal_RF_FPR_α", "normal_AE+Basamak1_FPR"]
FT = FLOW.groupby("aile", sort=False)[fcols].agg(["mean", "std"]).round(4)
FT.to_csv(RUN / "F2_akis_katman_ozet.csv"); FT'''),
        md("## 4 · Host düzeyi (Basamak 2) ve önceden kaydedilmiş başarı / başarısızlık ölçütleri"),
        code(r'''
rho1 = "karisik_ρ=1.00"
hcols = ["k_yildiz", "normal_haftalik_ort", "normal_haftalik_p95_host", "normal_haftalik_en_kotu_host", "saf_pencere_tespit"] + \
        [c for c in HOST.columns if c.startswith("karisik_")] + ["cikmaz_orani"]
HT = HOST.groupby(["sistem", "W", "F", "aile"], sort=False)[hcols].mean()
HT.to_csv(RUN / "F2_host_katman_ozet.csv")
fm = FLOW.groupby("aile")[["AE_ANOMALY", "RF_tek_recall_α"]].mean()
verdict = []
for (sysn, W, F), g in HOST[HOST["sistem"] == "AE + Basamak 2"].groupby(["sistem", "W", "F"]):
    gm = g.groupby("aile")[[rho1, "normal_haftalik_en_kotu_host"]].mean()
    gm = gm.join(fm)
    gm["azalma_puan"] = 100 * (gm[rho1] - gm["AE_ANOMALY"])          # kaçan+ertelenen akış − host düzeyi kaçan
    gm["bütçe_içinde"] = gm["normal_haftalik_en_kotu_host"] <= cfg.resolution_budget_per_week
    gm["katman_başarılı"] = (gm["azalma_puan"] >= 100 * cfg.lofo_success_points) & gm["bütçe_içinde"]
    gm["benzemeyen_aile"] = gm["RF_tek_recall_α"] < cfg.lofo_unlike_rf_recall
    gm["RF_yetişiyor"] = gm["RF_tek_recall_α"] >= gm[rho1] - cfg.lofo_match_margin
    n_ok = int(gm["katman_başarılı"].sum())
    fail = bool((gm["benzemeyen_aile"] & gm["RF_yetişiyor"]).any())
    verdict.append({"W": W, "F": F, "başarılı_katman": n_ok, "katman": len(gm),
                    "başarı_ölçütü_sağlandı": n_ok >= cfg.lofo_success_folds,
                    "benzemeyen_aileler": ", ".join(gm.index[gm["benzemeyen_aile"]]) or "yok",
                    "başarısızlık_ölçütü_tetiklendi": fail})
    gm.round(4).to_csv(RUN / f"F2_olcut_W{W}_F{F}.csv")
VER = pd.DataFrame(verdict); VER.to_csv(RUN / "F2_on_kayitli_olcutler.csv", index=False); VER'''),
        code(r'''
F0 = max(cfg.resolution_flows_per_day)
fig, axs = plt.subplots(1, len(cfg.resolution_windows), figsize=(4.2 * len(cfg.resolution_windows), 4), sharey=True)
for ax, W in zip(np.atleast_1d(axs), cfg.resolution_windows):
    fams = list(fm.index); x = np.arange(len(fams)); w = 0.2
    ae = FLOW.groupby("aile")["AE_ANOMALY"].mean().reindex(fams)
    aeu = (FLOW.groupby("aile")["AE_ANOMALY"].mean() + FLOW.groupby("aile")["AE_UNCERTAIN"].mean()).reindex(fams)
    rf = FLOW.groupby("aile")["RF_tek_recall_α"].mean().reindex(fams)
    h2 = HOST[(HOST["sistem"] == "AE + Basamak 2") & (HOST["W"] == W) & (HOST["F"] == F0)].groupby("aile")[rho1].mean().reindex(fams)
    for j, (vals, lab, col) in enumerate([(ae, "AE ANOMALY (akış)", "#e34948"), (aeu, "AE ANOMALY+UNCERTAIN (akış)", "#eda100"),
                                          (rf, "yalnız RF (akış)", "#2a78d6"), (h2, f"AE + Basamak 2 (host, ρ=1)", "#1baf7a")]):
        ax.bar(x + (j - 1.5) * w, 100 * vals, w, label=lab, color=col)
    ax.set_xticks(x); ax.set_xticklabels(fams, rotation=45, ha="right", fontsize=8); ax.set_title(f"W = {W}, F = {F0}/gün")
np.atleast_1d(axs)[0].set_ylabel("görülmemiş aile tespiti (%)"); np.atleast_1d(axs)[0].legend(fontsize=7)
fig.suptitle("LOFO: her aile sırayla görülmemiş (tohum 10–19 ortalaması)"); fig.tight_layout(); fig.savefig(RUN / "F2_lofo.png", dpi=150)
print("Sonuçlar:", RUN)'''),
        code(FLUSH),
    ]

    # =========================================================================== F3 / F4 (shared cells)
    RUN_CELL = r'''
for seed in SEEDS:
    f = CACHE / f"seed{seed}_{FP}.json"
    if RESUME and f.exists():
        print("tohum", seed, "Drive'da kayıtlı, atlanıyor (devam modu)"); continue
    print("tohum", seed, "çalışıyor...", flush=True)
    res = PL.run_seed(seed, cfg=cfg, X=X, cats=CAT, build=build, cache_dir=CACHE, fp=FP, resume=RESUME, coll_ho=COLL,
                      **seed_inputs(seed))
    utils.save_json(res, f)
    print("tohum", seed, "tamam (Drive'a kaydedildi)", flush=True)'''
    COLLECT_CELL = r'''
T, DONE = PL.collect(CACHE, SEEDS, FP)
for k, df in T.items(): df.to_csv(RUN / f"{TAG}_{k}_tum_tohumlar.csv", index=False)
print("tamamlanan tohumlar:", DONE)'''
    FL_CELL = r'''
flc = ["istemci_FPR_ort", "istemci_FPR_ağırlıklı", "istemci_FPR_en_kötü", "görülmemiş_ANOMALY", "görülmemiş_UNCERTAIN", "görülmemiş_kaçan",
       "bilinen_ANOMALY", "precision_görülmemiş", "recall_görülmemiş", "f1_görülmemiş", "coverage", "selective_risk", "atlanan_istemci"]
FLS = FZ.seed_summary(T["fl"], ["model", "senaryo", "kalibrasyon"], flc, cfg.bootstrap_repeats); FLS.to_csv(RUN / f"{TAG}_fl_ozet.csv", index=False)
EGS = T["egitim"].groupby(["senaryo", "protokol"])[["rounds_run", "epochs_equivalent", "local_steps_mean", "comm_MB", "val_loss_best"]].agg(["mean", "std"]).round(3)
EGS.to_csv(RUN / f"{TAG}_fl_egitim_ozet.csv"); display(EGS)
T["fl"]["konfig"] = T["fl"]["model"] + " | " + T["fl"]["senaryo"] + " | " + T["fl"]["kalibrasyon"]
pairs = [(f"Merkezi (yakınsama) | {s} | havuz skor", f"FedAvg · {p} | {s} | havuz skor") for s in cfg.fl_scenarios for p in cfg.fl_final_protocols]
FLT = pd.concat([FZ.paired_tests(T["fl"], "konfig", pairs, mt) for mt in ["görülmemiş_ANOMALY", "bilinen_ANOMALY", "selective_risk"]])
FLT.to_csv(RUN / f"{TAG}_fl_testler.csv", index=False)
FLS[FLS["metrik"].isin(["görülmemiş_ANOMALY", "bilinen_ANOMALY", "istemci_FPR_ağırlıklı", "istemci_FPR_en_kötü", "selective_risk"])].pivot_table(
    index=["model", "senaryo", "kalibrasyon"], columns="metrik", values="ortalama").round(4)'''
    TINY_CELL = r'''
TYS = FZ.seed_summary(T["tiny"], ["model"], ["parametre", "tflite_fp32_KB", "tflite_int8_KB", "tahmini_RAM_KB_int8",
                                             "gecikme_fp32_µs_colab", "gecikme_int8_µs_colab", "Spearman_FP32_INT8"], cfg.bootstrap_repeats)
I8S = FZ.seed_summary(T["int8"], ["model", "kural"], ["normal_FPR", "fark_α", "normal_UNCERTAIN", "görülmemiş_ANOMALY", "görülmemiş_UNCERTAIN"], cfg.bootstrap_repeats)
TYS.to_csv(RUN / f"{TAG}_tinyml_ozet.csv", index=False); I8S.to_csv(RUN / f"{TAG}_int8_gecerlilik_ozet.csv", index=False)
display(TYS.pivot_table(index="model", columns="metrik", values="ortalama").round(3))
I8S.pivot_table(index=["model", "kural"], columns="metrik", values="ortalama").round(4)'''
    ROB_CELL = r'''
rob = T["rob"].groupby(["tohum", "bozulma", "düzey", "politika"], as_index=False).mean(numeric_only=True)   # önce 3 tekrarın ortalaması
RBS = FZ.seed_summary(rob, ["bozulma", "düzey", "politika"], ["normal_FPR", "normal_UNCERTAIN", "görülmemiş_ANOMALY",
                      "görülmemiş_ANOMALY+UNCERTAIN", "bilinen_ANOMALY", "f1_görülmemiş", "coverage", "selective_risk", "selective_risk_π=%1"], cfg.bootstrap_repeats)
RBS.to_csv(RUN / f"{TAG}_saglamlik_ozet.csv", index=False)
RBS.pivot_table(index=["bozulma", "düzey", "politika"], columns="metrik", values="ortalama").round(4)'''
    ABL_CELL = r'''
abc = [c for c in T["abl"].columns if c not in ("yapılandırma", "tohum")]
ABS = FZ.seed_summary(T["abl"], ["yapılandırma"], abc, cfg.bootstrap_repeats); ABS.to_csv(RUN / f"{TAG}_ablasyon_ozet.csv", index=False)
pairs = [("A3 · AE + seçici", "A2 · AE (ikili)"), ("A3 · AE + seçici", "A3q · INT8 AE + seçici (merkezi)")]
for p in cfg.fl_final_protocols:
    pairs += [("A3 · AE + seçici", f"A5 · Federe AE + seçici · {p}"),
              (f"A5 · Federe AE + seçici · {p}", f"A4 · Federe AE (ikili) · {p}"),
              (f"A5 · Federe AE + seçici · {p}", f"A6 · INT8 Federe AE + seçici · {p}")]
ABT = pd.concat([FZ.paired_tests(T["abl"], "yapılandırma", pairs, mt)
                 for mt in ["görülmemiş_ANOMALY", "bilinen_ANOMALY", "selective_risk", "selective_risk_π=%1", "normal_FPR"]])
ABT.to_csv(RUN / f"{TAG}_ablasyon_testler.csv", index=False)
show = ["normal_FPR", "normal_UNCERTAIN", "bilinen_ANOMALY", "görülmemiş_ANOMALY", "görülmemiş_UNCERTAIN", "görülmemiş_kaçan", "recall_görülmemiş",
        "precision_görülmemiş", "precision_görülmemiş_π=%1", "f1_görülmemiş", "coverage", "selective_risk", "selective_risk_π=%1"]
display(ABS.pivot_table(index="yapılandırma", columns="metrik", values="ortalama", sort=False).reindex(columns=show).round(4))
display(ABS.pivot_table(index="yapılandırma", columns="metrik", values="std", sort=False).reindex(columns=show).round(4))
ABT.round(4)'''
    RC_CELL = r'''
RCS = T["rc"].groupby(["model", "yaygınlık", "kapsama"], sort=False)["seçici_risk"].agg(["mean", "std", "count"]).reset_index()
RCS.to_csv(RUN / f"{TAG}_risk_kapsama_ozet.csv", index=False)
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, prev in zip(axs, ["test kümesi", "π=%1"]):
    for name, g in RCS[RCS["yaygınlık"] == prev].groupby("model", sort=False):
        g = g.dropna(subset=["mean"])
        ax.plot(g["kapsama"], g["mean"], marker="o", ms=3, lw=1.2, label=name)
    ax.set_xlabel("kapsama (otomatik karar payı)"); ax.set_ylabel("seçici risk"); ax.set_title(f"Risk–kapsama · {prev} · {len(DONE)} tohum ortalaması")
axs[1].set_yscale("log"); axs[0].legend(fontsize=6)
fig.tight_layout(); fig.savefig(RUN / f"{TAG}_risk_kapsama.png", dpi=150)
RCS[RCS["yaygınlık"] == "test kümesi"].pivot_table(index="model", columns="kapsama", values="mean", sort=False).round(4)'''
    ABL_FIG_CELL = r'''
m_ = ABS[ABS["metrik"].isin(["görülmemiş_ANOMALY", "görülmemiş_UNCERTAIN"])].pivot_table(index="yapılandırma", columns="metrik", values="ortalama", sort=False)
s_ = ABS[ABS["metrik"].isin(["görülmemiş_ANOMALY", "görülmemiş_UNCERTAIN"])].pivot_table(index="yapılandırma", columns="metrik", values="std", sort=False)
fig, ax = plt.subplots(figsize=(9, 4.6)); y = np.arange(len(m_))
ax.barh(y, 100 * m_["görülmemiş_ANOMALY"], xerr=100 * s_["görülmemiş_ANOMALY"], color="#e34948", label="ANOMALY")
ax.barh(y, 100 * m_["görülmemiş_UNCERTAIN"], left=100 * m_["görülmemiş_ANOMALY"], color="#eda100", label="UNCERTAIN")
ax.set_yticks(y); ax.set_yticklabels(m_.index, fontsize=7); ax.invert_yaxis(); ax.set_xlim(0, 100)
ax.set_xlabel("görülmemiş saldırılar (%) — ortalama ± std"); ax.set_title(f"Ablasyon, {len(DONE)} tohum"); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(RUN / f"{TAG}_ablasyon.png", dpi=150)
utils.save_json({"tohumlar": DONE, "protokoller": cfg.fl_final_protocols, "parmak_izi": FP, "öznitelik_sayısı": int(X["benign_train"].shape[1]),
                 "not": "Gecikme Colab CPU'sunda ölçüldü; mikrodenetleyici değeri değildir. GA yalnız eğitim tohumu değişkenliğini yansıtır."},
                RUN / f"{TAG}_ozet.json")
print("Sonuçlar:", RUN)'''
    COMMON = [
        md("## Çalıştırma (her FL modeli ve her tohum Drive'a kaydedilir; oturum kapanırsa kaldığı yerden devam eder)"),
        code(RUN_CELL),
        md("## Toplama: tüm tohumlar"),
        code(COLLECT_CELL),
        md("### Aşama 5–6 · FL (tohumlar üzerinden ortalama; testler eşleştirilmiş Wilcoxon + Holm)\n"
           "`istemci_FPR_en_kötü` çok küçük bir istemciden gelebilir; bu yüzden istemci boyutuyla ağırlıklı oran da verilir. "
           "`atlanan_istemci`: verisi olmadığı için değerlendirilemeyen istemci sayısı (non-IID bölmelerde olabilir)."),
        code(FL_CELL),
        code("FLT.round(4)"),
        md("### Aşama 7 · TinyML (gecikme Colab CPU'sunda; mikrodenetleyici ölçümü değildir)"),
        code(TINY_CELL),
        md("### Aşama 8 · Sağlamlık (merkezi AE): gürültü, eksik öznitelik, bozuk öznitelik\n"
           "`düzey`: gürültüde standart sapma, eksik öznitelikte eksik payı, bozuk öznitelikte bozulan öznitelik sayısı "
           "(seçilen özniteliklerin değerleri örnekler arasında karıştırılır). Her satır 3 tekrarın, sonra tohumların ortalamasıdır."),
        code(ROB_CELL),
        md("### Aşama 9 · Ablasyon A1–A6: tüm metrikler (ilk tablo ortalama, ikinci tablo standart sapma, üçüncü testler)\n"
           "A3q = merkezi AE'nin INT8 sürümü; INT8 etkisini FL etkisinden ayırmak için eklendi."),
        code(ABL_CELL),
        md("### Madde 5 · Risk–kapsama eğrileri: tüm modeller (α sabit, β taranır)\n"
           "Her modelin eğrisi sabit kapsama düzeylerinde okunur ve tohumlar üzerinden ortalanır. Bir modelin ulaşamadığı "
           "kapsama düzeyi boş bırakılır. π = %1 paneli saldırının nadir olduğu senaryodur (yeniden ağırlıklandırma)."),
        code(RC_CELL),
        code(ABL_FIG_CELL),
        code(FLUSH),
    ]

    # =========================================================================== F3
    NB["F3_asama5_9_on_tohum.ipynb"] = [
        md(r"""
# F3 · Madde 1 (ve Madde 5) — Aşama 5–9'un 10 tohumla tekrarı, tüm performans metrikleri
**Profesörün notu:** *Aşama 5–9 deneylerini 10 farklı tohumla tekrarlayıp tüm performans metriklerini raporla.*
*Risk–Coverage, FPR, recall ve selective risk sonuçlarını tüm modeller için tamamla.*

Her tohum (0–9) için, 02 defterinde **aynı tohumla eğitilen** merkezi AE kullanılır:
* **Aşama 5–6 (FL):** istemci bölmeleri tohuma göre çekilir; protokoller `cfg.fl_final_protocols` (F1 teşhisinden sonra
  sabitlenir; varsayılan: ara dönem protokolü + yakınsama/Adam korunur + FedProx); yalnız yerel eğitim; iki kalibrasyon.
* **Aşama 7 (TinyML):** merkezi AE ve FedAvg-IID modelleri → TFLite FP32/INT8; boyut, kaba RAM tahmini, gecikme
  (**Colab CPU'sunda; mikrodenetleyici ölçümü değildir**), FP32↔INT8 skor uyumu, eşik geçerliliği.
* **Aşama 8 (sağlamlık):** gürültü, eksik öznitelik ve bozuk öznitelik (plandaki üç senaryo), 3 tekrar, devralınan eşik /
  yeniden kalibrasyon; her deneyde F1, FPR, görülmemiş recall, kapsama ve seçici risk.
* **Aşama 9 (ablasyon):** A1–A6; her yapılandırma için FPR, recall, precision, F1, ANOMALY/UNCERTAIN/kaçan, kapsama,
  seçici risk (test kümesi ve π = %1); her model için risk–kapsama eğrisi.
* İstemci bazında sonuçlar (`fl_istemci`) ve FP32/INT8 model dosyaları (`artifacts/final_f3/tflite/`) da kaydedilir.

Raporlama: ortalama, standart sapma, tohumlar üzerinden bootstrap %95 GA, eşleştirilmiş Wilcoxon + Holm.
Güven aralıkları yalnız **eğitim tohumu** değişkenliğini yansıtır (veri bölmesi sabittir).
"""),
        code(SETUP),
        code(r'''
import tensorflow as tf
from trustids import data as D, models as M, conformal as C, evaluation as E, fl as FL, tiny as TY, final as FZ, pipeline as PL
print(TY.self_test())                       # TFLite bu ortamda çalışıyor mu? (saatler süren eğitimden ÖNCE kontrol)
P = D.load_prepared(ART / "prepared"); X = P["X"]; FNAMES = P["preprocessor"].feature_names_
CHOSEN = utils.load_json(ART / "ae_selection.json")["chosen"]; spec = cfg.ae_variants[CHOSEN]
TAG = "F3"
CACHE = ART / "final_f3"; CACHE.mkdir(exist_ok=True)
FP = utils.fingerprint(cfg, ["fl_clients", "fl_scenarios", "fl_orig_rounds", "fl_local_epochs", "fl_fedprox_mu",
                             "fl_final_protocols", "alpha", "beta"])
RUN = utils.new_run_dir(Path(PROJECT_DIR) / cfg.runs_dir, "final_F3_asama5_9")
utils.save_json(utils.environment_info(), RUN / "environment.json"); cfg.save(RUN / "config_used.json")
d_in = X["benign_train"].shape[1]
def build(): return M.build_autoencoder(d_in, spec["hidden"], spec["dropout"], cfg.learning_rate)
CAT = {sp: FL.service_categories(X[sp], FNAMES) for sp in ["benign_train", "benign_val", "benign_cal", "benign_test"]}
COLL = P["collision"]["heldout_test"]
SEEDS = [s for s in cfg.train_seeds if (ART / "models" / f"ae_seed{s}.keras").exists() and E.scores_path(cfg, s).exists()]
missing = sorted(set(cfg.train_seeds) - set(SEEDS))
if missing: print("UYARI: bu tohumların merkezi modeli yok, önce 02 defterini tamamlayın:", missing)
def seed_inputs(seed):
    S = E.load_scores(cfg, seed)
    pick = lambda m: {sp: S[(m, sp)] for sp in PL.EV}
    return dict(central=tf.keras.models.load_model(ART / "models" / f"ae_seed{seed}.keras", compile=False),
                base=pick("ae"), iforest=pick("iforest"), latent=pick("latent"))
print("öznitelik:", d_in, "| tohumlar:", SEEDS, "| protokoller:", cfg.fl_final_protocols, "| parmak izi:", FP, "| sonuç:", RUN)'''),
    ] + COMMON

    # =========================================================================== F4
    NB["F4_cihaz_modeli.ipynb"] = [
        md(r"""
# F4 · Madde 4 — 21 öznitelikli cihaz modeli: federe öğrenme ve INT8 deneyleri (10 tohum)
**Profesörün notu:** *21 öznitelikli cihaz modelini federated ve INT8 deneylerine de dahil et.*

Cihaz öznitelik kümesi yalnız bir IoT düğümünün kendisinin sayabileceği 10 akış sayacından oluşur (protokol, süre, bayt,
paket, bağlantı durumu); DNS/SSL/HTTP alanları yoktur. Bu defter F3 ile **aynı kodu** (`trustids/pipeline.py`) cihaz
öznitelikleriyle çalıştırır: FL (aynı protokoller), FP32/INT8, sağlamlık, ablasyon ve risk–kapsama.

* **Aynı satırlar:** cihaz öznitelikleri ana bölmenin aynı satırlarından hesaplanır (02 defterindeki öznitelik karşılaştırmasıyla
  aynı yöntem); merkezi cihaz modeli 02 defterinde her tohum için eğitilip kaydedilen modeldir. Defter, yeniden hesaplanan
  skorların 02'de kaydedilen skorlarla aynı olduğunu **doğrular**.
* **Aynı istemciler:** non-IID bölme anahtarı (service) cihaz kümesinde yoktur; istemci ataması ana öznitelik kümesindeki
  service kategorisinden alınır. Böylece F3 ile F4 aynı istemcileri karşılaştırır.
* **Sınırlılık:** tekrar temizliği 53 öznitelikli vektörler üzerinde yapıldı; 21 öznitelikte bazı test vektörleri bir eğitim
  vektörüyle birebir aynı olabilir. Bu pay aşağıda raporlanır. A1 (Isolation Forest) bu kümede eğitilmediği için tabloda yoktur.
* Son bölüm, F3 sonuçları varsa **cihaz − tümü** farkını eşleştirilmiş testlerle verir.
"""),
        code(SETUP),
        code(r'''
import tensorflow as tf
from trustids import data as D, models as M, conformal as C, evaluation as E, fl as FL, tiny as TY, final as FZ, pipeline as PL
print(TY.self_test())
raw = D.load_raw(cfg.data_path, cfg)
P = D.load_prepared(ART / "prepared"); FNAMES = P["preprocessor"].feature_names_
CHOSEN = utils.load_json(ART / "ae_selection.json")["chosen"]; spec = cfg.ae_variants[CHOSEN]
cols_d = D.feature_columns(raw, cfg, feature_set="device")
pre_d = D.Preprocessor(max_card=cfg.max_categorical_cardinality, corr_threshold=cfg.correlation_threshold)
pre_d.fit(raw.loc[P["index"]["benign_train"]], cols_d)
X = {k: pre_d.transform(raw.loc[v]) for k, v in P["index"].items()}          # ana bölmenin aynı satırları
TAG = "F4"
CACHE = ART / "final_f4"; CACHE.mkdir(exist_ok=True)
FP = utils.fingerprint(cfg, ["fl_clients", "fl_scenarios", "fl_orig_rounds", "fl_local_epochs", "fl_fedprox_mu",
                             "fl_final_protocols", "alpha", "beta"])
RUN = utils.new_run_dir(Path(PROJECT_DIR) / cfg.runs_dir, "final_F4_cihaz_modeli")
utils.save_json(utils.environment_info(), RUN / "environment.json"); cfg.save(RUN / "config_used.json")
d_in = X["benign_train"].shape[1]
def build(): return M.build_autoencoder(d_in, spec["hidden"], spec["dropout"], cfg.learning_rate)
CAT = {sp: FL.service_categories(P["X"][sp], FNAMES) for sp in ["benign_train", "benign_val", "benign_cal", "benign_test"]}
COLL = P["collision"]["heldout_test"]
h_train = set(D._row_hashes(X["benign_train"]))
SEEN = {k: float(np.mean([h in h_train for h in D._row_hashes(X[k])])) for k in ["benign_cal", "benign_test", "dev_test", "heldout_test"]}
utils.save_json({"cihaz_sütunları": cols_d, "öznitelik": pre_d.feature_names_, "eğitimde_birebir_görülmüş_pay": SEEN}, RUN / "F4_cihaz_oznitelikleri.json")
SEEDS = [s for s in cfg.train_seeds if (ART / "models" / f"device_seed{s}.keras").exists()]
missing = sorted(set(cfg.train_seeds) - set(SEEDS))
if missing: print("UYARI: bu tohumların cihaz modeli yok, önce 02 defterini tamamlayın:", missing)
def seed_inputs(seed):
    m = tf.keras.models.load_model(ART / "models" / f"device_seed{seed}.keras", compile=False)
    assert m.input_shape[-1] == d_in, "kayıtlı cihaz modelinin girdi boyutu farklı"
    base = {sp: M.ae_score(m, X[sp]) for sp in PL.EV}
    f = ART / "scores" / f"device_seed{seed}.npz"
    if f.exists():                                   # 02 defterinde kaydedilen skorlarla aynı mı?
        old = np.load(f)["benign_test"]
        assert np.allclose(old, base["benign_test"], rtol=1e-3, atol=1e-7), "cihaz skorları 02 defterindekilerle uyuşmuyor"
    return dict(central=m, base=base, iforest=None, latent=None)
print("cihaz sütunları:", cols_d); print("model özniteliği:", d_in, "| eğitimde birebir görülmüş vektör payı:", {k: round(v, 4) for k, v in SEEN.items()})
print("tohumlar:", SEEDS, "| protokoller:", cfg.fl_final_protocols, "| parmak izi:", FP, "| sonuç:", RUN)'''),
    ] + COMMON[:-1] + [
        md("### Cihaz (21) − tümü (53): aynı tohum, aynı yapılandırma (F3 sonuçları varsa)"),
        code(r'''
T3, DONE3 = PL.collect(ART / "final_f3", cfg.train_seeds, FP)
if len(T3["abl"]) == 0:
    print("F3 sonuçları bulunamadı (aynı ayarlarla); karşılaştırma için önce F3 defterini çalıştırın.")
else:
    both = pd.concat([T["abl"].assign(küme="cihaz"), T3["abl"].assign(küme="tümü")])
    both["k"] = both["yapılandırma"] + " | " + both["küme"]
    names = [n for n in T["abl"]["yapılandırma"].unique() if n in set(T3["abl"]["yapılandırma"])]
    CMP = pd.concat([FZ.paired_tests(both, "k", [(f"{n} | cihaz", f"{n} | tümü") for n in names], mt)
                     for mt in ["görülmemiş_ANOMALY", "bilinen_ANOMALY", "normal_FPR", "selective_risk", "selective_risk_π=%1"]])
    CMP.to_csv(RUN / "F4_cihaz_eksi_tumu_testler.csv", index=False)
    ty = pd.concat([T["tiny"].assign(küme="cihaz"), T3["tiny"].assign(küme="tümü")])
    TYC = ty.groupby(["model", "küme"])[["parametre", "tflite_int8_KB", "tahmini_RAM_KB_int8", "gecikme_int8_µs_colab"]].mean().round(3)
    TYC.to_csv(RUN / "F4_kaynak_karsilastirma.csv"); display(TYC)
    display(CMP.round(4))'''),
        code(FLUSH),
    ]

    # =========================================================================== F5
    NB["F5_seyrek_saldiri.ipynb"] = [
        md(r"""
# F5 · Madde 6 — Host düzeyindeki güven mekanizması seyrek saldırılarda ne yapıyor?
**Profesörün notu:** *Host düzeyindeki güven mekanizmasını seyrek saldırılar açısından da değerlendir.*

Host sayacı, bir hostun W akışlık penceresinde p ≤ α+β olan akışları sayar ve sayı k\*'a ulaşınca hostu yükseltir.
Az sayıda kötü akışı çok sayıda normal akışın arasına yayan bir saldırgan k\*'ın altında kalabilir. Bu defter mekanizmayı
**değiştirmez, ölçer**:

* pencere başına saldırı payı ρ ∈ {%1, %2, %5, %10, %25, %50, %100}; pencerede round(ρ·W) saldırı akışı bulunur
  (hiç saldırı akışı içermeyen birleşimler atlanır ve tabloda yer almaz);
* W ∈ {20, 50, 100, 200, 500} (kalibrasyon için yeterli normal akışı olan host varsa);
* aynı operasyonel bütçe (cihaz başına haftada ≤ 1 yanlış yükseltme), k\* yine normal-doğrulama pencerelerinden;
* karşılaştırma: yalnız ANOMALY akışlarını sayan sayaç (kendi k\* değeriyle);
* tohumlar 0–9 (02 defterinde eğitilen modeller), 9 saldırı ailesinin tümü.

**Dürüstlük notları:** Sürüm B'de zaman damgası yoktur; pencereler rastgele çekilir (**simülasyon**). "Günlük tespit"
sütunu pencerelerin bağımsız olduğu varsayımıyla hesaplanan bir yaklaşımdır. Bu analiz önceden kaydedilmedi; **keşif
amaçlıdır**. ρ → 0 iken tespit oranı yanlış yükseltme oranına yaklaşır; tablolar bu yüzden ikisini birlikte verir.
"""),
        code(SETUP),
        code(r'''
from trustids import data as D, conformal as C, evaluation as E, resolution as R, sparse as SPR
P = D.load_prepared(ART / "prepared")
SDIR = ART / "sparse"; SDIR.mkdir(exist_ok=True)
FP = utils.fingerprint(cfg, ["sparse_rho", "sparse_windows", "sparse_mixed_windows", "resolution_flows_per_day",
                             "resolution_budget_per_week", "resolution_cal_windows", "resolution_eval_windows", "alpha", "beta"])
RUN = utils.new_run_dir(Path(PROJECT_DIR) / cfg.runs_dir, "final_F5_seyrek_saldiri")
utils.save_json(utils.environment_info(), RUN / "environment.json"); cfg.save(RUN / "config_used.json")
HOSTMAP = ART / "resolution" / "host_rows.csv.gz"
if HOSTMAP.exists():
    ROWS = pd.read_csv(HOSTMAP, keep_default_na=False); ROWS["split"] = ROWS["split"].replace({"": None})
else:
    raw = D.load_raw(cfg.data_path, cfg); ROWS = R.map_rows(raw, P, cfg)
    HOSTMAP.parent.mkdir(exist_ok=True); ROWS.to_csv(HOSTMAP, index=False)
ROWS = ROWS[ROWS["split"].isin(["benign_val", "benign_test", "dev_test", "heldout_test"])].reset_index(drop=True)
SEEDS = E.available_seeds(cfg)
hv = ROWS[ROWS["split"] == "benign_val"].groupby("host").size()
print("tohumlar:", SEEDS, "| ρ:", cfg.sparse_rho, "| W:", cfg.sparse_windows)
print("normal-doğrulama: W akışa ulaşan host sayısı:", {W: int((hv >= W).sum()) for W in cfg.sparse_windows})'''),
        code(r'''
for seed in SEEDS:
    f = SDIR / f"seed{seed}_{FP}.csv"
    if RESUME and f.exists():
        print("tohum", seed, "Drive'da kayıtlı, atlanıyor (devam modu)"); continue
    S = E.load_scores(cfg, seed)
    Sae = {sp: S[("ae", sp)] for sp in ["benign_cal", "benign_val", "benign_test", "dev_test", "heldout_test"]}
    pd.DataFrame(SPR.evaluate_seed(ROWS, Sae, cfg, seed, np.random.default_rng(50_000 + seed))).to_csv(f, index=False)
    print("tohum", seed, "tamam (Drive'a kaydedildi)", flush=True)
RES = pd.concat([pd.read_csv(SDIR / f"seed{s}_{FP}.csv") for s in SEEDS], ignore_index=True)
RES.to_csv(RUN / "F5_tum_tohumlar.csv", index=False)
SKIP = RES[RES["durum"] != "tamam"][["W", "durum"]].drop_duplicates()
MAIN = RES[RES["durum"] == "tamam"].copy()
print("atlanan pencere boyutları:", SKIP.to_dict(orient="records") if len(SKIP) else "yok")'''),
        md("## Normal trafikte maliyet (her W, F ve sayaç için; hedef haftada ≤ 1)"),
        code(r'''
COST = (MAIN.drop_duplicates(["tohum", "W", "F", "sayaç"]).groupby(["sayaç", "W", "F"])
            [["k_yildiz", "α_w", "normal_yanlis_yukseltme_pencere", "normal_haftalik_ort", "normal_haftalik_en_kotu_host"]].agg(["mean", "std"]).round(4))
COST.columns = [f"{a}_{b}" for a, b in COST.columns]; COST.to_csv(RUN / "F5_normal_maliyet.csv"); COST'''),
        md("## Tespit: saldırı payı ρ'ya göre pencere düzeyinde tespit oranı (önce tohum içinde aile ortalaması, sonra tohum ortalaması ± std)"),
        code(r'''
g1 = MAIN.groupby(["tohum", "sayaç", "W", "F", "grup", "ρ"], as_index=False)[["pencere_tespit", "gunluk_tespit_bagimsiz_pencere", "saldiri_akisi_pencerede"]].mean()
DET = g1.groupby(["sayaç", "W", "F", "grup", "ρ"])[["pencere_tespit", "gunluk_tespit_bagimsiz_pencere", "saldiri_akisi_pencerede"]].agg(["mean", "std"]).round(4)
DET.columns = [f"{a}_{b}" for a, b in DET.columns]; DET.to_csv(RUN / "F5_tespit_grup.csv")
FAMT = MAIN.groupby(["sayaç", "W", "F", "grup", "aile", "ρ"])[["pencere_tespit", "akis_ANOMALY", "akis_isaretli"]].mean().round(4)
FAMT.to_csv(RUN / "F5_tespit_aile.csv")
F0 = max(cfg.resolution_flows_per_day)
DET.xs(("ANOMALY+UNCERTAIN", F0), level=("sayaç", "F"))["pencere_tespit_mean"].unstack("ρ")'''),
        code(r'''
DET.xs(("ANOMALY+UNCERTAIN", F0), level=("sayaç", "F"))["gunluk_tespit_bagimsiz_pencere_mean"].unstack("ρ")'''),
        code(r'''
Ws = sorted(MAIN["W"].unique())
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
for ax, grp in zip(axs, ["görülmemiş", "bilinen"]):
    for W in Ws:
        for cname, ls in [("ANOMALY+UNCERTAIN", "-"), ("yalnız ANOMALY", ":")]:
            q = g1[(g1["sayaç"] == cname) & (g1["W"] == W) & (g1["F"] == F0) & (g1["grup"] == grp)].groupby("ρ")["pencere_tespit"].mean()
            if len(q): ax.plot(q.index, 100 * q.values, ls, marker="o", ms=3, lw=1.2, label=f"W={W} · {cname}")
    ax.set_xscale("log"); ax.set_xlabel("pencere başına saldırı payı ρ (log)"); ax.set_title(f"{grp} aileler · F = {F0}/gün")
axs[0].set_ylabel("pencere düzeyinde tespit (%)"); axs[1].legend(fontsize=6, ncol=2)
fig.suptitle("Seyrek saldırılarda host sayacı (simülasyon; tohum ortalaması)"); fig.tight_layout(); fig.savefig(RUN / "F5_seyrek_saldiri.png", dpi=150)
print("Sonuçlar:", RUN)'''),
        code(FLUSH),
    ]
