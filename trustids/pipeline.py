"""Phases 5-9 for ONE training seed (final phase). Used by notebook F3 (all 53 features) and F4 (21 device
features), so both go through exactly the same code.

Every FL model is cached on Drive as soon as it is trained; the per-seed result file is written by the
notebook when the whole seed is done. Nothing here is tuned on test data.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from . import conformal as C
from . import final as FZ
from . import fl as FL
from . import models as M
from . import tiny as TY
from . import utils

EV = ["benign_cal", "benign_test", "dev_test", "heldout_test"]
KEYS = ["fl", "fl_istemci", "egitim", "tiny", "int8", "rob", "abl", "rc"]


def _cached(cache_dir: Path, key: str, fp: str, resume: bool, fn):
    import tensorflow as tf
    mf, jf = cache_dir / f"{key}_{fp}.keras", cache_dir / f"{key}_{fp}.json"
    if resume and mf.exists() and jf.exists():
        return tf.keras.models.load_model(mf, compile=False), utils.load_json(jf)
    m, info = fn()
    m.save(mf)
    utils.save_json(info, jf)
    return m, info


def run_seed(seed: int, *, cfg, X: dict, cats: dict, build, central, base: dict, cache_dir: Path, fp: str,
             resume: bool, coll_ho: np.ndarray, iforest: dict | None = None, latent: dict | None = None,
             log=print) -> dict:
    """X: split -> feature matrix; cats: benign split -> non-IID category per vector (client partition key);
    build(): fresh AE; central: the converged central AE of this seed; base: its scores on the EV splits;
    iforest / latent: optional scores of the reference models on the EV splits (A1 and risk-coverage)."""
    out = {k: [] for k in KEYS}
    K = cfg.fl_clients
    parts = {s: FL.partition(cats, K, s, seed) for s in cfg.fl_scenarios}
    tag = lambda s: s.replace("=", "")

    def add_fl(model_name, s, score_fn, per_client_models=False):
        det = []
        for r in FL.evaluate(score_fn, parts[s], X, cfg, seed, per_client_models=per_client_models, detail=det):
            out["fl"].append({"tohum": seed, "model": model_name, "senaryo": s, **r})
        out["fl_istemci"] += [{"tohum": seed, "model": model_name, "senaryo": s, **r} for r in det]

    # ---------------- Phases 5-6: federated learning
    FLM = {}
    for s in cfg.fl_scenarios:
        for prot in cfg.fl_final_protocols:
            m, info = _cached(cache_dir, f"s{seed}_{tag(s)}_{prot}", fp, resume,
                              lambda: FL.run_protocol(prot, cfg, build, X["benign_train"], parts[s]["benign_train"],
                                                      X["benign_val"], seed))
            FLM[(s, prot)] = m
            out["egitim"].append({"tohum": seed, "senaryo": s, "protokol": prot,
                                  **{a: b for a, b in info.items() if a != "val_hist"}})
            sc = {sp: M.ae_score(m, X[sp]) for sp in EV}
            add_fl(f"FedAvg · {prot}", s, lambda k, sp, sc=sc: sc[sp])
            log(f"  tohum {seed}: FL {s} / {prot} tamam ({info['rounds_run']} tur, {info['stopped_by']})")
        add_fl("Merkezi (yakınsama)", s, lambda k, sp: base[sp])
    for s in [cfg.fl_scenarios[0], cfg.fl_scenarios[-1]]:
        ms = []
        for k in range(K):
            tr, va = parts[s]["benign_train"][k], parts[s]["benign_val"][k]
            if len(tr) == 0 or len(va) == 0:          # a client without training or validation data has no local model
                ms.append(None); continue
            m, _ = _cached(cache_dir, f"s{seed}_YEREL_{tag(s)}_k{k}", fp, resume,
                           lambda: FL.train_federated(build, X["benign_train"][tr], [np.arange(len(tr))], X["benign_val"][va],
                                                      rounds=None, local_epochs=cfg.fl_local_epochs, lr=cfg.learning_rate,
                                                      batch_size=cfg.batch_size, seed=100 * seed + k,
                                                      optimizer_state="persistent", conv_window=cfg.conv_window,
                                                      conv_rel_tol=cfg.conv_rel_tol, patience=cfg.patience,
                                                      epoch_cap=cfg.epochs))
            ms.append(m)
        add_fl("Yalnız yerel (yakınsama)", s, lambda k, sp, ms=ms: None if ms[k] is None else M.ae_score(ms[k], X[sp]),
               per_client_models=True)
        log(f"  tohum {seed}: yalnız yerel {s} tamam")

    # ---------------- Phase 7: TinyML (FP32 / INT8)
    from scipy import stats as st
    iid = cfg.fl_scenarios[0]
    rep = TY.representative(X["benign_train"], 500, seed)
    SRC = {"Merkezi AE": central, **{f"FedAvg-{iid} · {p}": FLM[(iid, p)] for p in cfg.fl_final_protocols}}
    Q8, S32ALL = {}, {}
    for name, m in SRC.items():
        fp32, q = TY.convert(m, rep, False), TY.convert(m, rep, True)
        tdir = cache_dir / "tflite"; tdir.mkdir(exist_ok=True)            # deliverable: FP32 and INT8 model files
        stem = f"s{seed}_" + ("merkezi" if name == "Merkezi AE" else "fedavg_" + name.split(" · ")[1])
        (tdir / f"{stem}_fp32.tflite").write_bytes(fp32); (tdir / f"{stem}_int8.tflite").write_bytes(q)
        S32 = base if name == "Merkezi AE" else {sp: M.ae_score(m, X[sp]) for sp in EV}
        S8 = {sp: TY.tflite_score(q, X[sp]) for sp in EV}
        Q8[name], S32ALL[name] = S8, S32
        out["tiny"].append({"tohum": seed, "model": name, "parametre": m.count_params(), "tflite_fp32_KB": len(fp32) / 1024,
                            "tflite_int8_KB": len(q) / 1024, "tahmini_RAM_KB_int8": TY.ram_estimate_kb(m),
                            "gecikme_fp32_µs_colab": TY.latency_us(fp32, X["benign_test"][0]),
                            "gecikme_int8_µs_colab": TY.latency_us(q, X["benign_test"][0]),
                            "Spearman_FP32_INT8": st.spearmanr(S32["benign_test"], S8["benign_test"]).correlation})
        th32 = C.thresholds(S32["benign_cal"], cfg.alpha, cfg.beta)
        for rule, sc, th in [("FP32 skor + FP32 eşik", S32, th32), ("INT8 skor + devralınan FP32 eşik", S8, th32),
                             ("INT8 skor + INT8 yeniden kalibrasyon", S8, None)]:
            if th is None:
                pb = C.pvalues(sc["benign_cal"], sc["benign_test"], seed=seed, model="int8")
                ph = C.pvalues(sc["benign_cal"], sc["heldout_test"], seed=seed, model="int8")
                fpr, ha = np.mean(pb <= cfg.alpha), np.mean(ph <= cfg.alpha)
                bu = np.mean((pb > cfg.alpha) & (pb <= cfg.alpha + cfg.beta))
                hu = np.mean((ph > cfg.alpha) & (ph <= cfg.alpha + cfg.beta))
            else:
                fpr, ha = np.mean(sc["benign_test"] > th["tau_H"]), np.mean(sc["heldout_test"] > th["tau_H"])
                bu = np.mean((sc["benign_test"] > th["tau_L"]) & (sc["benign_test"] <= th["tau_H"]))
                hu = np.mean((sc["heldout_test"] > th["tau_L"]) & (sc["heldout_test"] <= th["tau_H"]))
            out["int8"].append({"tohum": seed, "model": name, "kural": rule, "normal_FPR": fpr, "fark_α": fpr - cfg.alpha,
                                "normal_UNCERTAIN": bu, "görülmemiş_ANOMALY": ha, "görülmemiş_UNCERTAIN": hu})

    # ---------------- Phase 8: robustness (central AE): noise, missing features, corrupted features
    med = np.median(X["benign_train"], axis=0)
    d = X["benign_train"].shape[1]
    for kind, levels in TY.CORRUPTIONS:
        for lv in levels:
            for r_i in range(1 if kind == "temiz" else 3):
                rng = np.random.default_rng(100_000 * seed + 100 * r_i + int(lv * 1000))   # seed 0 = the midterm draws
                cols = rng.choice(d, int(lv), replace=False) if kind == "bozuk özellik" else None
                Sc = {sp: M.ae_score(central, TY.corrupt(X[sp], kind, lv, rng, med, cols)) for sp in EV}
                for pol, cal in [("devralınan eşik", base["benign_cal"]), ("yeniden kalibrasyon", Sc["benign_cal"])]:
                    r = FZ.config_row(kind, cal, Sc["benign_test"], Sc["dev_test"], Sc["heldout_test"], cfg,
                                      three_way=True, model="ae", seed=seed)
                    del r["yapılandırma"]
                    r["görülmemiş_ANOMALY+UNCERTAIN"] = r["görülmemiş_ANOMALY"] + r["görülmemiş_UNCERTAIN"]
                    out["rob"].append({"bozulma": kind, "düzey": float(lv), "tekrar": r_i, "politika": pol, **r})

    # ---------------- Phase 9: ablation A1-A6, and risk-coverage for every model
    g = lambda d: (d["benign_cal"], d["benign_test"], d["dev_test"], d["heldout_test"])
    kw = dict(seed=seed, coll_ho=coll_ho)
    A, RC = [], []
    if iforest is not None:
        A.append(FZ.config_row("A1 · Isolation Forest", *g(iforest), cfg, three_way=False, model="iforest", **kw))
        RC += FZ.rc_rows("Isolation Forest", *g(iforest), cfg, model="iforest", seed=seed)
    A += [FZ.config_row("A2 · AE (ikili)", *g(base), cfg, three_way=False, model="ae", **kw),
          FZ.config_row("A3 · AE + seçici", *g(base), cfg, three_way=True, model="ae", **kw)]
    RC += FZ.rc_rows("AE merkezi", *g(base), cfg, model="ae", seed=seed)
    if latent is not None:
        RC += FZ.rc_rows("AE gizil skor", *g(latent), cfg, model="latent", seed=seed)
    RC += FZ.rc_rows("AE merkezi INT8", *g(Q8["Merkezi AE"]), cfg, model="int8", seed=seed)
    A.append(FZ.config_row("A3q · INT8 AE + seçici (merkezi)", *g(Q8["Merkezi AE"]), cfg, three_way=True, model="int8", **kw))
    for p in cfg.fl_final_protocols:
        sf, q8 = S32ALL[f"FedAvg-{iid} · {p}"], Q8[f"FedAvg-{iid} · {p}"]
        A += [FZ.config_row(f"A4 · Federe AE (ikili) · {p}", *g(sf), cfg, three_way=False, model="ae", **kw),
              FZ.config_row(f"A5 · Federe AE + seçici · {p}", *g(sf), cfg, three_way=True, model="ae", **kw),
              FZ.config_row(f"A6 · INT8 Federe AE + seçici · {p}", *g(q8), cfg, three_way=True, model="int8", **kw)]
        RC += FZ.rc_rows(f"Federe AE · {p}", *g(sf), cfg, model="ae", seed=seed)
        RC += FZ.rc_rows(f"Federe AE INT8 · {p}", *g(q8), cfg, model="int8", seed=seed)
    out["abl"], out["rc"] = A, RC
    return out


def collect(cache_dir: Path, seeds: list, fp: str) -> tuple[dict, list]:
    """Load the per-seed result files that exist. Returns ({key: DataFrame}, seeds done)."""
    import pandas as pd
    acc = {k: [] for k in KEYS}
    done = [s for s in seeds if (cache_dir / f"seed{s}_{fp}.json").exists()]
    for s in done:
        z = utils.load_json(cache_dir / f"seed{s}_{fp}.json")
        for k in KEYS:
            acc[k] += z.get(k, [])
    return {k: pd.DataFrame(v) for k, v in acc.items()}, done
