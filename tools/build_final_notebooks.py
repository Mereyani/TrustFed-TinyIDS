"""FINAL AŞAMA defterlerini üretir (Aşama 1-4 yeniden + F1 FL teşhisi, F2 LOFO, F3 Aşama 5-9 on tohum). Dil: Türkçe.

Ara dönem klasörüne (TrustFed-TinyIDS/) dokunmaz; çıktı: Final_Asama/TrustFed-TinyIDS-Final/notebooks/.

Çalıştırma:  python tools/build_final_notebooks.py
Defterleri elle düzenlemek de mümkündür; bu betik yalnızca tutarlılığı korur.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "TrustFed-TinyIDS-Final" / "notebooks"

SETUP = r'''# ---- Kurulum (her defterde aynı): Drive'ı bağla, ortak kodu içe aktar ----
import os, sys
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
PROJECT_DIR = os.environ.get("TRUSTIDS_PROJECT", "/content/drive/MyDrive/TrustFed-TinyIDS-Final")
QUICK = os.environ.get("TRUSTIDS_QUICK", "0") == "1"   # hızlı mod YALNIZCA kodu test etmek içindir
# Devam modu: Colab oturumu kapanırsa, Drive'a kaydedilmiş tohumlar/adımlar atlanır ve kalan yerden devam edilir.
# Her şeyi baştan hesaplamak için: os.environ["TRUSTIDS_RESUME"] = "0"
RESUME = os.environ.get("TRUSTIDS_RESUME", "1") == "1"
sys.path.insert(0, PROJECT_DIR)

from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from trustids.config import Config
from trustids import utils

# Veri kümesi seçimi: varsayılan TON_IoT; ikinci veri kümesi için TRUSTIDS_CONFIG=edge_iiotset.json
CONFIG_NAME = os.environ.get("TRUSTIDS_CONFIG", "default.json")
CFG_PATH = Path(PROJECT_DIR) / "configs" / CONFIG_NAME
if CONFIG_NAME != "default.json" and not CFG_PATH.exists():
    raise FileNotFoundError(f"{CFG_PATH} bulunamadı: configs/ klasörünü de Drive'a yükleyin.")
cfg = Config.load(CFG_PATH) if CFG_PATH.exists() else Config(project_dir=PROJECT_DIR)
cfg.project_dir = PROJECT_DIR
if QUICK:
    cfg.train_seeds, cfg.validity_resplits, cfg.epochs = cfg.train_seeds[:2], 30, 15
    cfg.random_control_repeats, cfg.bootstrap_repeats = 10, 200
    cfg.lofo_seeds, cfg.fl_orig_rounds = cfg.lofo_seeds[:2], 3
    cfg.resolution_cal_windows, cfg.resolution_eval_windows = 600, 600
cfg.check()
ART = cfg.artifacts
FIG = Path(PROJECT_DIR) / cfg.figures_dir; FIG.mkdir(exist_ok=True)
pd.set_option("display.width", 160); pd.set_option("display.max_columns", 30)
print("Proje klasörü:", PROJECT_DIR, "| hızlı mod:", QUICK, "| devam modu:", RESUME)
print("Drive'da kayıtlı ilerleme:", utils.progress(cfg))'''

FLUSH = r'''# Colab: Drive'a yazılan tüm dosyaların kaydedildiğinden emin ol (oturumu kapatmadan önce mutlaka çalıştırın)
print("Kaydedilen ilerleme:", utils.progress(cfg))
if IN_COLAB:
    drive.flush_and_unmount()
    print("Drive kaydedildi ve ayrıldı. Sonraki defter Drive'ı yeniden bağlar.")'''


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


def notebook(cells):
    return {"cells": cells, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}, "colab": {"provenance": []}},
        "nbformat": 4, "nbformat_minor": 5}


NB = {}

# =============================================================================== 00
NB["00_setup_and_config.ipynb"] = [
    md("""
# 00 · Kurulum ve yapılandırma
**TrustFed-TinyIDS** · FİNAL AŞAMA (Aşama 1–4 Colab'da yeniden; ardından F1, F2, F3)

Bu defter Google Drive proje klasörünü hazırlar, tüm defterlerin kullandığı **tek yapılandırma dosyasını**
yazar ve TON_IoT veri dosyasını doğrular.

**Drive klasör yapısı** (`/content/drive/MyDrive/TrustFed-TinyIDS-Final/`):
```
trustids/        ortak kod (proje klasöründen yükleyin)
notebooks/       bu defterler
data/            train_test_network.csv  (siz ekleyeceksiniz)
configs/         default.json            (burada yazılır)
artifacts/       hazırlanmış veri, skorlar, modeller (01–04 tarafından yazılır)
figures/, runs/  şekiller ve sonuç tabloları
```
"""),
    code(SETUP),
    md("## 1 · Klasörleri oluştur ve yapılandırmayı kaydet\n"
       "Önceden kaydedilmiş (pre-registered) tüm seçimler — görülmeyecek saldırı aileleri, α, β, bölmeler, "
       "rastgele tohumlar — `configs/default.json` içindedir. **Test sonuçlarına baktıktan sonra değiştirilmez.**"),
    code(r'''
for d in ["data", "artifacts", "runs", "configs", "figures"]:
    (Path(PROJECT_DIR) / d).mkdir(parents=True, exist_ok=True)
import json, datetime
from dataclasses import asdict
current = {**asdict(Config()), **({} if CONFIG_NAME == "default.json" else asdict(cfg))}
current["project_dir"] = PROJECT_DIR
if not CFG_PATH.exists():
    Config(**current).save(CFG_PATH)      # hızlı-mod değişiklikleri değil, önceden kaydedilmiş değerler yazılır
    print("Yapılandırma yazıldı:", CFG_PATH)
else:
    old = json.loads(CFG_PATH.read_text(encoding="utf-8"))
    diff = {k: (old.get(k), v) for k, v in current.items() if old.get(k) != v}
    if diff and CONFIG_NAME == "default.json":
        # eski bir Colab çalıştırmasından kalan yapılandırma, yeni kodla sessizce karışmasın
        backup = CFG_PATH.with_name(f"default.{datetime.datetime.now():%Y%m%d-%H%M%S}.bak.json")
        backup.write_text(json.dumps(old, indent=2), encoding="utf-8")
        Config(**current).save(CFG_PATH)
        cfg = Config.load(CFG_PATH)
        print("Drive'daki yapılandırma koddan farklıydı; yedeklendi ve güncellendi:", backup.name)
        for k, (a, b) in diff.items():
            print(f"  {k}: {a} -> {b}")
    else:
        print("Yapılandırma güncel:", CFG_PATH)
print("Görülmeyecek (held-out) aileler — son değerlendirmeye kadar hiç kullanılmaz:", cfg.heldout_families)
print("Geliştirme (bilinen) aileleri:", cfg.dev_families)
print("alpha =", cfg.alpha, "| beta =", cfg.beta)'''),
    md("""
## 2 · TON_IoT ağ dosyasını edinin
Öneri metni **sürüm A**'yı birincil kabul eder (UNSW resmî `train_test_network.csv`, 461.043 satır, `ts` sütunu var).

1. Resmî TON_IoT sayfasından indirin (UNSW Canberra, *Train_Test_datasets → Train_Test_Network_dataset*).
   SharePoint bağlantısı genellikle `wget` ile çalışmaz; tarayıcıdan indirin.
2. `MyDrive/TrustFed-TinyIDS-Final/data/train_test_network.csv` konumuna yükleyin.

Yalnızca ayna (mirror) kopyası varsa (ör. Hugging Face `codymlewis/TON_IoT_network`, **sürüm B**: 211.043 satır,
`ts` yok), onu kullanın; ancak raporda bu belirtilmeli ve zamansal analiz (S4) çıkarılmalıdır.
"""),
    code(r'''
from trustids import data as D
path = cfg.data_path
assert path.exists(), f"Veri dosyası bulunamadı: {path}. Önce Drive'a yükleyin (yukarıdaki talimatlar)."
raw = D.load_raw(path, cfg)
info = {**D.detect_version(raw), "sha256": utils.sha256_file(path), "file": str(path)}
utils.save_json(info, ART / "data_file_info.json")
info'''),
    code(r'''
env = utils.environment_info()
utils.save_json(env, ART / "environment.json")
env'''),
    code(FLUSH),
]

# =============================================================================== 01
NB["01_data_preparation.ipynb"] = [
    md("""
# 01 · Aşama 1 — TON_IoT veri hazırlama ve görülmemiş saldırı protokolü
**Amaç (Aşama 1):** normal trafik davranışını öğrenebilen ve daha önce görülmemiş saldırılar üzerinde
değerlendirilebilen bir veri yapısı oluşturmak.

Bu defter sırasıyla:
1. dosyayı yükler ve denetler (sınıf sayıları, eksik değerler, tekrarlar, etiket tutarlılığı);
2. kimlik / **veri sızıntısı** sütunlarını (`ts`, IP'ler, portlar) ve serbest metin alanlarını çıkarır;
3. **küresel tekrar temizliği** yapar (önce girdi sütunları, sonra nihai model öznitelik vektörü);
   aynı vektör hem normal hem saldırı etiketiyle görülürse **her etiketten bir kopya** tutulur ve işaretlenir;
4. rastgele bölme: normal 50/10/20/20 (eğitim/doğrulama/kalibrasyon/test); bilinen saldırılar 50/50
   (geliştirme-doğrulama / geliştirme-test); görülmeyecek aileler → yalnızca test;
5. kodlayıcı, öznitelik filtresi ve ölçekleyiciyi **yalnızca normal-eğitim** verisinde öğrenir;
6. tekrarlanabilirlik için her şeyi kaydeder (indeksler, tekrar sayıları, ön işlemci);
7. **IoT cihazında hesaplanabilen** öznitelik kümesini ayrıca hazırlar;
8. sızıntı kontrolü: aynı hattı kimlik sütunları *dahil* çalıştırır (yalnızca kontrol amaçlı).
"""),
    code(SETUP),
    code(r'''
from trustids import data as D
raw = D.load_raw(cfg.data_path, cfg)
print(D.detect_version(raw))
audit = D.audit(raw)
pd.Series(audit["class_counts"]).rename("satır sayısı").to_frame()'''),
    code(r'''
print("label/type uyuşmazlığı:", audit.get("label_type_mismatch"))
print("tüm sütunlarda birebir tekrar eden satır:", audit["exact_duplicate_rows"])
pd.Series(audit["dash_missing_per_column"]).rename("'-' değerleri").sort_values(ascending=False).to_frame().head(20)'''),
    md("## Hazırlama: tekrar temizliği, bölmeler, ön işleme (yalnızca normal-eğitim üzerinde)"),
    code(r'''
bundle = D.prepare(raw, cfg, include_leakage=False)
rep = bundle["report"]
print("Girdi sütunları:", len(rep["input_columns"]), "| kodlama/filtre sonrası model öznitelikleri:", rep["n_features"])
DEDUP = pd.DataFrame(rep["dedup"]["per_type"]).T.rename(columns={
    "before": "satır", "after_stage1": "kimliksiz_tekil_kayıt", "after": "tekil_model_vektörü"})
DEDUP["tekil_vektör_%"] = (100 * DEDUP["tekil_model_vektörü"] / DEDUP["satır"]).round(1)
print("Kimlik sütunları DAHİL birebir tekrar eden satır oranı: %.1f%%" % (100 * audit["exact_duplicate_rows"] / len(raw)))
DEDUP'''),
    md("""
### Tekrar temizliğinin üç düzeyi
1. **satır**: ham dosyadaki kayıt sayısı;
2. **kimliksiz tekil kayıt**: `ts`/IP/port gibi kimlik sütunları çıkarıldıktan sonra farklı kalan kayıtlar
   (bu kayıtlar ancak kimlik sütunlarıyla ayırt edilebiliyordu);
3. **tekil model vektörü**: modelin gördüğü girdi vektörü düzeyinde tekil örnekler (ör. `dst_ip_bytes` ≈ `dst_bytes`
   korelasyon filtresiyle çıkarıldığında yalnızca bu sütunda farklılaşan kayıtlar birleşir).

Dikkat: birçok satır **farklı akışlardır** ancak kimlik sütunları olmadan birbirinden ayırt edilemez. Model bu kayıtları
aynı örnek olarak görür; bu nedenle tüm sonuçlar tekil model vektörleri üzerinde raporlanır, satır ağırlıklı sonuçlar
ikincil olarak verilir.
"""),
    code(r'''
fig, ax = plt.subplots(figsize=(8.5, 3.8))
x = np.arange(len(DEDUP))
ax.bar(x - 0.27, DEDUP["satır"], 0.27, label="satır")
ax.bar(x, DEDUP["kimliksiz_tekil_kayıt"], 0.27, label="kimliksiz tekil kayıt")
ax.bar(x + 0.27, DEDUP["tekil_model_vektörü"], 0.27, label="tekil model vektörü")
ax.set_xticks(x); ax.set_xticklabels(DEDUP.index, rotation=30, ha="right")
ax.set_yscale("log"); ax.set_ylabel("örnek sayısı (log)")
ax.set_title("TON_IoT: sınıf başına satır ve tekil örnek sayıları"); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "01_dedup_before_after.png", dpi=150)'''),
    code(r'''
print({k: v for k, v in rep["dedup"].items() if k != "per_type"})
print("Bölmeler arasında paylaşılan aynı vektörler. Beklenen: normal bölmeler arasında ~0; "
      "normal–saldırı örtüşmeleri işaretlenmiş çakışmalardır (her etiketten bir kopya tutulur):")
print(rep["residual_cross_split_identical_vectors"])
pd.DataFrame(rep["split_by_type"]).fillna(0).astype(int)'''),
    code(r'''
n_cal = rep["split_sizes"]["benign_cal"]
rule = D.calibration_rule(n_cal, cfg.alpha, cfg.alpha_grid)
print("n_cal kuralı ((n_cal+1)·α ≥ 20):", rule)
mitm_n = int(np.sum(bundle["types"]["heldout_test"] == "mitm"))
rep["mitm_unique_vectors"] = mitm_n
rep["mitm_in_macro_average"] = mitm_n >= 200
print("mitm benzersiz vektör:", mitm_n, "-> makro ortalamaya dahil:", mitm_n >= 200)
rep["calibration_rule"] = rule
pd.Series(rep["dropped_columns"]).rename("çıkarılma nedeni").to_frame()'''),
    code(r'''
out = ART / "prepared"
D.save_prepared(bundle, out)
utils.save_json(rep, out / "prepare_report.json")
utils.save_json({"features": bundle["preprocessor"].feature_names_,
                 "groups": bundle["preprocessor"].groups_}, out / "features.json")
print("Kaydedildi:", out)'''),
    md("## IoT cihazında hesaplanabilen öznitelik kümesi (Aşama 1 gereksinimi)\n"
       "Yalnızca akış sayaçları (DNS/SSL/HTTP alanları derin paket incelemesi gerektirdiği için hariç). "
       "Aşama 2'de karşılaştırma olarak, Aşama 7'de (TinyML) aday girdi olarak kullanılır."),
    code(r'''
dev = D.prepare(raw, cfg, feature_set="device")
D.save_prepared(dev, ART / "prepared_device")
utils.save_json(dev["report"], ART / "prepared_device" / "prepare_report.json")
print("Cihaz öznitelik kümesi:", dev["report"]["input_columns"], "->", dev["report"]["n_features"], "model özniteliği")'''),
    md("## Sızıntı kontrolü: aynı hat `ts`, IP ve port sütunları *dahil*\n"
       "Yalnızca kimlik sütunlarının sonuçları şişirip şişirmediğini göstermek içindir; ana sonuçlarda **kullanılmaz**."),
    code(r'''
RUN_LEAKAGE_CHECK = True
if RUN_LEAKAGE_CHECK:
    leak = D.prepare(raw, cfg, include_leakage=True)
    D.save_prepared(leak, ART / "prepared_leakage")
    utils.save_json(leak["report"], ART / "prepared_leakage" / "prepare_report.json")
    print("Sızıntı varyantı öznitelik sayısı:", leak["report"]["n_features"])'''),
    md("## Aşama 1 denetim özeti (profesöre gönderilecek)"),
    code(r'''
info = utils.load_json(ART / "data_file_info.json") if (ART / "data_file_info.json").exists() else D.detect_version(raw)
AUDIT = {
    "dosya": {k: info.get(k) for k in ["version", "rows", "columns", "has_ts", "sha256"]},
    "tekrar_temizligi": {k: v for k, v in rep["dedup"].items() if k != "per_type"},
    "sinif_basina_once_sonra": rep["dedup"]["per_type"],
    "bolme_boyutlari": rep["split_sizes"],
    "n_cal_kurali": rule,
    "mitm_benzersiz": mitm_n,
    "model_oznitelik_sayisi": rep["n_features"],
    "cihaz_oznitelikleri": dev["report"]["input_columns"],
    "cikarilan_sutunlar": rep["dropped_columns"],
}
utils.save_json(AUDIT, FIG / "01_faz1_denetim_ozeti.json")
pd.json_normalize(AUDIT["tekrar_temizligi"]).T.rename(columns={0: "değer"})'''),
    md("""
## Aşama 1 çıktıları
* `artifacts/prepared/` — öznitelik matrisleri, etiketler, bölme indeksleri, tekrar sayıları, ön işlemci
* `artifacts/prepared/prepare_report.json` — denetim, tekrar temizliği, bölme boyutları, çıkarılan sütunlar, n_cal kuralı
* `figures/01_dedup_before_after.png`, `figures/01_faz1_denetim_ozeti.json`
"""),
    code(FLUSH),
]

# =============================================================================== 02
NB["02_baseline_models.ipynb"] = [
    md("""
# 02 · Aşama 2 — Temel anomali tespit modelleri
| Model | Görevi |
|---|---|
| Isolation Forest | referans anomali tespit modeli |
| Hafif Autoencoder (32-16-**8**-16-32) | temel hafif sinir ağı |
| AE gizil uzay Mahalanobis skoru | alternatif skor (Aşama 4'te B5 karşılaştırması) |

Tüm modeller **yalnızca normal-eğitim** verisiyle eğitilir. Erken durdurma **normal-doğrulama** yeniden oluşturma
kaybına göre yapılır. Bilinen saldırılar (geliştirme-doğrulama) yalnızca tek bir amaçla kullanılır: 2–3 AE boyutunu
karşılaştırmak. Görülmeyecek ailelere dokunulmaz. Skorlar her tohum için önbelleğe alınır; Aşama 3–4 yeniden eğitim yapmaz.
"""),
    code(SETUP),
    code(r'''
import tensorflow as tf
from trustids import data as D, models as M, evaluation as E, metrics as MT, conformal as C
P = D.load_prepared(ART / "prepared")
X, T = P["X"], P["types"]
print({k: v.shape for k, v in X.items()})
print("TensorFlow", tf.__version__, "| GPU:", tf.config.list_physical_devices("GPU"))'''),
    md("## AE boyut karşılaştırması (tohum 0) — bilinen saldırıların tek kullanımı\n"
       "Önceden kaydedilmiş kural: profesörün mimarisi `ae_32_16_8` korunur; başka bir boyut ancak geliştirme-doğrulama "
       "PR-AUC değerinde 0,01'den fazla daha iyiyse seçilir."),
    code(r'''
CKPT = utils.checkpoint_ok(ART, cfg, RESUME)       # aynı ayarlarla üretilmiş ara sonuçlar yeniden kullanılır
if CKPT and (ART / "ae_selection.json").exists():
    SEL = utils.load_json(ART / "ae_selection.json"); CHOSEN = SEL["chosen"]
    print("Kayıtlı AE seçimi kullanılıyor (devam modu):", CHOSEN)
    cmp = pd.DataFrame(SEL["comparison"]).T
else:
  utils.set_seed(cfg.train_seeds[0])
  rows = {}
  for name, spec in cfg.ae_variants.items():
    print(f"{name} eğitiliyor (en fazla {cfg.epochs} epoch; birkaç dakika sürebilir)...", flush=True)
    m = M.build_autoencoder(X["benign_train"].shape[1], spec["hidden"], spec["dropout"], cfg.learning_rate)
    h = M.train_autoencoder(m, X["benign_train"], X["benign_val"], cfg.epochs, cfg.batch_size, cfg.patience,
                           conv_window=cfg.conv_window, conv_rel_tol=cfg.conv_rel_tol)
    s_val = np.concatenate([M.ae_score(m, X["benign_val"]), M.ae_score(m, X["dev_val"])])
    y_val = np.r_[np.zeros(len(X["benign_val"])), np.ones(len(X["dev_val"]))]
    rows[name] = {"parametre": M.count_parameters(m), "en_iyi_dogrulama_kaybi": float(min(h["val_loss"])),
                  "epoch": len(h["val_loss"]), "gelistirme_dogrulama_pr_auc": MT.binary_metrics(y_val, s_val, s_val > np.inf)["pr_auc"]}
    print(f"  {name} tamam: {len(h['val_loss'])} epoch, durma nedeni: {h['stopped_by']}", flush=True)
  cmp = pd.DataFrame(rows).T
  best = cmp["gelistirme_dogrulama_pr_auc"].idxmax()
  CHOSEN = best if cmp.loc[best, "gelistirme_dogrulama_pr_auc"] > cmp.loc[cfg.ae_default, "gelistirme_dogrulama_pr_auc"] + 0.01 else cfg.ae_default
  utils.save_json({"comparison": cmp.to_dict(orient="index"), "chosen": CHOSEN}, ART / "ae_selection.json")
print("Seçilen AE:", CHOSEN); cmp'''),
    md("## Her tohum için eğitim ve tüm bölmelerin skorlarının önbelleğe alınması"),
    code(r'''
spec = cfg.ae_variants[CHOSEN]
(ART / "training").mkdir(exist_ok=True)
for seed in cfg.train_seeds:
    if CKPT and E.scores_path(cfg, seed).exists() and (ART / "training" / f"seed{seed}.json").exists():
        print("tohum", seed, "Drive'da kayıtlı, atlanıyor (devam modu)"); continue
    utils.set_seed(seed)
    print("tohum", seed, "eğitiliyor...", flush=True)
    scores = {}
    ifo = M.fit_iforest(X["benign_train"], cfg.iforest_estimators, seed)
    ae = M.build_autoencoder(X["benign_train"].shape[1], spec["hidden"], spec["dropout"], cfg.learning_rate)
    hist = M.train_autoencoder(ae, X["benign_train"], X["benign_val"], cfg.epochs, cfg.batch_size, cfg.patience,
                           conv_window=cfg.conv_window, conv_rel_tol=cfg.conv_rel_tol)
    lat = M.LatentMahalanobis(ae).fit(X["benign_train"])
    for split, Xs in X.items():
        scores[("iforest", split)] = M.iforest_score(ifo, Xs)
        scores[("ae", split)] = M.ae_score(ae, Xs)
        scores[("latent", split)] = lat.score(Xs)
    E.save_scores(cfg, seed, scores)
    # final aşama: HER tohumun modeli kaydedilir (Aşama 5–9 on tohumla bu modelleri kullanır)
    (ART / "models").mkdir(exist_ok=True)
    ae.save(str(ART / "models" / f"ae_seed{seed}.keras"))
    utils.save_json(hist, ART / "models" / f"ae_seed{seed}_history.json")
    utils.save_json({"tohum": seed, "ae_parametre": M.count_parameters(ae), "epoch": len(hist["val_loss"]),
                     "durma_nedeni": hist["stopped_by"], "en_iyi_epoch": hist["best_epoch"],
                     "en_iyi_dogrulama_kaybi": float(min(hist["val_loss"]))}, ART / "training" / f"seed{seed}.json")
    print("tohum", seed, "tamam (Drive'a kaydedildi)")
summary = pd.DataFrame([utils.load_json(ART / "training" / f"seed{s}.json") for s in cfg.train_seeds]); utils.save_json(summary.to_dict(orient="records"), ART / "training_summary.json")
print("Durma nedenleri:", summary["durma_nedeni"].value_counts().to_dict(), "| üst sınır:", cfg.epochs, "epoch")
summary'''),
    md("## Yeniden oluşturma hatası dağılımları (tohum 0)"),
    code(r'''
from trustids import plotting as PL
S = E.load_scores(cfg, cfg.train_seeds[0])
groups = {"normal (test)": S[("ae", "benign_test")],
          "bilinen saldırılar (gel.-test)": S[("ae", "dev_test")],
          "görülmemiş saldırılar": S[("ae", "heldout_test")]}
PL.score_distributions(groups, "Gruba göre AE yeniden oluşturma hatası (tohum 0)", FIG / "02_ae_score_distributions.png");
for fam in cfg.heldout_families:
    v = S[("ae", "heldout_test")][T["heldout_test"] == fam]
    print(f"{fam:12s} n={len(v):6d}  medyan hata={np.median(v) if len(v) else float('nan'):.4g}")'''),
    md("## İlk tespit sonuçları: α düzeyinde ikili kural (B2), profesörün metrikleri\n"
       "Eşik = normal-kalibrasyondan konformal τ_H (α düzeyinde). Bilinen ve görülmemiş saldırılar için ayrı raporlanır."),
    code(r'''
rows = []
for model in ["ae", "iforest", "latent"]:
    tau = C.thresholds(S[(model, "benign_cal")], cfg.alpha, cfg.beta)["tau_H"]
    for part in ["dev_test", "heldout_test"]:
        s = np.r_[S[(model, "benign_test")], S[(model, part)]]
        y = np.r_[np.zeros(len(S[(model, "benign_test")])), np.ones(len(S[(model, part)]))]
        r = MT.binary_metrics(y, s, s > tau)
        rows.append({"model": model, "saldırılar": "bilinen" if part == "dev_test" else "görülmemiş", **r})
b2 = pd.DataFrame(rows).round(4); b2.to_csv(FIG / "02_binary_B2_seed0.csv", index=False); b2'''),
    md("## Profesörün Aşama 2 metrikleri: IF ve AE, 10 tohum (ortalama ± standart sapma)"),
    code(r'''
rows = []
for seed in cfg.train_seeds:
    Ss = E.load_scores(cfg, seed)
    for model in ["ae", "iforest", "latent"]:
        tau = C.thresholds(Ss[(model, "benign_cal")], cfg.alpha, cfg.beta)["tau_H"]
        for part in ["dev_test", "heldout_test"]:
            s = np.r_[Ss[(model, "benign_test")], Ss[(model, part)]]
            y = np.r_[np.zeros(len(Ss[(model, "benign_test")])), np.ones(len(Ss[(model, part)]))]
            rows.append({"tohum": seed, "model": model, "saldırılar": "bilinen" if part == "dev_test" else "görülmemiş",
                         **MT.binary_metrics(y, s, s > tau)})
B2ALL = pd.DataFrame(rows); B2ALL.to_csv(FIG / "02_binary_B2_10seeds.csv", index=False)
B2ALL.groupby(["model", "saldırılar"])[["precision", "recall", "f1", "fpr", "pr_auc", "roc_auc"]].agg(["mean", "std"]).round(4)'''),
    md("## Tohum 0 karşılaştırmaları: cihaz öznitelikleri ve sızıntı kontrolü\n"
       "Aynı AE ve aynı kural; (a) yalnızca cihazda hesaplanabilen akış sayaçları, (b) `ts`/IP/port *dahil* öznitelikler. "
       "(b) yalnızca kontroldür: büyük bir sıçrama, kimlik sütunlarının etiketi sızdırdığı anlamına gelir."),
    code(r'''
rows = []
VAR_DONE = CKPT and (FIG / "02_device_and_leakage_check.csv").exists()
if VAR_DONE:
    print("Kayıtlı tablo kullanılıyor (devam modu)")
for variant in ([] if VAR_DONE else ["prepared_device", "prepared_leakage"]):
    if not (ART / variant / "prepared.npz").exists():
        continue
    Pv = D.load_prepared(ART / variant); Xv = Pv["X"]
    utils.set_seed(cfg.train_seeds[0])
    m = M.build_autoencoder(Xv["benign_train"].shape[1], spec["hidden"], spec["dropout"], cfg.learning_rate)
    M.train_autoencoder(m, Xv["benign_train"], Xv["benign_val"], cfg.epochs, cfg.batch_size, cfg.patience,
                           conv_window=cfg.conv_window, conv_rel_tol=cfg.conv_rel_tol)
    tau = C.thresholds(M.ae_score(m, Xv["benign_cal"]), cfg.alpha, cfg.beta)["tau_H"]
    for part in ["dev_test", "heldout_test"]:
        s = np.r_[M.ae_score(m, Xv["benign_test"]), M.ae_score(m, Xv[part])]
        y = np.r_[np.zeros(len(Xv["benign_test"])), np.ones(len(Xv[part]))]
        rows.append({"varyant": variant, "öznitelik": Xv["benign_train"].shape[1],
                     "saldırılar": "bilinen" if part == "dev_test" else "görülmemiş", **MT.binary_metrics(y, s, s > tau)})
VAR = pd.read_csv(FIG / "02_device_and_leakage_check.csv") if VAR_DONE else pd.DataFrame(rows).round(4)
VAR.to_csv(FIG / "02_device_and_leakage_check.csv", index=False); VAR'''),
    md("""
## Öznitelik kümeleri: adil karşılaştırma (10 tohum, aynı satırlar, eşitlenmiş yanlış alarm)
Tek tohumlu karşılaştırmada modeller farklı yanlış alarm oranlarında ve farklı tekrar-temizlenmiş kümelerde çalışıyordu.
Burada üç öznitelik kümesi **ana bölmenin aynı satırları** üzerinde eğitilir, kalibre edilir ve test edilir:

* **tümü** — ana model (önbellekteki skorlar);
* **cihaz** — yalnızca IoT cihazında hesaplanabilen akış sayaçları;
* **sızıntı** — kimlik sütunları (`ts`/IP/port) *dahil* (yalnızca kontrol; ana sonuçlarda kullanılmaz).

Karşılaştırma (a) aynı konformal α düzeyinde ve (b) normal testte **eşitlenmiş %1 yanlış alarm oranında** yapılır.
(b)'deki eşik normal-test üzerinden seçilir; bu bir **analiz yapısıdır** (etiket kullanır), dağıtılabilir bir kural değildir.
Ayrıca cihaz kümesinde, daha az öznitelik nedeniyle bazı test vektörleri bir eğitim vektörüyle aynı olabilir; bu pay
raporlanır ve bu vektörler çıkarılarak da recall hesaplanır.
"""),
    code(r'''
raw = D.load_raw(cfg.data_path, cfg)
VARIANTS = {"cihaz": D.feature_columns(raw, cfg, feature_set="device"),
            "sızıntı": D.feature_columns(raw, cfg, include_leakage=True)}
XV = {}
for name, cols_v in VARIANTS.items():
    pre_v = D.Preprocessor(max_card=cfg.max_categorical_cardinality if name != "sızıntı" else 100,
                           corr_threshold=cfg.correlation_threshold)
    pre_v.fit(raw.loc[P["index"]["benign_train"]], cols_v)
    XV[name] = {k: pre_v.transform(raw.loc[v]) for k, v in P["index"].items()}
    print(name, "öznitelik:", XV[name]["benign_train"].shape[1])

# cihaz kümesinde eğitim vektörüyle birebir aynı olan test vektörleri
h_train = set(D._row_hashes(XV["cihaz"]["benign_train"]))
SEEN = {k: np.array([h in h_train for h in D._row_hashes(XV["cihaz"][k])]) for k in ["benign_test", "dev_test", "heldout_test"]}
print("cihaz: eğitimde birebir görülmüş test vektörü payı:", {k: round(float(v.mean()), 4) for k, v in SEEN.items()})

def recall_at_fpr(s_benign, s_attack, fpr):
    thr = np.quantile(s_benign, 1 - fpr)
    return float(np.mean(s_attack > thr))

(ART / "featcmp").mkdir(exist_ok=True)
for seed in cfg.train_seeds:
    if CKPT and (ART / "featcmp" / f"seed{seed}.json").exists():
        print("tohum", seed, "Drive'da kayıtlı, atlanıyor (devam modu)"); continue
    rows = []
    sf = E.load_scores(cfg, seed)
    SC = {"tümü": {k: sf[("ae", k)] for k in ["benign_cal", "benign_test", "dev_test", "heldout_test"]}}
    for name in VARIANTS:
        utils.set_seed(seed)
        Xv = XV[name]
        m = M.build_autoencoder(Xv["benign_train"].shape[1], spec["hidden"], spec["dropout"], cfg.learning_rate)
        M.train_autoencoder(m, Xv["benign_train"], Xv["benign_val"], cfg.epochs, cfg.batch_size, cfg.patience,
                           conv_window=cfg.conv_window, conv_rel_tol=cfg.conv_rel_tol)
        SC[name] = {k: M.ae_score(m, Xv[k]) for k in SC["tümü"]}
        if name == "cihaz":   # final aşama: cihaz modeli de kaydedilir (madde 4: FL ve INT8 deneyleri için)
            m.save(str(ART / "models" / f"device_seed{seed}.keras"))
    np.savez_compressed(ART / "scores" / f"device_seed{seed}.npz", **SC["cihaz"])
    for name, sc in SC.items():
        tau = C.thresholds(sc["benign_cal"], cfg.alpha, cfg.beta)["tau_H"]
        for part in ["dev_test", "heldout_test"]:
            row = {"tohum": seed, "öznitelik": name, "saldırılar": "bilinen" if part == "dev_test" else "görülmemiş",
                   "fpr_alpha": float(np.mean(sc["benign_test"] > tau)), "recall_alpha": float(np.mean(sc[part] > tau)),
                   "recall_fpr_1%": recall_at_fpr(sc["benign_test"], sc[part], 0.01)}
            if name == "cihaz":
                nb, na = ~SEEN["benign_test"], ~SEEN[part]
                row["recall_fpr_1%_görülmemiş_vektörler"] = recall_at_fpr(sc["benign_test"][nb], sc[part][na], 0.01)
            rows.append(row)
    utils.save_json(rows, ART / "featcmp" / f"seed{seed}.json")
    print("tohum", seed, "tamam (Drive'a kaydedildi)")
FEATCMP = pd.DataFrame([r for s in cfg.train_seeds for r in utils.load_json(ART / "featcmp" / f"seed{s}.json")]); FEATCMP.to_csv(FIG / "02_feature_sets_10seeds.csv", index=False)
FEATCMP.groupby(["saldırılar", "öznitelik"])[["fpr_alpha", "recall_alpha", "recall_fpr_1%"]].agg(["mean", "std"]).round(4)'''),
    code(r'''
from scipy import stats as _st
res = []
for other in ["cihaz", "sızıntı"]:
    for part in ["bilinen", "görülmemiş"]:
        a = FEATCMP[(FEATCMP["saldırılar"] == part) & (FEATCMP["öznitelik"] == other)].sort_values("tohum")["recall_fpr_1%"].to_numpy()
        b = FEATCMP[(FEATCMP["saldırılar"] == part) & (FEATCMP["öznitelik"] == "tümü")].sort_values("tohum")["recall_fpr_1%"].to_numpy()
        p = _st.wilcoxon(a, b).pvalue if not np.allclose(a, b) else 1.0
        res.append({"karşılaştırma": f"{other} - tümü", "saldırılar": part, "ortalama_fark": float(np.mean(a - b)),
                    "kazanan_tohum": int(np.sum(a > b)), "wilcoxon_p": float(p)})
RES = pd.DataFrame(res).sort_values("wilcoxon_p").reset_index(drop=True)
m = len(RES); RES["p_holm"] = np.maximum.accumulate([min(1.0, (m - i) * p) for i, p in enumerate(RES["wilcoxon_p"])])
RES.to_csv(FIG / "02_feature_sets_tests.csv", index=False); RES.round(4)'''),
    md("""
## Eğitim süresine duyarlılık (tohum 0): epoch sayısına göre recall
Eğitim süresi sonuçları belirgin biçimde etkileyebildiği için, yakınsama kuralına ek olarak recall'un epoch sayısıyla
nasıl değiştiği raporlanır (yalnızca normal veriyle eğitim; eşikler her noktada konformal α ile yeniden hesaplanır).
"""),
    code(r'''
utils.set_seed(cfg.train_seeds[0])
m = M.build_autoencoder(X["benign_train"].shape[1], spec["hidden"], spec["dropout"], cfg.learning_rate)
rows, done = [], 0
EPC_DONE = CKPT and (FIG / "02_recall_vs_epochs_seed0.csv").exists()
for target in ([] if EPC_DONE else [25, 50, 100, 200, 400, 800, 1000, 1500]):
    if QUICK and target > 50:
        break
    m.fit(X["benign_train"], X["benign_train"], epochs=target - done, batch_size=cfg.batch_size, shuffle=True, verbose=0)
    done = target
    tau = C.thresholds(M.ae_score(m, X["benign_cal"]), cfg.alpha, cfg.beta)["tau_H"]
    rows.append({"epoch": target, "val_loss": float(np.mean(M.ae_score(m, X["benign_val"]))),
                 "recall_bilinen": float(np.mean(M.ae_score(m, X["dev_test"]) > tau)),
                 "recall_görülmemiş": float(np.mean(M.ae_score(m, X["heldout_test"]) > tau)),
                 "normal_fpr": float(np.mean(M.ae_score(m, X["benign_test"]) > tau))})
if EPC_DONE:
    print("Kayıtlı epoch eğrisi kullanılıyor (devam modu)"); EPC = pd.read_csv(FIG / "02_recall_vs_epochs_seed0.csv")
else:
    EPC = pd.DataFrame(rows); EPC.to_csv(FIG / "02_recall_vs_epochs_seed0.csv", index=False)
fig, ax = plt.subplots(figsize=(6, 3.5))
ax.plot(EPC["epoch"], EPC["recall_görülmemiş"], "o-", label="görülmemiş recall")
ax.plot(EPC["epoch"], EPC["recall_bilinen"], "s-", label="bilinen recall")
ax.set_xscale("log"); ax.set_xlabel("epoch"); ax.set_ylabel("recall (α düzeyinde)"); ax.legend()
ax.set_title("Eğitim süresine göre recall (tohum 0)"); fig.tight_layout(); fig.savefig(FIG / "02_recall_vs_epochs.png", dpi=150)
EPC.round(4)'''),
    code(FLUSH),
]

# =============================================================================== 03
NB["03_trust_aware_decision.ipynb"] = [
    md(r"""
# 03 · Aşama 3 — Güvenilirlik farkındalıklı karar mekanizması
$$
d(x)=\begin{cases}\text{NORMAL} & p(x) > \alpha+\beta \\ \text{UNCERTAIN} & \alpha < p(x)\le \alpha+\beta \\ \text{ANOMALY} & p(x)\le\alpha\end{cases}
\qquad p(x)=\frac{1+\#\{i\in\text{kal}: s_i\ge s(x)\}}{n_{kal}+1}
$$
Bu, profesörün iki eşikli kuralının uygulanışıdır: $\tau_H,\tau_L$ normal-kalibrasyon skorlarının sıra istatistikleridir.
Tek fark sınır kuralıdır: burada ANOMALY için $s(x) > \tau_H$ kullanılır (plandaki $s(x)\ge\tau_H$ yerine); böylece eşik
kuralı p-değeri kuralıyla eşitlikler dahil **birebir eşdeğer** olur (`tests/test_conformal.py`).

**Garanti edilen** (kalibrasyon çekimine göre marjinal; normal test ve kalibrasyon örnekleri değiştirilebilir ise):
$P(\text{ANOMALY}\mid\text{normal})\le\alpha$ ve $P(\text{UNCERTAIN}\mid\text{normal})\le\beta+\tfrac{1}{n+1}$.
Garanti, **tekrar temizliği sonrası benzersiz vektörler** için geçerlidir.

**Garanti edilmeyen:** saldırılar hakkında hiçbir şey. $p(x)$ bir **olasılık değildir** ($P(\text{saldırı}\mid x)$ değil);
bu yüzden güvenilirlik burada ve Aşama 4'te **deneysel** olarak sınanır.
"""),
    code(SETUP),
    code(r'''
from trustids import data as D, conformal as C, metrics as MT, evaluation as E, plotting as PL
P = D.load_prepared(ART / "prepared")
SEEDS = E.available_seeds(cfg); print("skorları önbellekte olan tohumlar:", SEEDS)
S0 = E.load_scores(cfg, SEEDS[0])
GROUPS = E.family_groups(cfg)
# Aşama 1'de önceden kaydedilmiş n_cal kuralını uygula: (n_cal + 1) * alpha >= 20
rule = utils.load_json(ART / "prepared" / "prepare_report.json")["calibration_rule"]
if not rule["rule_satisfied"]:
    print("n_cal kuralı sağlanmadı -> alpha", cfg.alpha, "değerinden", rule["alpha_effective"], "değerine yükseltildi (raporlayın)")
    cfg.alpha = rule["alpha_effective"]
print("n_cal =", rule["n_cal"], "| kullanılan alpha =", cfg.alpha, "| beta =", cfg.beta)'''),
    md("## Eşikler, eşit skorlar ve kararlar (tohum 0)\n"
       "Eşit skor (tie) içeren modellerde (Isolation Forest, ileride INT8) **rastgeleleştirilmiş p-değerleri** kullanılır; "
       "rastgelelik tohumla sabitlenir, böylece sonuçlar tekrarlanabilir."),
    code(r'''
rows, DEC0 = [], {}
for model in E.MODELS:
    ev = E.eval_set(P, S0, model)
    ties = C.tie_report(ev["cal"])
    p = C.pvalues(ev["cal"], ev["scores"], seed=SEEDS[0], model=model)
    d = C.decide(p, cfg.alpha, cfg.beta)
    DEC0[model] = {"p": p, "d": d, "ev": ev}
    th = C.thresholds(ev["cal"], cfg.alpha, cfg.beta)
    rows.append({"model": model, **th, "farklı_kal_skoru": ties["distinct"], "eşitlik_oranı": ties["tie_mass"],
                 "rastgele_p": model in C.ALWAYS_RANDOMIZED_MODELS or ties["use_randomized"]})
pd.DataFrame(rows)'''),
    code(r'''
tab = MT.per_family_table(DEC0["ae"]["ev"]["types"], DEC0["ae"]["d"], GROUPS)
tab.to_csv(FIG / "03_ae_per_family_seed0.csv", index=False)
PL.family_bars(tab, "AE + konformal üç yönlü karar, aile bazında (tohum 0)", FIG / "03_ae_family_decisions.png")
tab.round(4)'''),
    md("## B3 temel çizgisi: eğitim hatalarından sezgisel eşikler (μ + kσ)\n"
       "Yaygın uygulama; eğitim hataları görülmemiş normal örneklerin hatalarından küçük olduğu için iyimserdir."),
    code(r'''
ev = DEC0["ae"]["ev"]
h = C.heuristic_thresholds(ev["train"], cfg.heuristic_k[0], cfg.heuristic_k[1])
d_b3 = C.decide_by_thresholds(ev["scores"], h["tau_L"], h["tau_H"])
print(h)
b = ~ev["y_attack"]
print("normal ANOMALY oranı   B3 = %.4f | konformal = %.4f (bütçe alpha = %.3f)" %
      (np.mean(d_b3[b] == C.ANOMALY), np.mean(DEC0["ae"]["d"][b] == C.ANOMALY), cfg.alpha))
print("normal UNCERTAIN oranı B3 = %.4f | konformal = %.4f (bütçe beta = %.3f)" %
      (np.mean(d_b3[b] == C.UNCERTAIN), np.mean(DEC0["ae"]["d"][b] == C.UNCERTAIN), cfg.beta))'''),
    md("""
## E1 — Kural bütçelerini karşılıyor mu? (önceden kaydedilmiş karar kuralı)
Model sabit; normal-kalibrasyon ∪ normal-test R kez yeniden bölünür. Yöntem geçerli olsa bile tek tek bölmelerin
yaklaşık yarısında oran bütçeyi aşar; bu nedenle kural şudur: (a) ortalama ≤ bütçe + 2·SE,
(b) dağılım teorik Beta-Binom yasasıyla uyumlu (histogram + QQ), (c) teorik %95 yüzdeliğin üstünde kalan pay ≤ %10.

**Not:** Sabit bir havuzun rastgele yeniden bölünmesinde E1 yapı gereği sağlanır; burada esas olarak **uygulamanın
doğruluğunu** sınar. Asıl geçerlilik soruları (FL, INT8, gürültü, zaman) sonraki aşamalardadır.
"""),
    code(r'''
val_rows, KEEP = [], {}
for seed in SEEDS:
    S = E.load_scores(cfg, seed)
    for model in E.MODELS:
        pool = np.r_[S[(model, "benign_cal")], S[(model, "benign_test")]]
        n_cal = len(S[(model, "benign_cal")])
        ties = model in C.ALWAYS_RANDOMIZED_MODELS or C.tie_report(S[(model, "benign_cal")])["use_randomized"]
        note = "rastgeleleştirilmiş p" if ties else "deterministik p"
        res = C.validity_resplits(pool, n_cal, cfg.alpha, cfg.beta, cfg.validity_resplits, seed, model=model)
        a = MT.validity_summary(res["fpr"], n_cal, res["n_test"], cfg.alpha)
        u = MT.validity_summary(res["uncertain"], n_cal, res["n_test"], cfg.alpha + cfg.beta, lower=cfg.alpha)
        val_rows.append({"seed": seed, "model": model, "decision": "ANOMALY", **a, "note": note})
        val_rows.append({"seed": seed, "model": model, "decision": "UNCERTAIN", **u, "note": note})
        if seed == SEEDS[0] and model == "ae":
            KEEP = {"res": res, "n_cal": n_cal}
VAL = pd.DataFrame(val_rows); VAL.to_csv(FIG / "03_validity_E1.csv", index=False)
VAL.groupby(["model", "decision"])[["budget", "mean", "share_above_theory_q95", "rule_a_mean_ok", "rule_c_ok"]].mean().round(4)'''),
    code(r'''
res, n_cal = KEEP["res"], KEEP["n_cal"]
bbA, _ = MT.theory_betabinom(n_cal, res["n_test"], cfg.alpha)
bbU, _ = MT.theory_betabinom(n_cal, res["n_test"], cfg.alpha + cfg.beta, lower=cfg.alpha)
PL.validity_histogram(res["fpr"], cfg.alpha, bbA, res["n_test"], "AE: yeniden bölmelerde normal ANOMALY oranı", FIG / "03_validity_anomaly_hist.png")
PL.validity_qq(res["fpr"], bbA, res["n_test"], "QQ: ANOMALY oranı - teori", FIG / "03_validity_anomaly_qq.png")
PL.validity_histogram(res["uncertain"], cfg.beta, bbU, res["n_test"], "AE: yeniden bölmelerde normal UNCERTAIN oranı", FIG / "03_validity_uncertain_hist.png");'''),
    md("## α ve β duyarlılığı (tohum 0, AE) — yanlış alarm ve kaçırılan saldırılara etkisi"),
    code(r'''
ev, p = DEC0["ae"]["ev"], DEC0["ae"]["p"]
rows = []
for a in cfg.alpha_grid:
    for b_ in cfg.beta_grid:
        d = C.decide(p, a, b_)
        ho = ev["split"] == "heldout_test"; kn = ev["split"] == "dev_test"; bn = ~ev["y_attack"]
        rows.append({"alpha": a, "beta": b_,
                     "normal_yanlis_alarm": np.mean(d[bn] == C.ANOMALY), "normal_belirsiz": np.mean(d[bn] == C.UNCERTAIN),
                     "bilinen_recall": np.mean(d[kn] == C.ANOMALY), "bilinen_kacan": np.mean(d[kn] == C.NORMAL),
                     "gorulmemis_recall": np.mean(d[ho] == C.ANOMALY), "gorulmemis_ertelenen": np.mean(d[ho] == C.UNCERTAIN),
                     "gorulmemis_kacan": np.mean(d[ho] == C.NORMAL)})
SENS = pd.DataFrame(rows); SENS.to_csv(FIG / "03_sensitivity_alpha_beta.csv", index=False); SENS.round(4)'''),
    code(r'''
# Aşama 4 için p-değerlerini ve kararları önbelleğe al
for seed in SEEDS:
    S = E.load_scores(cfg, seed); out = {}
    for model in E.MODELS:
        ev = E.eval_set(P, S, model)
        p = C.pvalues(ev["cal"], ev["scores"], seed=seed, model=model)
        out[f"{model}__p"] = p; out[f"{model}__d"] = C.decide(p, cfg.alpha, cfg.beta)
    (ART / "decisions").mkdir(exist_ok=True)
    np.savez_compressed(ART / "decisions" / f"seed{seed}.npz", **out)
print("kararlar önbelleğe alındı, tohumlar:", SEEDS)'''),
    code(FLUSH),
]

# =============================================================================== 04
NB["04_selective_detection_risk_coverage.ipynb"] = [
    md("""
# 04 · Aşama 4 — Seçici tespit ve risk–kapsama analizi
Tanımlar (hata = saldırının NORMAL kararı alması veya normal örneğin ANOMALY kararı alması):
* **Kapsama (coverage)** = otomatik karar verilen pay (NORMAL veya ANOMALY)
* **Çekimser kalma oranı (abstention)** = UNCERTAIN payı (normal ve saldırı için ayrıca raporlanır)
* **Seçici risk (selective risk)** = otomatik kararlardaki hata oranı
* **Görülmemiş saldırı recall** = ANOMALY kararı alan görülmemiş saldırılar; **ertelenen** = UNCERTAIN alanlar
* Saldırı yaygınlığına göre yeniden ağırlıklandırma (π ∈ {0,001; 0,01; 0,1}) test kümesindeki temel oran etkisini kaldırır.

Önceden kaydedilmiş uç noktalar: **E2** — konformal bant, *eşleştirilmiş kapsama*da güçlü alternatiflerden
(B3 sezgisel bant, IF bandı, gizil skor bandı; rastgele çekimserlik yalnızca alt sınır kontrolüdür) daha iyi mi?
**E3** — görülmemiş saldırı ailelerinin aile bazında tespiti ve ertelenmesi.
"""),
    code(SETUP),
    code(r'''
from trustids import data as D, conformal as C, metrics as MT, evaluation as E, plotting as PL
P = D.load_prepared(ART / "prepared")
SEEDS = E.available_seeds(cfg); GROUPS = E.family_groups(cfg)
def decisions(seed):
    z = np.load(ART / "decisions" / f"seed{seed}.npz"); return {k: z[k] for k in z.files}
RUN = utils.new_run_dir(Path(PROJECT_DIR) / cfg.runs_dir, "midterm_phase4")
PREP_REP = utils.load_json(ART / "prepared" / "prepare_report.json")
if not PREP_REP["calibration_rule"]["rule_satisfied"]:          # önceden kaydedilmiş n_cal kuralı
    cfg.alpha = PREP_REP["calibration_rule"]["alpha_effective"]
EXCLUDE_MACRO = () if PREP_REP.get("mitm_in_macro_average", True) else ("mitm",)   # mitm yedek kuralı
utils.save_json(utils.environment_info(), RUN / "environment.json")
print("alpha =", cfg.alpha, "| makro ortalamadan çıkarılan:", EXCLUDE_MACRO)
print("sonuç klasörü:", RUN)'''),
    md("## Genel seçici metrikler (tohum 0), yaygınlığa göre yeniden ağırlıklandırma ile"),
    code(r'''
S0, D0 = E.load_scores(cfg, SEEDS[0]), decisions(SEEDS[0])
rows = []
for model in E.MODELS:
    ev = E.eval_set(P, S0, model)
    for pi in [None] + cfg.prevalence_grid:
        r = MT.selective_metrics(ev["y_attack"], D0[f"{model}__d"], pi)
        rows.append({"model": model, "yaygınlık": "test kümesi" if pi is None else pi, **r})
OVR = pd.DataFrame(rows); OVR.to_csv(RUN / "overall_selective_seed0.csv", index=False); OVR.round(4)'''),
    md("## Profesörün metrikleri: normal / bilinen / görülmemiş ayrı ayrı (tohum 0, AE)"),
    code(r'''
ev = E.eval_set(P, S0, "ae"); d = D0["ae__d"]; p = D0["ae__p"]
rows = []
for part, name in [("dev_test", "bilinen"), ("heldout_test", "görülmemiş")]:
    m = (ev["split"] == "benign_test") | (ev["split"] == part)
    y = ev["y_attack"][m]
    rows.append({"saldırılar": name, **MT.binary_metrics(y, ev["scores"][m], d[m] == C.ANOMALY),
                 **MT.selective_metrics(y, d[m])})
PROF = pd.DataFrame(rows); PROF.to_csv(RUN / "professor_metrics_seed0.csv", index=False); PROF.round(4)'''),
    md("## E2 — Konformal bant, eşleştirilmiş kapsamada alternatiflerden daha mı iyi? (tüm tohumlar)\n"
       "Alternatif yöntemlere referans kuralla **aynı sayıda** UNCERTAIN kararı verdirilir (etiket kullanılmaz). "
       "`delta_sr > 0` konformal AE bandının seçici riskinin **daha düşük** olduğu anlamına gelir; fark yanlış alarm "
       "ve kaçırma bileşenlerine ayrıştırılır."),
    code(r'''
rows = []
for seed in SEEDS:
    S, Dd = E.load_scores(cfg, seed), decisions(seed)
    ev = E.eval_set(P, S, "ae"); y = ev["y_attack"]; d_ref = Dd["ae__d"]
    h = C.heuristic_thresholds(ev["train"], cfg.heuristic_k[0], cfg.heuristic_k[1])
    alts = {"B3 sezgisel bant (eğitim hataları)": (ev["scores"], h["tau_H"])}
    for model, label in [("iforest", "B1 IF konformal bandı"), ("latent", "B5 gizil skor bandı")]:
        e2 = E.eval_set(P, S, model)
        alts[label] = (e2["scores"], C.thresholds(e2["cal"], cfg.alpha, cfg.beta)["tau_H"])
    for label, (s_alt, tauH) in alts.items():
        for pi in [None, 0.01]:
            r = MT.matched_coverage_comparison(y, d_ref, s_alt, tauH, pi)
            rows.append({"seed": seed, "comparison": label, "prevalence": "test kümesi" if pi is None else pi, **r})
    rc = MT.random_abstention_control(y, d_ref, cfg.random_control_repeats, seed)
    rows.append({"seed": seed, "comparison": "rastgele çekimserlik (alt sınır)", "prevalence": "test kümesi",
                 "sr_ref": rc["real_selective_risk"], "sr_alt": rc["random_mean"], "delta_sr": rc["delta"]})
E2 = pd.DataFrame(rows); E2.to_csv(RUN / "E2_matched_coverage.csv", index=False)
cols = ["abstain_ref", "abstain_alt", "sr_ref", "sr_alt", "delta_sr", "delta_false_alarm_part", "delta_miss_part"]
E2.groupby(["comparison", "prevalence"])[[c for c in cols if c in E2]].mean().round(5)'''),
    md("""
### E2 istatistikleri — iki yaygınlık düzeyinde
* **test kümesi** (önceden kaydedilmiş birincil analiz; eşleştirme etiketsiz, UNCERTAIN *sayısı* üzerinden);
* **π = 0,01** (keşifsel; eşleştirme yaygınlık ağırlıklı UNCERTAIN *kütlesi* üzerinden — etiket kullanır, yalnızca analiz amaçlıdır).

Not: 10 tohumla Wilcoxon testinin alabileceği en küçük iki yönlü p-değeri 2/1024 ≈ 0,002'dir; asıl kanıt
bootstrap güven aralıklarıdır. **Bu aralıklar ve testler yalnızca eğitim tohumu değişkenliğini ölçer** (tek, sabit bir
veri bölmesi üzerinde); test örneklerinin örnekleme belirsizliğini içermez.
"""),
    code(r'''
stats_rows = []
for prev, sub in E2.groupby("prevalence"):
    for comp, g in sub.groupby("comparison"):
        lo, hi = MT.bootstrap_ci(g["delta_sr"].to_numpy(), cfg.bootstrap_repeats, 0)
        stats_rows.append({"prevalence": prev, "comparison": comp, "mean_delta_sr": g["delta_sr"].mean(),
                           "ci_low": lo, "ci_high": hi, "seeds": len(g)})
ST = pd.DataFrame(stats_rows)
if len(SEEDS) >= 5:
    W = pd.concat([MT.paired_wilcoxon_holm(sub.assign(zero=0.0), "delta_sr", "zero", "comparison").assign(prevalence=prev)
                   for prev, sub in E2.groupby("prevalence")])
    ST = ST.merge(W[["prevalence", "comparison", "p_raw", "p_holm"]], on=["prevalence", "comparison"])
ST.to_csv(RUN / "E2_statistics.csv", index=False); ST.round(5)'''),
    md("""
### B3 sezgisel eşiğinin gerçekleşen yanlış alarm oranı (10 tohum)
μ + 3σ kuralı Gauss varsayımı altında yaklaşık %0,13 yanlış alarm *vaat eder*; ancak eğitim hatalarından
hesaplandığı için gerçek normal testte bu oran kontrol edilmez. Konformal kuralın oranı ise α ile sınırlıdır.
"""),
    code(r'''
rows = []
for seed in SEEDS:
    S, Dd = E.load_scores(cfg, seed), decisions(seed)
    ev = E.eval_set(P, S, "ae"); b = ~ev["y_attack"]
    h = C.heuristic_thresholds(ev["train"], cfg.heuristic_k[0], cfg.heuristic_k[1])
    rows.append({"tohum": seed, "B3_normal_ANOMALY": float(np.mean(ev["scores"][b] > h["tau_H"])),
                 "konformal_normal_ANOMALY": float(np.mean(Dd["ae__d"][b] == C.ANOMALY))})
B3F = pd.DataFrame(rows)
for col in ["B3_normal_ANOMALY", "konformal_normal_ANOMALY"]:
    lo, hi = MT.bootstrap_ci(B3F[col].to_numpy(), cfg.bootstrap_repeats, 0)
    print(f"{col}: ortalama {B3F[col].mean():.4f}  (%95 GA {lo:.4f}–{hi:.4f}) | Gauss 3σ nominal = 0.00135 | α = {cfg.alpha}")
B3F.to_csv(RUN / "B3_false_alarm_10seeds.csv", index=False)'''),
    md("""
## UNCERTAIN bandı gerçekte ne kazandırıyor? — katmanlama (10 tohum)
Üç yönlü kuralda ANOMALY ∪ UNCERTAIN birleşimi, **α+β düzeyindeki ikili kuralla aynıdır**; yani işaretlenen toplam
pay yapı gereği aynıdır. Kazanç, işaretlenen kümenin **anında alarm** ve **inceleme** katmanlarına bölünmesidir:
anında alarmların yanlış alarm yükü α ile, inceleme yükü β ile sınırlıdır. Tablo, katman başına kesinliği (precision)
gerçekçi yaygınlıkta (π = 0,01) ve 10 000 akış başına analist yükünü gösterir.
"""),
    code(r'''
tier_rows = []
for seed in SEEDS:
    S, Dd = E.load_scores(cfg, seed), decisions(seed)
    ev = E.eval_set(P, S, "ae")
    for pi in [None, 0.01]:
        for part, name in [("heldout_test", "görülmemiş"), ("dev_test", "bilinen")]:
            m = (ev["split"] == "benign_test") | (ev["split"] == part)
            t = MT.tiering_vs_binary(ev["y_attack"][m], Dd["ae__p"][m], cfg.alpha, cfg.beta, pi)
            t["tohum"], t["yaygınlık"], t["saldırılar"] = seed, "test kümesi" if pi is None else pi, name
            tier_rows.append(t)
TIER = pd.concat(tier_rows); TIER.to_csv(RUN / "tiering_vs_binary_10seeds.csv", index=False)
cols = ["benign_immediate_alarm", "benign_review", "attack_immediate_alarm", "attack_review", "attack_missed",
        "precision_alarm_tier", "precision_review_tier", "alarms_per_flows", "reviews_per_flows"]
TIER.groupby(["saldırılar", "yaygınlık", "rule"])[cols].mean().round(4)'''),
    md("## Risk–kapsama eğrileri (tohum 0)"),
    code(r'''
curves = {}
for model, label in [("ae", "AE konformal (β taranır)"), ("iforest", "IF konformal"), ("latent", "gizil skor konformal")]:
    ev_m = E.eval_set(P, S0, model)
    curves[label] = MT.risk_coverage_curve(ev_m["y_attack"], D0[f"{model}__p"], cfg.alpha)
ev = E.eval_set(P, S0, "ae"); h = C.heuristic_thresholds(ev["train"], *cfg.heuristic_k)
pts = []
for k in np.linspace(0, 0.4, 40):
    n_abs = int(k * len(ev["scores"]))
    tl = MT.band_for_abstention(ev["scores"], h["tau_H"], n_abs)
    pts.append(MT.selective_metrics(ev["y_attack"], C.decide_by_thresholds(ev["scores"], tl, h["tau_H"])))
curves["B3 sezgisel bant"] = pd.DataFrame(pts).sort_values("coverage")
ref = MT.selective_metrics(ev["y_attack"], D0["ae__d"])
PL.risk_coverage(curves, "Risk–kapsama (tohum 0)", RUN / "risk_coverage.png",
                 {f"önceden kaydedilmiş α={cfg.alpha}, β={cfg.beta}": (ref["coverage"], ref["selective_risk"])});'''),
    code(r'''
# AURC: güven = p-değerinin karar sınırına (log ölçekte) uzaklığı.
# Not: AURC her modelin KENDİ kararları ve sıralaması üzerinden hesaplanır; modeller farklı karar kümeleri
# ürettiği için modeller arası karşılaştırmaya uygun değildir (yalnızca bilgi amaçlı, birincil uç nokta değildir).
rows = []
for model in E.MODELS:
    ev_m = E.eval_set(P, S0, model); p_m = D0[f"{model}__p"]
    pred = p_m <= cfg.alpha
    conf = np.abs(np.log(p_m) - np.log(cfg.alpha))
    rows.append({"model": model, **MT.aurc(ev_m["y_attack"], conf, pred == ev_m["y_attack"])})
AU = pd.DataFrame(rows); AU.to_csv(RUN / "aurc_seed0.csv", index=False); AU.round(5)'''),
    md("## Düşük p-değeri gerçekten 'saldırı' mı demek? (p-değeri aralığına göre güvenilirlik, tohum 0, AE)"),
    code(r'''
RB = MT.error_by_pvalue_bin(ev["y_attack"], D0["ae__p"], D0["ae__d"], cfg.pvalue_bins)
PL.reliability_bins(RB, "p-değeri aralığına göre saldırı payı ve karar hatası (AE, tohum 0)", RUN / "reliability_bins.png")
RB.round(4)'''),
    md("## E3 — Görülmemiş aileler: tespit edilen, ertelenen, kaçırılan (tohumlar üzerinden ortalama)\n"
       "**Birincil recall** = çakışan (aynı vektörü normal etiketle de taşıyan) saldırılar *kaçırılmış* sayılarak hesaplanan kötümser değer."),
    code(r'''
fam_rows = []
for seed in SEEDS:
    S, Dd = E.load_scores(cfg, seed), decisions(seed)
    ev = E.eval_set(P, S, "ae")
    t = MT.per_family_table(ev["types"], Dd["ae__d"], GROUPS, collision=ev["collision"],
                            exclude_from_macro=EXCLUDE_MACRO); t["seed"] = seed; fam_rows.append(t)
FAM = pd.concat(fam_rows)
E3_COLS = ["anomaly_rate_collisions_as_missed", "anomaly_rate", "uncertain_rate", "normal_rate"]   # ilki = birincil
E3 = FAM.groupby(["group", "family"])[[c for c in E3_COLS if c in FAM]].agg(["mean", "std"]).round(4)
FAM.to_csv(RUN / "E3_per_family_all_seeds.csv", index=False); E3'''),
    md("## İkincil: tekrar ağırlıklandırmasına duyarlılık (satır ağırlıklı ve benzersiz vektör, tohum 0, AE)\n"
       "Garanti benzersiz vektörler içindir; satır (akış) ağırlıklı oranlar ikincil olarak, ek bir 'kayma' (S0) gibi raporlanır."),
    code(r'''
ev = E.eval_set(P, S0, "ae"); d = D0["ae__d"]; w = ev["multiplicity"]
g = E.group_of(ev["types"], cfg)
rows = []
for grp in ["normal", "known", "held-out"]:
    m = g == grp
    rows.append({"grup": grp, "anomaly_benzersiz": np.mean(d[m] == C.ANOMALY),
                 "anomaly_satir_agirlikli": np.average(d[m] == C.ANOMALY, weights=w[m]),
                 "uncertain_benzersiz": np.mean(d[m] == C.UNCERTAIN),
                 "uncertain_satir_agirlikli": np.average(d[m] == C.UNCERTAIN, weights=w[m])})
MW = pd.DataFrame(rows); MW.to_csv(RUN / "multiplicity_weighted_seed0.csv", index=False); MW.round(4)'''),
    md("## Normal/saldırı çakışmaları (aynı vektör iki etiketle görülmüş)\n"
       "Bir normal ve bir saldırı kopyası tutulur; saldırı kopyası işaretlenir. Recall: (a) olduğu gibi, "
       "(b) çakışmalar hariç, (c) çakışan saldırılar kaçırılmış sayılarak. **(c) birincil (kötümser) değerdir.**"),
    code(r'''
rows = []
for grp in ["known", "held-out"]:
    m = g == grp; c = ev["collision"] & m
    rec = np.mean(d[m] == C.ANOMALY)
    rec_excl = np.mean(d[m & ~ev["collision"]] == C.ANOMALY) if (m & ~ev["collision"]).any() else np.nan
    rec_pess = np.mean(np.where(ev["collision"][m], False, d[m] == C.ANOMALY))
    rows.append({"grup": grp, "çakışan_vektör": int(c.sum()), "recall": rec,
                 "recall_çakışmalar_hariç": rec_excl, "recall_çakışmalar_kaçmış (birincil)": rec_pess})
COL = pd.DataFrame(rows); COL.to_csv(RUN / "collisions_seed0.csv", index=False); COL.round(4)'''),
    md("## Ara rapor özeti (profesör için)"),
    code(r'''
val = pd.read_csv(FIG / "03_validity_E1.csv")
summary = {
    "yapilandirma": {"alpha": cfg.alpha, "beta": cfg.beta, "tohumlar": SEEDS, "gorulmeyecek_aileler": cfg.heldout_families},
    "E1_gecerlilik_tohum_ortalamasi": val.groupby(["model", "decision"])[["budget", "mean", "share_above_theory_q95"]].mean().round(5).reset_index().to_dict(orient="records"),
    "E2_eslestirilmis_kapsama": ST.round(5).to_dict(orient="records"),
    "B3_yanlis_alarm_10_tohum": B3F.drop(columns=["tohum"], errors="ignore").agg(["mean", "std"]).round(5).to_dict(),
    "katmanlama_10_tohum": TIER.groupby(["saldırılar", "yaygınlık", "rule"])[cols].mean().round(4).reset_index().to_dict(orient="records"),
    "E3_gorulmemis": FAM[FAM["group"] == "held-out"].groupby("family")[[c for c in E3_COLS if c in FAM]].mean().round(4).reset_index().to_dict(orient="records"),
    "profesor_metrikleri_tohum0": PROF.round(4).to_dict(orient="records"),
    "ortam": utils.environment_info(),
}
utils.save_json(summary, RUN / "midterm_summary.json")
import shutil
cfg.save(RUN / "config_used.json")
for f in ["data_file_info.json", "training_summary.json", "ae_selection.json", "environment.json"]:
    if (ART / f).exists():
        shutil.copy(ART / f, RUN / f)
shutil.copy(ART / "prepared" / "prepare_report.json", RUN / "prepare_report.json")
shutil.copytree(FIG, RUN / "figures", dirs_exist_ok=True)   # bu çalıştırmanın şekilleri/tabloları, ileride üzerine yazılmasın
print("Tüm sonuçlar kaydedildi (yapılandırma ve şekiller dahil):", RUN)
pd.DataFrame(summary["E3_gorulmemis"])'''),
    md("""
**Sonraki adım (final aşama):** `04b_uncertain_resolution`, ardından `F1_fl_teshis`, `F2_lofo`, `F3_asama5_9_on_tohum`.
"""),
    code(FLUSH),
]


# =============================================================================== 04b
NB["04b_uncertain_resolution.ipynb"] = [
    md("""
# 04b · Aşama 4 (devam) — UNCERTAIN kararının çözümlenmesi: "ek inceleme / üst sisteme yönlendirme"
Profesörün planı belirsiz örneklerin otomatik karar yerine **ek incelemeye** veya **üst sisteme** yönlendirilmesini ister.
Bu defter bu adımı somutlaştırır: **UNCERTAIN asla sessiz bir çıkmaz değildir.**

| Basamak | Nerede | Ne olur |
|---|---|---|
| 0 | Cihaz, hemen | UNCERTAIN → geri alınabilir önlem (izleme / hız sınırlama); asla sessizlik, asla otomatik engelleme |
| **2 (ana katkı)** | Cihaz, sonraki akışlar | Ana bilgisayar (host) başına sayaç: W akışlık pencerede p ≤ α+β olan akış sayısı K. K ≥ k\\* ise **yükselt**, değilse **serbest bırak** |
| 1 (isteğe bağlı) | Ağ geçidi = "üst sistem" | Yalnızca *bilinen* ailelerle eğitilmiş denetimli model; esas olarak **temel çizgi** olarak raporlanır |

**Operasyonel bütçe (önceden kaydedildi):** cihaz başına haftada en fazla B = 1 yanlış yükseltme. Günde F akış ve W'lik
pencerelerle pencere başına bütçe α_w = B·W/(7F) olur; k\\* bu bütçeyle normal-doğrulama pencerelerinden konformal olarak seçilir.

**Dürüstlük notları:**
* TON_IoT sürüm B'de zaman damgası yoktur. Bu nedenle host pencereleri **rastgele çekilir**; gerçek zaman akışı değil, **simülasyondur**.
* Küçük bütçeler için kalibrasyon pencereleri **alt örnekleme** ile üretilir (pencereler örtüşebilir). Bu yüzden garanti yaklaşıktır ve normal-test üzerinde host bazında doğrulanır.
* Görülmeyecek üç aile (ransomware, xss, mitm) daha önce defalarca incelendi. Bu defterin sonuçları **keşif amaçlıdır**; doğrulayıcı test, önceden kaydedilmiş "her seferinde bir aile dışarıda" protokolüyledir (öneri v6, §7a.3).
* `src_ip` yalnızca **gruplama anahtarıdır**, hiçbir zaman model özniteliği değildir.
"""),
    code(SETUP),
    code(r'''
from trustids import data as D, conformal as C, evaluation as E, resolution as R
P = D.load_prepared(ART / "prepared")
RES_DIR = ART / "resolution"; RES_DIR.mkdir(exist_ok=True)
FP = utils.config_fingerprint(cfg)   # ara sonuç dosyaları bu ayarlara bağlıdır; ayar değişirse yeniden hesaplanır
RUN = utils.new_run_dir(Path(PROJECT_DIR) / cfg.runs_dir, "midterm_phase4b_resolution")
SEEDS = E.available_seeds(cfg)
HOSTMAP = RES_DIR / "host_rows.csv.gz"
if RESUME and HOSTMAP.exists():
    ROWS = pd.read_csv(HOSTMAP, keep_default_na=False)
    ROWS["split"] = ROWS["split"].replace({"": None})
    print("Kayıtlı host eşlemesi kullanılıyor (devam modu)")
else:
    raw = D.load_raw(cfg.data_path, cfg)
    ROWS = R.map_rows(raw, P, cfg)
    ROWS.to_csv(HOSTMAP, index=False)
ROWS = ROWS[ROWS["split"].isin(["benign_val", "benign_test", "dev_test", "heldout_test"])].reset_index(drop=True)
print("eşlenen ham akış:", len(ROWS), ROWS.groupby("split").size().to_dict())
print("farklı host sayısı:", ROWS.groupby("split")["host"].nunique().to_dict())'''),
    md("## Operasyonel bütçe: cihaz başına haftada ≤ 1 yanlış yükseltme"),
    code(r'''
BUD = pd.DataFrame([{"W": W, "günlük_akış_F": F, "pencere_bütçesi_α_w": R.window_budget(cfg.resolution_budget_per_week, W, F),
                     "gereken_kalibrasyon_penceresi": R.min_cal_windows(R.window_budget(cfg.resolution_budget_per_week, W, F))}
                    for W in cfg.resolution_windows for F in cfg.resolution_flows_per_day])
BUD.to_csv(RUN / "04b_operational_budget.csv", index=False); BUD'''),
    md("""
## Basamak 2: host sayacı (tüm tohumlar; her tohum Drive'a kaydedilir, oturum kapanırsa kaldığı yerden devam eder)
Her tohum için: akış p-değerleri → işaret (p ≤ α+β) → pencereler → k\\* (normal-doğrulama) → değerlendirme.
Karşılaştırma (ablasyon): yalnızca ANOMALY akışlarını (p ≤ α) sayan sayaç; kendi k\\* değeriyle.
"""),
    code(r'''
def evaluate_seed(seed):
    S = E.load_scores(cfg, seed)
    cal = S[("ae", "benign_cal")]
    pv = {sp: C.pvalues(cal, S[("ae", sp)], seed=seed, model="ae") for sp in ["benign_val", "benign_test", "dev_test", "heldout_test"]}
    p = R.row_values(ROWS, pv)
    flags = {"ANOMALY+UNCERTAIN": p <= cfg.alpha + cfg.beta, "yalnız ANOMALY": p <= cfg.alpha}
    rng = np.random.default_rng(1000 + seed)
    g_val = R.host_groups(ROWS, (ROWS["split"] == "benign_val").to_numpy())
    g_ben = R.host_groups(ROWS, (ROWS["split"] == "benign_test").to_numpy())
    ben_all = np.concatenate(list(g_ben.values()))
    fams = [f for f in cfg.dev_families + cfg.heldout_families if f in set(ROWS["type"])]
    out = []
    for W in cfg.resolution_windows:
        cal_w, _ = R.sample_windows(g_val, W, cfg.resolution_cal_windows, rng)
        ev_w, ev_h = R.sample_windows(g_ben, W, cfg.resolution_eval_windows, rng)
        if len(cal_w) == 0 or len(ev_w) == 0:
            print(f"W={W}: {W} akışa ulaşan normal host yok, atlanıyor"); continue
        for F in cfg.resolution_flows_per_day:
            a_w = R.window_budget(cfg.resolution_budget_per_week, W, F)
            for fname, flag in flags.items():
                k = R.k_threshold(R.counts(flag, cal_w), a_w)
                esc = R.counts(flag, ev_w) >= k
                host_rate = pd.Series(esc).groupby(ev_h).mean()
                base = {"tohum": seed, "W": W, "F": F, "sayaç": fname, "k_yildiz": k, "α_w": a_w,
                        "normal_yanlis_yukseltme_pencere": float(esc.mean()),
                        "normal_haftalik_yanlis_yukseltme_ortalama": R.per_week(float(esc.mean()), W, F),
                        "normal_haftalik_host_p95": R.per_week(float(host_rate.quantile(0.95)), W, F),
                        "normal_haftalik_en_kotu_host": R.per_week(float(host_rate.max()), W, F),
                        "en_kotu_host": str(host_rate.idxmax())}
                for fam in fams:
                    sp = "heldout_test" if fam in cfg.heldout_families else "dev_test"
                    m_f = ((ROWS["split"] == sp) & (ROWS["type"] == fam)).to_numpy()
                    att_ix = np.where(m_f)[0]
                    pure, _ = R.disjoint_windows(R.host_groups(ROWS, m_f), W, rng)
                    row = dict(base, aile=fam, grup="görülmemiş" if fam in cfg.heldout_families else "bilinen",
                               akış_ANOMALY=float(np.mean(p[att_ix] <= cfg.alpha)),
                               akış_UNCERTAIN=float(np.mean((p[att_ix] > cfg.alpha) & (p[att_ix] <= cfg.alpha + cfg.beta))),
                               saf_pencere_sayisi=len(pure),
                               saf_pencere_tespit=float(np.mean(R.counts(flag, pure) >= k)) if len(pure) else np.nan)
                    for rho in cfg.resolution_rho:
                        if len(att_ix) >= W:
                            mw = R.mixed_windows(att_ix, ben_all, W, rho, 300, rng)
                            row[f"karisik_ρ={rho:.2f}"] = float(np.mean(R.counts(flag, mw) >= k))
                    out.append(row)
    # çıkmaz oranı: penceresini dolduramayan hostlardaki UNCERTAIN akışlar (W akışa ulaşmadan karar verilemez)
    unc = (p > cfg.alpha) & (p <= cfg.alpha + cfg.beta)
    sizes = ROWS.groupby(["split", "host", "type"])["host"].transform("size").to_numpy()
    for W in cfg.resolution_windows:
        for grp, msk in [("normal", (ROWS["split"] == "benign_test").to_numpy()),
                         ("bilinen", (ROWS["split"] == "dev_test").to_numpy()),
                         ("görülmemiş", (ROWS["split"] == "heldout_test").to_numpy())]:
            u = unc & msk
            out.append({"tohum": seed, "W": W, "sayaç": "çıkmaz_oranı", "grup": grp,
                        "cikmaz_orani": float(np.mean(sizes[u] < W)) if u.any() else 0.0})
    return pd.DataFrame(out)

for seed in SEEDS:
    f = RES_DIR / f"seed{seed}_{FP}.csv"
    if RESUME and f.exists():
        print("tohum", seed, "Drive'da kayıtlı, atlanıyor (devam modu)"); continue
    evaluate_seed(seed).to_csv(f, index=False)
    print("tohum", seed, "tamam (Drive'a kaydedildi)")
RES = pd.concat([pd.read_csv(RES_DIR / f"seed{s}_{FP}.csv") for s in SEEDS], ignore_index=True)
RES.to_csv(RUN / "04b_resolution_all_seeds.csv", index=False)
print("toplam satır:", len(RES))'''),
    md("""
## Sonuç 1 — Normal trafikte maliyet: cihaz başına haftalık yanlış yükseltme (hedef ≤ 1)
Ortalama, %95'lik host ve en kötü host ayrı ayrı raporlanır. Bütçe pencereler üzerinden *ortalama* bir garantidir;
tek tek hostlar için değil. En kötü host bu yüzden ayrıca gösterilir.
"""),
    code(r'''
main = RES[RES["sayaç"] != "çıkmaz_oranı"]
COST = (main.drop_duplicates(["tohum", "W", "F", "sayaç"])
            .groupby(["sayaç", "W", "F"])[["k_yildiz", "normal_haftalik_yanlis_yukseltme_ortalama",
                                           "normal_haftalik_host_p95", "normal_haftalik_en_kotu_host"]]
            .agg(["mean", "std"]).round(3))
COST.columns = [f"{a}_{b}" for a, b in COST.columns]
COST.to_csv(RUN / "04b_benign_cost.csv"); COST'''),
    md("## Sonuç 2 — Saldırılar: akış düzeyinde (tek akış) ve host düzeyinde (sayaç) tespit, tohum ortalaması"),
    code(r'''
DET = (main.groupby(["sayaç", "W", "F", "grup", "aile"])
           [["akış_ANOMALY", "akış_UNCERTAIN", "saf_pencere_tespit"] + [c for c in main.columns if c.startswith("karisik_")]]
           .mean().round(3))
DET.to_csv(RUN / "04b_detection_per_family.csv"); DET.xs("ANOMALY+UNCERTAIN", level="sayaç")'''),
    code(r'''
W0, F0 = cfg.resolution_windows[0], max(cfg.resolution_flows_per_day)
sub = main[(main["W"] == W0) & (main["F"] == F0) & (main["grup"] == "görülmemiş")]
rhos = [c for c in sub.columns if c.startswith("karisik_")]
fig, ax = plt.subplots(figsize=(6.5, 3.8))
for fname, mk in [("ANOMALY+UNCERTAIN", "o-"), ("yalnız ANOMALY", "s--")]:
    v = sub[sub["sayaç"] == fname].groupby("tohum")[rhos].mean()
    ax.errorbar([float(c.split("=")[1]) for c in rhos], v.mean(), yerr=v.std(), fmt=mk, capsize=3, label=f"sayaç: {fname}")
flow = sub[sub["sayaç"] == "ANOMALY+UNCERTAIN"].groupby("tohum")["akış_ANOMALY"].mean().mean()
ax.axhline(flow, color="gray", ls=":", label="tek akış ANOMALY (sayaç yok)")
ax.set_xlabel("host trafiğindeki saldırı payı ρ"); ax.set_ylabel("görülmemiş aileler: host tespiti")
ax.set_title(f"UNCERTAIN çözümleme (W={W0}, F={F0}/gün, ≤1 yanlış yükseltme/hafta)")
ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(FIG / "04b_resolution_vs_rho.png", dpi=150)'''),
    md("## Sonuç 3 — Çıkmaz oranı: penceresi dolmadığı için çözümlenemeyen UNCERTAIN akış payı"),
    code(r'''
DEAD = RES[RES["sayaç"] == "çıkmaz_oranı"].groupby(["W", "grup"])["cikmaz_orani"].agg(["mean", "std"]).round(4)
DEAD.to_csv(RUN / "04b_dead_end_rate.csv"); DEAD'''),
    md("""
## Basamak 1 — "Üst sistem" (ağ geçidi) ve dürüst temel çizgi: yalnızca bilinen ailelerle eğitilmiş Random Forest
Üç soru: (a) RF **tek başına** görülmemiş aileleri ne kadar yakalar (aynı %α yanlış alarmda)? (b) AE'nin UNCERTAIN bandı
içinde RF saldırıyı normalden ayırabiliyor mu (AUC)? (c) AE + ağ geçidi: UNCERTAIN akış, RF eşiği aşarsa ANOMALY olur.
(a) yüksekse bu, TON_IoT'deki "görülmemiş" ailelerin bilinen ailelere benzediği anlamına gelir: bu bir **veri kümesi
bulgusudur** ve gizlenmez.
"""),
    code(r'''
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
X, T = P["X"], P["types"]
GW_FILE = RES_DIR / f"gateway_rf_{FP}.csv"
if RESUME and GW_FILE.exists():
    GW = pd.read_csv(GW_FILE); print("Kayıtlı ağ geçidi sonuçları kullanılıyor (devam modu)")
else:
    rows = []
    for seed in SEEDS:
        rf = RandomForestClassifier(n_estimators=200, random_state=seed, n_jobs=-1, class_weight="balanced")
        rf.fit(np.r_[X["benign_train"], X["dev_val"]], np.r_[np.zeros(len(X["benign_train"])), np.ones(len(X["dev_val"]))])
        thr = np.quantile(rf.predict_proba(X["benign_cal"])[:, 1], 1 - cfg.alpha, method="higher")
        S = E.load_scores(cfg, seed); cal = S[("ae", "benign_cal")]
        pb = C.pvalues(cal, S[("ae", "benign_test")]); ph = C.pvalues(cal, S[("ae", "heldout_test")])
        rb, rh = rf.predict_proba(X["benign_test"])[:, 1], rf.predict_proba(X["heldout_test"])[:, 1]
        ub = (pb > cfg.alpha) & (pb <= cfg.alpha + cfg.beta)
        for fam in cfg.heldout_families:
            m = T["heldout_test"] == fam
            uh = m & (ph > cfg.alpha) & (ph <= cfg.alpha + cfg.beta)
            auc = roc_auc_score(np.r_[np.zeros(ub.sum()), np.ones(uh.sum())], np.r_[rb[ub], rh[uh]]) if uh.sum() and ub.sum() else np.nan
            rows.append({"tohum": seed, "aile": fam, "AE_ANOMALY": float(np.mean(ph[m] <= cfg.alpha)),
                         "RF_tek_basina_recall": float(np.mean(rh[m] > thr)), "RF_AUC_UNCERTAIN_bandinda": auc,
                         "AE+ağ_geçidi_recall": float(np.mean((ph[m] <= cfg.alpha) | ((ph[m] <= cfg.alpha + cfg.beta) & (rh[m] > thr))))})
        rows.append({"tohum": seed, "aile": "normal (yanlış alarm)", "AE_ANOMALY": float(np.mean(pb <= cfg.alpha)),
                     "RF_tek_basina_recall": float(np.mean(rb > thr)), "RF_AUC_UNCERTAIN_bandinda": np.nan,
                     "AE+ağ_geçidi_recall": float(np.mean((pb <= cfg.alpha) | (ub & (rb > thr))))})
        print("tohum", seed, "tamam")
    GW = pd.DataFrame(rows); GW.to_csv(GW_FILE, index=False)
GWT = GW.groupby("aile").agg(["mean", "std"]).drop(columns="tohum", level=0).round(3)
GWT.to_csv(RUN / "04b_gateway_baseline.csv"); GWT'''),
    md("## Özet (profesör için) ve kayıt"),
    code(r'''
import shutil
key = main[(main["sayaç"] == "ANOMALY+UNCERTAIN")]
summary = {
    "not": "Keşif amaçlı; host pencereleri simülasyondur (sürüm B'de zaman damgası yok). Doğrulayıcı test: öneri v6 §7a.3.",
    "operasyonel_bütçe": "cihaz başına haftada <= %.1f yanlış yükseltme" % cfg.resolution_budget_per_week,
    "normal_maliyet": COST.reset_index().to_dict(orient="records"),
    "görülmemiş_host_tespiti": key[key["grup"] == "görülmemiş"].groupby(["W", "F", "aile"])[["akış_ANOMALY", "saf_pencere_tespit"] + rhos].mean().round(3).reset_index().to_dict(orient="records"),
    "çıkmaz_oranı": DEAD.reset_index().to_dict(orient="records"),
    "ağ_geçidi_temel_çizgi": GW.groupby("aile").mean(numeric_only=True).drop(columns="tohum").round(3).reset_index().to_dict(orient="records"),
}
utils.save_json(summary, RUN / "resolution_summary.json")
cfg.save(RUN / "config_used.json"); utils.save_json(utils.environment_info(), RUN / "environment.json")
for f in FIG.glob("04b_*"):
    shutil.copy(f, RUN / f.name)
print("Tüm sonuçlar kaydedildi:", RUN)'''),
    md("""
**Yorumlama kılavuzu.** Ana soru: UNCERTAIN akışlar, normal trafikte haftada ≤ 1 yanlış yükseltme bütçesiyle host düzeyinde
saldırıya dönüştürülebiliyor mu? "yalnız ANOMALY" sayacıyla karşılaştırma, UNCERTAIN seviyesinin katkısını gösterir.
RF temel çizgisi yüksekse bu, veri kümesi hakkında bir bulgudur. Doğrulayıcı sonuçlar ancak "her seferinde bir aile dışarıda"
protokolüyle (yeni tohumlarla) raporlanır.
"""),
    code(FLUSH),
]


# =============================================================================== F1, F2, F3 (final aşama)
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from final_cells import define as _define_final
_define_final(NB, md, code, SETUP, FLUSH)


def main():
    OUT.mkdir(exist_ok=True)
    for name, cells in NB.items():
        (OUT / name).write_text(json.dumps(notebook(cells), indent=1, ensure_ascii=False), encoding="utf-8")
        print("yazıldı:", OUT / name)


if __name__ == "__main__":
    main()
