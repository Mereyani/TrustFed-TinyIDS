// ======================================================================================
// _core_en.js — English journal-style version of the core content (phases 1–9) of the
// TrustFed-TinyIDS report (rapor/_body.js, sections 3–8). Requires _head_en.js.
// Every number is produced by the same accessors (values.json) as the Turkish source.
//
// Functions (each pushes into the children array C passed by the assembler):
//   secFramework(C)        -> subsections 3.1–3.5   (Turkish §4.1–4.5)
//   secSetup(C)            -> subsections 5.1–5.5   (Turkish §3 and §4.6)
//   secResults(C)          -> subsections 6.1–6.11  (Turkish §5.1–5.11, all tables and figures)
//   secDiscussionCore(C)   -> paragraphs, no heading (Turkish §6)
//   secLimitationsCore(C)  -> bullets, no heading    (Turkish §7)
//   secConclusionCore(C)   -> paragraph + bullets, no heading (Turkish §8)
//   abstractCoreFacts      -> { key: { value, desc } } numbers the abstract may use
// Bullets use numbering reference "bul" (EN_NUMBERING in _head_en.js).
// ======================================================================================

// ---------- table builders (ported from rapor/_body.js, labels translated) ----------
const MLAB = { "Merkezi (yakınsama)": "Central", "FedAvg · orijinal": "FedAvg P1", "FedAvg · orijinal_kucuk_yigin": "FedAvg P2",
  "FedAvg · yakinsama_kalici": "FedAvg P3", "FedAvg · fedprox_kalici": "FedProx P4", "Yalnız yerel (yakınsama)": "Local only¹" };
const PKEY = { "FedAvg · orijinal": "orijinal", "FedAvg · orijinal_kucuk_yigin": "orijinal_kucuk_yigin", "FedAvg · yakinsama_kalici": "yakinsama_kalici", "FedAvg · fedprox_kalici": "fedprox_kalici" };
function flFull(k, cap, key) {
  const rows = [];
  for (const s of SCN) {
    for (const m of [KCENTRAL, ...PROT.map(FA)]) {
      const r = fl(k, KPOOL, s, m), pk = PKEY[m];
      rows.push([SCN_LAB[s], MLAB[m], pc(r.fpr_w, 2), pc(r.fpr_worst, 2), SD(r.ano, r.ano_sd), SD(r.kac, r.kac_sd), nf(r.f1, 3), nf(r.cov, 3), nf(r.sr, 3),
        pk ? nf(V[k].rounds[`${s}|${pk}`], 0) : "—", pk ? nf(V[k].comm[`${s}|${pk}`], 1) : "—"]);
    }
    const lr = V[k].tab[`${KCLIENT}|${s}|${KLOCAL}`];
    if (lr) rows.push([SCN_LAB[s], MLAB[KLOCAL], pc(lr.fpr_w, 2), pc(lr.fpr_worst, 2), SD(lr.ano, lr.ano_sd), SD(lr.kac, lr.kac_sd), nf(lr.f1, 3), nf(lr.cov, 3), nf(lr.sr, 3), "—", "—"]);
  }
  return table(["Split", "Model", "FPR (weighted)", "Worst-client FPR", "Recall (unseen)", "Missed", "F1", "Coverage", "Selective risk", "Rounds", "Communication (MB)"],
    rows, [1150, 1050, 800, 850, 1200, 1100, 650, 750, 750, 550, 788], cap,
    { key, note: "Pooled calibration (¹ local-only models: per-client calibration; run only for IID and Dirichlet 0.1). Recall = ANOMALY on unseen attacks. All metrics in this table are computed for each client (the client’s own normal test set + the shared known and unseen attack sets, α = 1%, β = 4%) and then averaged over the clients; coverage and selective risk therefore differ from the values in the ablation tables, which are computed on a single test set. Rounds and communication are means over 10 seeds; central and local models involve no communication (—)." });
}
const TLAB = { "Merkezi AE": "Central AE", "FedAvg-IID · orijinal": "FedAvg P1 (IID)", "FedAvg-IID · orijinal_kucuk_yigin": "FedAvg P2 (IID)",
  "FedAvg-IID · yakinsama_kalici": "FedAvg P3 (IID)", "FedAvg-IID · fedprox_kalici": "FedProx P4 (IID)" };
function tinyTab() {
  const rows = [];
  for (const [k, n] of [["F3", "53"], ["F4", "21"]]) for (const m of Object.keys(TLAB)) {
    const t = V[k].tiny[m];
    rows.push([`${TLAB[m]} · ${n}`, th(t.parametre), nf(t.tflite_fp32_KB), nf(t.tflite_int8_KB), nf(t.tahmini_RAM_KB_int8),
      `${nf(t["gecikme_fp32_µs_colab"], 2)} / ${nf(t["gecikme_int8_µs_colab"], 2)}`, `${nf(t.Spearman_FP32_INT8, 2)} (${nf(t.sp_min, 2)}–${nf(t.sp_max, 2)})`]);
  }
  return table(["Model · features", "Parameters", "TFLite FP32 (KB)", "TFLite INT8 (KB)", "Rough RAM, INT8 (KB)", "Latency FP32 / INT8 (µs, Colab CPU)", "Spearman FP32–INT8 (normal test)"],
    rows, [2238, 1000, 1100, 1100, 1100, 1600, 1500], "TinyML: model size, rough memory estimate, latency and score rank agreement (mean over 10 seeds)",
    { key: "tiny", note: "Latency was measured on the Colab CPU with a single sample; it is not a microcontroller value. The RAM estimate does not include the TFLite Micro working area. Spearman correlation was computed on the normal test scores only; in parentheses, the minimum–maximum across seeds." });
}
const RCLAB = { "Isolation Forest": "Isolation Forest", "AE gizil skor": "AE latent score (Mahalanobis)", "AE merkezi": "AE central", "AE merkezi INT8": "AE central INT8",
  "Federe AE · orijinal": "FedAvg P1", "Federe AE INT8 · orijinal": "FedAvg P1 INT8", "Federe AE · orijinal_kucuk_yigin": "FedAvg P2", "Federe AE INT8 · orijinal_kucuk_yigin": "FedAvg P2 INT8",
  "Federe AE · yakinsama_kalici": "FedAvg P3", "Federe AE INT8 · yakinsama_kalici": "FedAvg P3 INT8", "Federe AE · fedprox_kalici": "FedProx P4", "Federe AE INT8 · fedprox_kalici": "FedProx P4 INT8" };
function rcTab(k, cap, key) {
  const g = (m, y, c) => { const v = V[k].rc[`${m}|${y}|${c}`]; return v === null || v === undefined || Number.isNaN(Number(v)) ? "—" : nf(v, y === "test kümesi" ? 3 : 4); };
  const rows = Object.keys(RCLAB).filter((m) => V[k].rc[`${m}|test kümesi|0.70`] !== undefined)
    .map((m) => [RCLAB[m], ...["0.50", "0.70", "0.90", "1.00"].map((c) => g(m, "test kümesi", c)), ...["0.70", "0.90"].map((c) => g(m, "π=%1", c))]);
  return table(["Model (FL: IID)", "Coverage 0.5", "0.7", "0.9", "1.0", "π = 1% · 0.7", "π = 1% · 0.9"], rows, [2838, 1150, 1100, 1100, 1100, 1175, 1175], cap,
    { key, note: "Values are selective risk (lower is better); each curve was obtained by sweeping β with α = 1% fixed, read at fixed coverage levels and averaged over 10 seeds. Risk–coverage curves were computed only for the IID federated models; the coverage and selective risk of the non-IID federated models and the local models at α = 1%, β = 4% are given in the all-model tables of Sections 6.5 and 6.10." });
}
function robTab(k, cap, key) {
  const RBx = [["temiz", "0.0", "clean"], ["gürültü", "0.01", "noise σ = 0.01"], ["gürültü", "0.05", "noise σ = 0.05"], ["gürültü", "0.1", "noise σ = 0.10"],
    ["eksik", "0.05", "5% missing"], ["eksik", "0.1", "10% missing"], ["eksik", "0.2", "20% missing"], ["bozuk özellik", "1.0", "1 corrupted feature"], ["bozuk özellik", "3.0", "3 corrupted features"], ["bozuk özellik", "5.0", "5 corrupted features"]];
  const rows = RBx.map(([b, l, lab]) => { const d = rb(k, b, l, "devralınan eşik"), r = rb(k, b, l, "yeniden kalibrasyon");
    return [lab, nf(d.f1, 3), nf(d.cov, 3), nf(d.sr, 3), nf(r.f1, 3), nf(r.cov, 3), nf(r.sr, 3)]; });
  return table(["Corruption", "Inherited: F1", "Coverage", "Selective risk", "Recalibrated: F1", "Coverage", "Selective risk"], rows, [2038, 1300, 1250, 1250, 1300, 1250, 1250], cap,
    { key, note: "F1 for unseen attacks (ANOMALY = positive); coverage and selective risk on the test set. Mean over 10 seeds × 3 repetitions." });
}

// ======================================================================================
// 3.x  The TrustFed-TinyIDS framework (Turkish §4.1–4.5)
// ======================================================================================
function secFramework(C) {
  C.push(H2("3.1 Model and training"));
  C.push(P(`The flow-level detector is an autoencoder (AE) with the architecture 53 → 32 → 16 → 8 → 16 → 32 → 53 (${th(sl.ae_32_16_8.parametre)} parameters, ReLU, mean squared error loss, Adam, learning rate 0.001, batch size 512). The anomaly score s(x) of a flow x is the reconstruction error of the AE. This architecture was selected because, on the development data of the known attack families, it gave a higher PR-AUC than two alternatives (16-8-4, and 32-16-8 with dropout): ${nf(sl.ae_32_16_8.gelistirme_dogrulama_pr_auc, 3)}, versus ${nf(sl.ae_16_8_4.gelistirme_dogrulama_pr_auc, 3)} and ${nf(sl.ae_32_16_8_do.gelistirme_dogrulama_pr_auc, 3)}. Training is stopped by a convergence rule fixed in advance: stop when the best validation loss improves by less than 0.5% over 50 epochs; early stopping with a patience of 40 epochs; at most 1,500 epochs. Over the 10 seeds, training lasted ${Math.min(...ep10)}–${th(Math.max(...ep10))} epochs (${10 - capN} seeds stopped by the convergence rule and ${capN} by the cap).`));

  C.push(H2("3.2 Conformal p-value and three-way decision rule"));
  C.push(P("The score is converted into a p-value with respect to normal calibration data [@vovk2005alrw,bates2023outliers]. With s₁, …, sₙ the scores of the n normal calibration flows,"));
  C.push(EQ("p(x) = (1 + #{i : sᵢ ≥ s(x)}) / (n + 1),     n = 3,348,"));
  C.push(P("that is, one plus the number of calibration scores greater than or equal to s(x), divided by n plus one. If the calibration data and the normal test data come from the same distribution, the rule “alarm if p ≤ α” produces, on average, at most a fraction α of false alarms on normal traffic, and no attack labels are needed for this [@angelopoulos2023]. The three-way decision rule, in which UNCERTAIN defers the decision [@chow1970], is"));
  C.push(EQ("p ≤ 1% → ANOMALY,     1% < p ≤ 5% → UNCERTAIN,     p > 5% → NORMAL     (α = 1%, β = 4%)."));
  C.push(P("For models in which tied scores are frequent (Isolation Forest [@liu2008iforest], the latent score and INT8 models), a randomised p-value is used."));

  C.push(H2("3.3 UNCERTAIN resolution: host trust signal"));
  C.push(P("At the flow level, only ANOMALY produces an immediate alarm; UNCERTAIN decisions are not sent to the analyst but serve as input to a host counter. The counter counts the ANOMALY + UNCERTAIN decisions within a window of W flows of a host and escalates the host to the upper-level system when the count reaches k*. The threshold k* is calibrated on normal validation hosts for a target of at most 1 false escalation per device per week (a calibration target that is verified empirically, not guaranteed) (with F flows per day, the per-window budget is W / (7F)). The source IP is used as the host identifier, for grouping only. Because the data contain no timestamps, windows are drawn at random from the flows of a host; the host experiments are therefore simulations. In addition, a “gateway” step was evaluated that forwards UNCERTAIN flows to a Random Forest (RF) trained only on the known families."));

  C.push(H2("3.4 Federated learning"));
  C.push(P("The normal data were distributed across 5 clients in three ways: IID, and Dirichlet partitions over the service column with α_D = 1.0 and 0.1 [@hsu2019noniid]. Four training protocols, based on FedAvg [@mcmahan2017] and FedProx [@li2020fedprox], were compared:"));
  for (const p of PROT) C.push(B(`**${PLAB[p]}**`));
  C.push(P("P1 gives the same number of epochs (200) as a 200-epoch central reference model, but because each client sees one fifth of the data, the number of update steps is much smaller (~800 versus ~3,400); P2 equalises the number of steps with that reference. The central model reported in the results is trained with the convergence rule instead (733–1,500 epochs). P3 and P4 use the convergence rule of the central model (one round = 5 local epochs). In addition, local models trained by each client on its own data only were compared. Calibration was performed in two ways: **pooled calibration** (the clients send their normal calibration scores to the server; scores, not data, are shared) and **per-client calibration**."));

  C.push(H2("3.5 TinyML, robustness and ablation design"));
  C.push(P("The central model and the IID FedAvg models were converted to TFLite FP32 and INT8 [@jacob2018quant] (representative set of 500 normal training vectors). For INT8, three rules were compared: FP32 score and threshold; INT8 score with the inherited FP32 threshold; and recalibration on INT8 scores. For robustness, Gaussian noise (σ = 0.01–0.10), missing features (5–20%, median imputation) and corrupted features (the values of 1, 3 or 5 features shuffled across samples) were applied, with 3 repetitions; for each corruption, the inherited threshold was compared with recalibration on corrupted normal data. The ablation compared A1 Isolation Forest, A2 AE (binary), A3 AE + three-way decision, A3q INT8 AE + three-way decision, A4–A5 federated AE (binary / three-way decision) and A6 INT8 federated AE."));
}

// ======================================================================================
// 5.x  Experimental setup and evaluation protocol (Turkish §3 and §4.6)
// ======================================================================================
function secSetup(C) {
  C.push(H2("5.1 Dataset and preprocessing"));
  C.push(P(`The train_test_network.csv file of the TON_IoT network data [@moustafa2021toniot], part of the TON_IoT family of datasets [@alsaedi2020toniot], was used. The version used here consists of ${th(P14.data.rows)} rows and ${P14.data.cols} columns and contains no time column. The IP address and port columns were removed, as were text-valued columns such as the DNS query, HTTP and SSL fields. The data contain many duplicates: after removing identical rows and vectors that are identical after preprocessing, the ${th(P14.data.rows)} flows were reduced first to ${th(P14.data.after1)} and then to ${th(P14.data.after2)} unique vectors (e.g. only ${th(pt_.ransomware.after)} of the ${th(pt_.ransomware.before)} ransomware rows are distinct). Signed log(1 + x) and MinMax scaling were applied to the numerical columns and one-hot encoding to the categorical columns, and features with a mutual correlation above 0.98 were removed, leaving ${P14.data.n_feat} features. The scaler, the encoder and the correlation filter were fitted on the normal training data only.`));
  C.push(P("Some of the 53 features (the DNS, SSL and HTTP fields and the service label) require application-layer parsing, which assumes a Zeek-like flow extractor at the gateway. For constrained edge nodes, a separate **device feature set** was defined, consisting of 10 flow fields that can be counted from header and connection information alone, without parsing the packet payload (protocol, duration, byte and packet counts, connection state); after one-hot encoding it comprises 21 features."));

  C.push(H2("5.2 Data split"));
  C.push(...table(["Split", "Content", "Vectors"], [
    ["Normal training / validation", "normal", `${th(sp.benign_train)} / ${th(sp.benign_val)}`],
    ["Normal calibration / test", "normal", `${th(sp.benign_cal)} / ${th(sp.benign_test)}`],
    ["Known families (development / test)", "backdoor, ddos, dos, injection, password, scanning", `${th(sp.dev_val)} / ${th(sp.dev_test)}`],
    ["Unseen families (test only)", `ransomware (${th(sbt.heldout_test.ransomware)}), xss (${th(sbt.heldout_test.xss)}), mitm (${th(sbt.heldout_test.mitm)})`, th(sp.heldout_test)],
  ], [3000, 4638, 2000], "Data split (split seed 2027, fixed in all experiments)", { key: "split" }));
  C.push(P("The unseen families and the decision budgets were fixed in the project proposal, before the first run. The known families are not used to train the AE; they are used only for model-size selection, for training the Random Forest (RF) used for comparison, and for reporting."));

  C.push(H2("5.3 Leakage check"));
  const lk = fst("sızıntı - tümü", "bilinen"), lku = fst("sızıntı - tümü", "görülmemiş");
  C.push(P(`When the IP and port columns were added back to the model, recall on the known attacks at 1% false alarms increased by ${pt(lk.ortalama_fark)} points (in ${seedsOf(lk.kazanan_tohum)}; p_Holm = ${pv(lk.p_holm)}), whereas on the unseen attacks it did not change significantly (p_Holm = ${pv(lku.p_holm)}). This increase most likely stems from the address information of the machines rather than from attack behaviour [@arp2022]; these columns were therefore removed.`));

  C.push(H2("5.4 Evaluation protocol and statistical analysis"));
  C.push(P("The data split was kept fixed and 10 training seeds (0–9) were used; in each seed, the central model of that seed and the seed-dependent client split are used. Tables report the mean over the 10 seeds; for the main results, the ± standard deviation (in percentage points) is also given. Bootstrap 95% confidence intervals are provided in the summary CSV files of the output folders; paired comparisons use the Wilcoxon signed-rank test [@wilcoxon1945] with Holm correction (p_Holm) [@holm1979]. The intervals reflect training-seed variability only. A few comparisons that were not predefined in the notebooks were additionally computed from the same per-seed results; these are marked as “**additional test**”, and no Holm correction was applied to them. Because attacks form the majority of the test set, precision and selective risk are additionally reported re-weighted to a scenario in which attacks make up 1% of the traffic (π = 1%). Coverage is the fraction of decisions other than UNCERTAIN (automatic decisions); selective risk is the fraction of errors among the automatic decisions (an attack declared NORMAL or a normal flow declared ANOMALY) [@geifman2017]."));

  C.push(H2("5.5 Computing environment"));
  C.push(P("All training and evaluation runs of the framework (Sections 6.1–6.11) were performed on Google Colab with a Tesla T4 GPU, with a fixed data split and 10 training seeds (for LOFO, 10 separate seeds fixed in advance). All reported numbers are read automatically from the output files written by these runs. Environment: Google Colab, Tesla T4 GPU, TensorFlow 2.21.0, Python 3.13.16, NumPy 2.4.6, scikit-learn 1.6.1 (recorded in an environment.json file in each output folder). For one seed, the complete set of experiments of Sections 6.5–6.9 mostly took 21–24 minutes on the T4 (computed from file timestamps)."));
}

// ======================================================================================
// 6.x  Results (Turkish §5.1–5.11)
// ======================================================================================
function secResults(C) {
  // ---------------- 6.1
  C.push(H2("6.1 Baseline models and feature sets"));
  const aeU = b2("ae", "görülmemiş"), aeK = b2("ae", "bilinen"), ifU = b2("iforest", "görülmemiş"), ltU = b2("latent", "görülmemiş");
  C.push(...table(["Model (α = 1%)", "Normal FPR", "Recall unseen", "Recall known", "ROC-AUC unseen", "PR-AUC unseen"], [
    ["Isolation Forest", pc(ifU.fpr, 2), pc(ifU.recall), pc(b2("iforest", "bilinen").recall), nf(ifU.roc_auc, 3), nf(ifU.pr_auc, 3)],
    ["AE latent space (Mahalanobis)", pc(ltU.fpr, 2), pc(ltU.recall), pc(b2("latent", "bilinen").recall), nf(ltU.roc_auc, 3), nf(ltU.pr_auc, 3)],
    ["AE reconstruction error", pc(aeU.fpr, 2), pc(aeU.recall), pc(aeK.recall), nf(aeU.roc_auc, 3), nf(aeU.pr_auc, 3)],
  ], [2838, 1300, 1400, 1300, 1400, 1400], "Baseline models, binary decision p ≤ 1% (10 seeds)", { key: "baseline" }));
  const e200 = epo(200), e100 = epo(100), e1500 = epo(1500);
  // forward reference: the per-family figure is the next figure created (Section 6.2)
  C.push(P(`A high AUC does not imply usable detection: the ROC-AUC of Isolation Forest on the unseen families is ${nf(ifU.roc_auc, 2)}, yet at the 1% budget it flags no attack. At the same budget, the AE detects ${pc(aeU.recall)} of the unseen attacks but only ${pc(aeK.recall)} of the known attacks. Since all attacks are unseen from the point of view of the AE, this difference arises because known families such as injection and password closely resemble normal traffic (${figRef("families")}). Training length is also decisive: for seed 0, unseen recall is ${pc(e100["recall_görülmemiş"])} at 100 epochs, ${pc(e200["recall_görülmemiş"])} at 200 epochs and ${pc(e1500["recall_görülmemiş"])} at 1,500 epochs.`));
  const dK = fst("cihaz - tümü", "bilinen"), dU = fst("cihaz - tümü", "görülmemiş");
  C.push(P(`**Device feature set.** At 1% false alarms, the 21-feature set gave higher recall than the 53-feature set, by ${pt(dK.ortalama_fark)} points on the known families (in ${seedsOf(dK.kazanan_tohum)}; p_Holm = ${pv(dK.p_holm)}) and by ${pt(dU.ortalama_fark)} points on the unseen families (in ${seedsOf(dU.kazanan_tohum)}; p_Holm = ${pv(dU.p_holm)}). Dropping the application-layer fields therefore did not reduce detection. This set was taken through all the FL and INT8 experiments in Section 6.10.`));

  // ---------------- 6.2
  C.push(H2("6.2 Three-way rule: false-alarm guarantee and per-family decisions"));
  C.push(P(`When the normal calibration and test data were randomly re-split 200 times, the mean ANOMALY rate of the AE on normal traffic was ${pc(e1("ae", "ANOMALY").mean, 2)} and the UNCERTAIN rate ${pc(e1("ae", "UNCERTAIN").mean, 3)} (budgets 1% and 4.03%); for Isolation Forest and the latent score the rates also matched the budget (${pc(e1("iforest", "ANOMALY").mean, 2)} and ${pc(e1("latent", "ANOMALY").mean, 2)}). Because the guarantee holds on average, small deviations occur on the fixed test split (AE: ${pc(ab("F3", "A3 · AE + seçici", "normal_FPR").m, 2)}). The widely used μ+3σ threshold (mean of the training errors plus 3 standard deviations) promises 0.135% false alarms under a Gaussian assumption; in practice this rate is ${pc(P14.B3.B3_normal_ANOMALY.mean, 2)}, compared with ${pc(P14.B3.konformal_normal_ANOMALY.mean, 2)} for the conformal threshold (10 seeds).`));
  C.push(...figure("aile_kararlari.png", "Distribution of the three decisions for each family, AE, mean over 10 seeds. * family never used in training or model selection.", 6.5, { key: "families" }));
  const hm = e3("held-out", "macro-average");
  C.push(P(`Averaged over the unseen families (equal weight per family), ${pc(hm.anomaly_rate)} of the flows are ANOMALY, ${pc(hm.uncertain_rate)} UNCERTAIN and ${pc(hm.normal_rate)} NORMAL. The families behave very differently: ${pc(e3("held-out", "ransomware").uncertain_rate)} of ransomware flows are UNCERTAIN (the model is not certain about a single flow but is suspicious), ${pc(e3("held-out", "xss").anomaly_rate)} of xss flows are ANOMALY, and mitm is the hardest family (${pc(e3("held-out", "mitm").normal_rate)} NORMAL). Among the known families, injection (${pc(e3("known", "injection").normal_rate)}) and password (${pc(e3("known", "password").normal_rate)}) mostly receive a NORMAL decision. Vector-level (micro-averaged) rates differ because of the weight of xss: ${pc(F3m.ano)} of the unseen flows are ANOMALY and ${pc(F3m.kac)} NORMAL.`));

  // ---------------- 6.3
  C.push(H2("6.3 Selective detection: alarm and review load"));
  const tb = tierU("binary α=0.01"), t5_ = tierU("binary α+β=0.05"), t3w = tierU("three-way α=0.01, β=0.04");
  C.push(...table(["Rule (unseen families, attack share 1%)", "Immediate alarms / 10,000 flows", "Alarm precision", "Reviews / 10,000 flows", "Review precision", "Missed attacks"], [
    ["Binary, p ≤ 1%", nf(tb.alarms_per_flows, 0), nf(tb.precision_alarm_tier, 3), "—", "—", pc(tb.attack_missed)],
    ["Binary, p ≤ 5%", nf(t5_.alarms_per_flows, 0), nf(t5_.precision_alarm_tier, 3), "—", "—", pc(t5_.attack_missed)],
    ["Three-way (α = 1%, β = 4%)", nf(t3w.alarms_per_flows, 0), nf(t3w.precision_alarm_tier, 3), nf(t3w.reviews_per_flows, 0), nf(t3w.precision_review_tier, 3), pc(t3w.attack_missed)],
  ], [3038, 1400, 1200, 1400, 1200, 1400], "Alarm and review load (10 seeds)", { key: "tiering" }));
  C.push(P(`The immediate alarms of the three-way rule are identical to those of the binary p ≤ 1% rule, and ANOMALY and UNCERTAIN together flag the same flows as the binary p ≤ 5% rule. The three-way decision therefore adds no new detection power; it splits the flagged flows into two tiers: instead of the ${nf(t5_.alarms_per_flows, 0)} alarms of the binary p ≤ 5% rule, which achieves the same total detection, there are ${nf(t3w.alarms_per_flows, 0)} immediate alarms (precision ${nf(t3w.precision_alarm_tier, 3)}) and a review queue of ${nf(t3w.reviews_per_flows, 0)} flows (precision ${nf(t3w.precision_review_tier, 3)}). Because the precision of the queue is low, sending it directly to an analyst is not practical; the queue is therefore used as input to the host counter (Section 6.4).`));
  const eIF = e2r("test kümesi", "B1"), eLt = e2r("test kümesi", "B5"), eB3 = e2r("test kümesi", "B3"), eRnd = e2r("test kümesi", "rastgele");
  const eIF1 = e2r("0.01", "B1"), eLt1 = e2r("0.01", "B5");
  C.push(P(`**Does deferral carry information?** Compared with alternatives that defer the same number of flows (pre-specified primary analysis, test set), the selective risk of the conformal AE band is lower by ${nf(eIF.mean_delta_sr, 2)} than that of the Isolation Forest band, by ${nf(eLt.mean_delta_sr, 2)} than that of the latent-score band and by ${nf(eRnd.mean_delta_sr, 2)} than that of random deferral; it is higher by ${nf(-eB3.mean_delta_sr, 2)} than that of the μ+3σ band, because μ+3σ detects more attacks by exceeding the false-alarm budget. In the 1% scenario, in which attacks are rare (exploratory), the conformal AE gave a lower risk than all three alternatives (${nf(eLt1.mean_delta_sr, 3)} … ${nf(eIF1.mean_delta_sr, 3)}). In all comparisons the direction was the same in 10 of 10 seeds, p_Holm ≤ ${pv(Math.max(...P14.E2.map((r) => r.p_holm)))}.`));

  // ---------------- 6.4
  C.push(H2("6.4 Host trust signal and sparse attacks"));
  const rhos = [0.05, 0.1, 0.25, 0.5, 1.0], Ws = [20, 50, 100, 200];
  C.push(...table(["ρ", ...Ws.map((W) => `W = ${W}`)], rhos.map((r) => [r === 0.05 ? "≤ 0.05" : nf(r, 2),
    ...Ws.map((W) => { const a = f5(W, r); if (!a) return "—"; if (r === 0.05) { const vs = [0.01, 0.02, 0.05].map((x) => f5(W, x)).filter(Boolean); return pc(Math.max(...vs.map((q) => q.pencere_tespit_mean))); } return pc(a.pencere_tespit_mean); })]),
    [1638, 2000, 2000, 2000, 2000], "Host-window detection on the unseen families; ρ = share of attack flows in the window, ANOMALY + UNCERTAIN counter, F = 1,000 flows/day (10 seeds, simulation)",
    { key: "sparse", note: "The “≤ 0.05” row gives the highest value over the ρ values for which the window contains at least one attack flow. W = 500 was not used: only two normal hosts had enough flows for calibration, and 28.2% of the normal windows were escalated (target 7.1%); the high detection in this setting stems from false alarms." }));
  C.push(...figure("seyrek.png", "Detection by the host counter as a function of the attack share (unseen families, F = 1,000 flows/day, 10 seeds, simulation).", 5.8, { key: "sparse" }));
  const cw = (W) => V.F5.en_kotu_host[W] ? Object.values(V.F5.en_kotu_host[W]) : [];
  const okSeeds = (W) => cw(W).filter((v) => v <= 1).length;
  C.push(B(`**The counter is effective against dense attacks.** The immediate-alarm rate of ${pc(F3m.ano)} for a single flow becomes 100% escalation for hosts whose traffic is entirely malicious at W ≥ 50. When only ANOMALY is counted, this rate remains at ${pc(f5a(50, 1).pencere_tespit_mean)} at W = 50; UNCERTAIN decisions are therefore evidence that can accumulate.`));
  C.push(B(`**The counter is ineffective against sparse attacks.** When attack flows make up ≤ 5% of the traffic in the window, detection is 0%; at ρ = 10% it is at most ${pc(f5(200, 0.1).pencere_tespit_mean)}. The mechanism works only at ρ ≈ 25% and W ≥ 50 (${pc(f5(50, 0.25).pencere_tespit_mean)}–${pc(f5(200, 0.25).pencere_tespit_mean)}). This analysis was not pre-registered; it is exploratory.`));
  C.push(B(`**Cost on normal hosts.** Number of seeds in which the worst normal host stayed within the weekly budget: ${okSeeds(20)}/10 at W = 20, ${okSeeds(50)}/10 at W = 50, ${okSeeds(100)}/10 at W = 100 and ${okSeeds(200)}/10 at W = 200. Where the budget is exceeded, a single normal host appears persistently suspicious (350 false escalations per week at W = 20).`));
  const g = P14.gw;
  C.push(P(`**Gateway step (UNCERTAIN → RF).** Within the UNCERTAIN band, the RF separates attacks from normal flows well (AUC ${nf(g.mitm.auc, 3)}–${nf(g.ransomware.auc, 3)}). When the UNCERTAIN flows confirmed by the RF are added to the ANOMALY decisions of the AE, flow-level detection changed from ${pc(g.ransomware.ae)} to ${pc(g.ransomware.ae_gw)} for ransomware, from ${pc(g.xss.ae)} to ${pc(g.xss.ae_gw)} for xss and from ${pc(g.mitm.ae)} to ${pc(g.mitm.ae_gw)} for mitm, with a false-alarm rate of ${pc(g["normal (yanlış alarm)"].ae_gw)} on normal traffic. However, the RF alone detects these families at rates of ${pc(g.xss.rf)}–${pc(g.ransomware.rf)}; this was the first indication of the dataset limitation discussed in Section 6.11.`));

  // ---------------- 6.5
  C.push(H2("6.5 Federated learning: why can the federated model fall behind?"));
  C.push(P("A single-seed (seed 0) diagnostic experiment (31 training runs) was carried out first to test three hypotheses: **H1** the clients perform fewer update steps than the central model; **H2** the Adam state is reset in every round; **H3** non-IID clients drift apart from each other [@kairouz2021]."));
  C.push(...table(["Model (seed 0, IID, pooled calibration)", "Steps per client", "Unseen ANOMALY", "Missed"], [
    ["Central, until the convergence rule", "21,658", pc(F1.M_yak.ano), pc(F1.M_yak.kac)],
    ["Central, 200 epochs", "3,400", pc(F1.M_200.ano), pc(F1.M_200.kac)],
    ["Central, same number of steps as P1 (47 epochs)", "799", pc(F1.M_esit.ano), pc(F1.M_esit.kac)],
    ["FedAvg P1", "800", pc(F1.FL_orj.ano), pc(F1.FL_orj.kac)],
    ["FedAvg P2 (H1)", "3,400", pc(F1.FL_kucuk.ano), pc(F1.FL_kucuk.kac)],
    ["FedAvg, until the cap, Adam reset every round", "6,000", pc(F1.FL_reset.ano), pc(F1.FL_reset.kac)],
    ["FedAvg P3 (H1 + H2)", "6,000", pc(F1.FL_kalici.ano), pc(F1.FL_kalici.kac)],
    ["FedProx P4", "6,000", pc(F1.FL_prox.ano), pc(F1.FL_prox.kac)],
  ], [4400, 1600, 1838, 1800], "Diagnostic experiment (single seed)", { key: "fldiag" }));
  C.push(P(`The diagnosis supported H1 and H2 but also gave an important warning: when the same central training (200 epochs, same initial weights) was run with Keras and with the FL code using a single client, with only the batch order differing, the results were ${pc(F1.M_200.ano)} and ${pc(F1.K1_kalici.ano)}. This metric is highly volatile for under-trained models; the four protocols were therefore repeated with 10 seeds.`));
  C.push(...table(["Model", ...SCN.map((s) => SCN_LAB[s])], [
    ["Central (convergence rule)", ...SCN.map((s) => cellAK("F3", KPOOL, s, KCENTRAL))],
    ...PROT.map((p) => [PLAB[p], ...SCN.map((s) => cellAK("F3", KPOOL, s, FA(p)))]),
  ], [3838, 1933, 1933, 1934], "ANOMALY on unseen attacks (missed in parentheses), 53 features, 10 seeds, pooled calibration", { key: "flmain", note: "The central model is not affected by the client split; the same value is therefore repeated in every column." }));
  C.push(...figure("fl_merkezi.png", "ANOMALY rate on unseen attacks; bar = mean over 10 seeds, dot = single seed. Left: 53 features; right: 21-feature device model. Pooled calibration.", 6.5, { key: "flcentral" }));
  const tO = t3("IID", "orijinal"), tK = t3("IID", "orijinal_kucuk_yigin"), tY = t3("IID", "yakinsama_kalici");
  const kY = own("F3", "kac|IID|yakinsama_kalici"), h1 = own("F3", "H1|IID"), h1d = own("F3", "H1|Dirichlet=0.1");
  const px = (s) => own("F3", `prox|${s}`);
  C.push(B(`**The gap with P1 is large and consistent:** in IID, ${pc(fl("F3", KPOOL, "IID", FA("orijinal")).ano)} (P1) versus ${pc(F3m.ano)} (central); the central model is higher in ${seedsOf(tO.a_buyuk)} (p_Holm = ${pv(tO.p_holm)}).`));
  C.push(B(`**H1 explains most of the gap, but not all of it.** When the number of steps is equalised (P2), ANOMALY increases by ${pt(h1.fark)} points (in ${seedsOf(h1.a_buyuk)}; additional test p = ${pv(h1.p)}) but remains ${pt(tK.fark)} points below the central model (p_Holm = ${pv(tK.p_holm)}). The single-seed result (${pc(F1.FL_kucuk.ano)}) was optimistic.`));
  C.push(B(`**With equivalent training, the IID gap largely closes.** P3 reaches ${pc(fl("F3", KPOOL, "IID", FA("yakinsama_kalici")).ano)} and the central model ${pc(F3m.ano)}: the difference is ${pt(tY.fark)} points, the central model is higher in ${seedsOf(tY.a_buyuk)}, and the difference is not significant (p_Holm = ${pv(tY.p_holm)}). The missed rate, however, remains ${pt(kY.fark)} points higher in FL (in ${seedsOf(kY.a_buyuk)}; additional test p = ${pv(kY.p)}).`));
  C.push(B(`**Under non-IID partitions the gap persists (H3).** P3 reaches ${pc(fl("F3", KPOOL, "Dirichlet=1.0", FA("yakinsama_kalici")).ano)} at Dirichlet 1.0 (p_Holm = ${pv(t3("Dirichlet=1.0", "yakinsama_kalici").p_holm)}) and ${pc(fl("F3", KPOOL, "Dirichlet=0.1", FA("yakinsama_kalici")).ano)} at Dirichlet 0.1 (p_Holm = ${pv(t3("Dirichlet=0.1", "yakinsama_kalici").p_holm)}). Equalising the number of steps gave no consistent improvement at Dirichlet 0.1 (+${pt(h1d.fark)} points, in ${seedsOf(h1d.a_buyuk)}; additional test p = ${pv(h1d.p)}).`));
  C.push(B(`**FedProx (μ = 0.01) gave no consistent improvement:** relative to P3, the difference is ${nf(100 * px("IID").fark)} points in IID, ${nf(100 * px("Dirichlet=1.0").fark)} at Dirichlet 1.0 and +${nf(100 * px("Dirichlet=0.1").fark)} at Dirichlet 0.1 (in the last case better in only ${seedsOf(px("Dirichlet=0.1").a_buyuk)}; additional test p = ${pv(px("Dirichlet=0.1").p)}). Only μ = 0.01 was tested.`));
  C.push(...flFull("F3", "All federated, central and local models, 53 features (mean over 10 seeds; ± standard deviation)", "flfull53"));
  const v3 = vh["F3|IID|yakinsama_kalici"], v4 = vh["F4|IID|yakinsama_kalici"];
  C.push(P(`**Convergence.** In IID, the P3 and P4 runs stopped at the cap of 300 rounds (1,500 epochs) in all 10 seeds. According to the validation losses recorded in every round, none of the ${V.valhist_all_cap.n} federated runs that reached the cap had fallen below the convergence threshold: the improvement over the last 50 epochs was ${pc(v3.r10_min, 2)}–${pc(v3.r10_max, 2)} for 53 features and ${pc(v4.r10_min, 2)}–${pc(v4.r10_max, 2)} for 21 features (threshold 0.5%). These models are therefore referred to as “trained until the cap”; whether the small remaining IID gap would close with longer training cannot be determined from these experiments.`));
  C.push(...figure("val_hist.png", "Best validation loss of the P3 and P4 runs on the IID split (each line is one seed). The curves are still decreasing at the 1,500-epoch cap.", 6.5, { key: "valhist" }));
  C.push(P(`**Summary for federated learning.** The main reason why the federated model appears weaker is insufficient training: an equal number of epochs means ~4 times fewer update steps for the clients, and an Adam state reset in every round slows training down. Under equivalent conditions in IID, the ANOMALY gap is no longer significant (${pc(fl("F3", KPOOL, "IID", FA("yakinsama_kalici")).ano)} / ${pc(F3m.ano)}), while a small gap of ${pt(kY.fark)} points remains in missed attacks. Under strong non-IID partitions there is a real gap, and FedProx (μ = 0.01) does not close it. In the 21-feature model, no gap arises at all (Section 6.10).`));

  // ---------------- 6.6
  C.push(H2("6.6 Calibration in federated learning and local-only models"));
  const w01 = PROT.map((p) => fl("F3", KPOOL, "Dirichlet=0.1", FA(p)));
  const y01a = own("F3", "yerel|Dirichlet=0.1|görülmemiş_ANOMALY");
  C.push(P(`Pooled calibration keeps the weighted FPR around α (0.6–1.1%), but at Dirichlet 0.1 the FPR of the worst client of the federated models is ${pc(Math.min(...w01.map((r) => r.fpr_worst)))}–${pc(Math.max(...w01.map((r) => r.fpr_worst)))} on average and ${pc(Math.max(...w01.map((r) => r.fpr_worst_max)))} in the worst seed. These clients are very small (only 4 normal test vectors in one seed). Per-client calibration keeps the worst client at ≤ 2.2% for the federated models but reduces detection. With this calibration, under strong non-IID partitions, the per-client local-only models outperform FedAvg: unseen ANOMALY ${pc(fl("F3", KCLIENT, "Dirichlet=0.1", KLOCAL).ano)} (local only) versus ${pc(fl("F3", KCLIENT, "Dirichlet=0.1", FA("yakinsama_kalici")).ano)} (FedAvg P3) (in ${seedsOf(y01a.a_buyuk)}; additional test p = ${pv(y01a.p)}), missed ${pc(fl("F3", KCLIENT, "Dirichlet=0.1", KLOCAL).kac)} versus ${pc(fl("F3", KCLIENT, "Dirichlet=0.1", FA("yakinsama_kalici")).kac)}. In IID, by contrast, FedAvg misses fewer attacks. Detailed results for every seed, model, split, calibration and client are available in the per-client result files of the output folders (53- and 21-feature models); the worst client is summarised here.`));

  // ---------------- 6.7
  C.push(H2("6.7 TinyML and threshold validity in INT8"));
  const i4d = i8("F4", "Merkezi AE", "INT8 skor + devralınan FP32 eşik"), i4r = i8("F4", "Merkezi AE", "INT8 skor + INT8 yeniden kalibrasyon"), i4f = i8("F4", "Merkezi AE", "FP32 skor + FP32 eşik");
  const i3d = i8("F3", "Merkezi AE", "INT8 skor + devralınan FP32 eşik"), i3r = i8("F3", "Merkezi AE", "INT8 skor + INT8 yeniden kalibrasyon"), i3f = i8("F3", "Merkezi AE", "FP32 skor + FP32 eşik");
  C.push(P(`The INT8 model occupies ${nf(tinyC("F3").tflite_int8_KB)} KB for 53 features (FP32 TFLite: ${nf(tinyC("F3").tflite_fp32_KB)} KB) and ${nf(tinyC("F4").tflite_int8_KB)} KB for 21 features; the rough RAM estimates are ${nf(tinyC("F3").tahmini_RAM_KB_int8)} and ${nf(tinyC("F4").tahmini_RAM_KB_int8)} KB. These values are below the RAM of typical TinyML microcontrollers, which ranges from tens to a few hundred KB [@banbury2021mlperftiny]; however, the estimate does not include the TFLite Micro working area. Latency was measured on the Colab CPU (INT8 ≈ ${nf(tinyC("F3").gecikme_int8_µs_colab, 2)} µs); it is not a microcontroller value.`));
  C.push(...tinyTab());
  C.push(...table(["Central AE", "53 feat.: FPR", "53 feat.: normal UNCERTAIN", "21 feat.: FPR", "21 feat.: normal UNCERTAIN"], [
    ["FP32 score + FP32 threshold", pc(i3f.fpr, 2), pc(i3f.unc), pc(i4f.fpr, 2), pc(i4f.unc)],
    ["INT8 score + inherited FP32 threshold", `${pc(i3d.fpr, 2)} (max ${pc(i3d.fpr_max, 2)})`, `${pc(i3d.unc)} (${pc(i3d.unc_min)}–${pc(i3d.unc_max)})`, `**${pc(i4d.fpr, 2)}** (max ${pc(i4d.fpr_max, 2)})`, `**${pc(i4d.unc)}** (${pc(i4d.unc_min)}–${pc(i4d.unc_max)})`],
    ["INT8 score + recalibration with INT8", pc(i3r.fpr, 2), pc(i3r.unc), pc(i4r.fpr, 2), pc(i4r.unc)],
  ], [2838, 1500, 1900, 1500, 1900], "Validity of FP32-computed thresholds in the INT8 model (10 seeds; target FPR ≤ 1%, UNCERTAIN ≈ 4%)", { key: "int8" }));
  C.push(...figure("int8_esik.png", "UNCERTAIN rate on normal traffic, each dot is one seed (central model). Dashed line: β = 4%.", 5.8, { key: "int8" }));
  const kq = V.own_device.kac_int8_eksi_fp32_cihaz;
  C.push(P(`The FP32 thresholds remained valid for ANOMALY in the 53-feature model, but the UNCERTAIN band shifted (${pc(i3f.unc)} → ${pc(i3d.unc)}). In the 21-feature model both thresholds broke: the false-alarm rate exceeded α and most of the normal traffic fell into UNCERTAIN. Recalibration with INT8 scores restored the budget in both models; the cost is an increase of ${pt(kq.fark)} points in the missed-attack rate of the device model (in ${seedsOf(kq.a_buyuk)}; additional test p = ${pv(kq.p)}). The FedAvg-IID models were less affected by INT8. For the central model, the rank correlation (Spearman) between FP32 and INT8 scores on normal traffic is ${nf(tinyC("F3").Spearman_FP32_INT8, 2)} for 53 features and ${nf(tinyC("F4").Spearman_FP32_INT8, 2)} for 21 features.`));

  // ---------------- 6.8
  C.push(H2("6.8 Corrupted input"));
  const RB = [["temiz", 0, "clean"], ["gürültü", 0.01, "noise σ = 0.01"], ["gürültü", 0.05, "noise σ = 0.05"], ["gürültü", 0.1, "noise σ = 0.10"],
    ["eksik", 0.05, "5% missing features"], ["eksik", 0.2, "20% missing features"], ["bozuk özellik", 1, "1 corrupted feature"], ["bozuk özellik", 5, "5 corrupted features"]];
  const rbRow = (b, l, lab) => { const lv = b === "bozuk özellik" ? `${l}.0` : (l === 0 ? "0.0" : String(l));
    const d3 = rb("F3", b, lv, "devralınan eşik"), r3 = rb("F3", b, lv, "yeniden kalibrasyon"), d4 = rb("F4", b, lv, "devralınan eşik"), r4 = rb("F4", b, lv, "yeniden kalibrasyon");
    return [lab, pc(d3.fpr), `${pc(r3.fpr)} / ${pc(r3.kac)}`, pc(d4.fpr), `${pc(r4.fpr)} / ${pc(r4.kac)}`]; };
  C.push(...table(["Corruption", "53 feat.: inherited threshold FPR", "53 feat.: recalibrated FPR / missed", "21 feat.: inherited threshold FPR", "21 feat.: recalibrated FPR / missed"],
    RB.map(([b, l, lab]) => rbRow(b, l, lab)), [2038, 1700, 2000, 1900, 2000], "Central AE under corrupted input (10 seeds × 3 repetitions)", { key: "robfpr" }));
  C.push(...robTab("F3", "F1, coverage and selective risk under corrupted input, 53-feature central AE", "rob53"));
  C.push(...robTab("F4", "F1, coverage and selective risk under corrupted input, 21-feature central AE", "rob21"));
  C.push(P("The inherited threshold breaks down even under small corruptions; the device model is more sensitive to noise. Recalibration with normal data subjected to the same corruption brings the false-alarm rate back to around 1%, but in that case most attacks are missed. Recalibration restores the guarantee, not the detection; moreover, normal data subjected to the same corruption may not always be available in the field."));

  // ---------------- 6.9
  C.push(H2("6.9 Ablation and risk–coverage for all models"));
  const AB = [["A1 · Isolation Forest", "A1 · Isolation Forest"], ["A2 · AE (ikili)", "A2 · AE (binary)"], ["A3 · AE + seçici", "A3 · AE + three-way"],
    ["A3q · INT8 AE + seçici (merkezi)", "A3q · INT8 AE + three-way"], ["A5 · Federe AE + seçici · orijinal", "A5 · FedAvg P1 + three-way"],
    ["A5 · Federe AE + seçici · orijinal_kucuk_yigin", "A5 · FedAvg P2 + three-way"], ["A4 · Federe AE (ikili) · yakinsama_kalici", "A4 · FedAvg P3, binary"],
    ["A5 · Federe AE + seçici · yakinsama_kalici", "A5 · FedAvg P3 + three-way"], ["A6 · INT8 Federe AE + seçici · yakinsama_kalici", "A6 · INT8 FedAvg P3 + three-way"],
    ["A5 · Federe AE + seçici · fedprox_kalici", "A5 · FedProx P4 + three-way"]];
  const abRow = (k, key, lab) => { const g2 = (m) => ab(k, key, m); if (!g2("normal_FPR")) return null;
    return [lab, pc(g2("normal_FPR").m, 2), SD(g2("recall_görülmemiş").m, g2("recall_görülmemiş").sd), SD(g2("görülmemiş_kaçan").m, g2("görülmemiş_kaçan").sd), g2("f1_görülmemiş") && g2("f1_görülmemiş").m !== null ? nf(g2("f1_görülmemiş").m, 3) : "—",
      nf(g2("coverage").m, 3), nf(g2("selective_risk").m, 3), nf(g2("selective_risk_π=%1").m, 4)]; };
  const hdr = ["Configuration (FL: IID)", "FPR", "Recall (unseen)", "Missed", "F1", "Coverage", "Selective risk", "Selective risk π = 1%"], wd = [3238, 800, 1000, 800, 700, 900, 1000, 1200];
  C.push(...table(hdr, AB.map(([k, l]) => abRow("F3", k, l)).filter(Boolean), wd, "Ablation, 53-feature models, mean over 10 seeds (± standard deviation)", { key: "abl53", note: "Recall = ANOMALY rate on unseen attacks. Selective risk is given on the test set and re-weighted to an attack share of 1%." }));
  C.push(...table(hdr, AB.map(([k, l]) => abRow("F4", k, l)).filter(Boolean), wd, "Ablation, 21-feature models, mean over 10 seeds (± standard deviation; Isolation Forest was not run for the 21-feature set)", { key: "abl21" }));
  const a23 = V.F3.abl_tests["A3 · AE + seçici||A2 · AE (ikili)||selective_risk"];
  C.push(P(`The three-way rule (deferral through UNCERTAIN) reduced the selective risk in 10 of 10 seeds for all AE-based models with 53 and 21 features (e.g. for the central AE, ${nf(ab("F3", "A2 · AE (ikili)", "selective_risk").m, 3)} → ${nf(ab("F3", "A3 · AE + seçici", "selective_risk").m, 3)}; p_Holm = ${pv(a23.p_holm)}). For the 53-feature models, INT8 conversion (A3 → A3q, A5 → A6) did not change the results significantly; the effect on the 21-feature device model is reported in Section 6.7. Isolation Forest flagged no attack at the 1% budget and produced ${pc(V.F3.iforest_fpr.min, 2)}–${pc(V.F3.iforest_fpr.max, 2)} false alarms on normal traffic. The selective risk is high on the test set because attacks are the majority and attacks that look normal receive a “confident” NORMAL decision; when re-weighted to an attack share of 1%, the selective risks of the AE-based models converge to approximately the range 0.010–0.019.`));
  C.push(...rcTab("F3", "Risk–coverage: selective risk at fixed coverage levels for all 53-feature models (10 seeds)", "rc53"));
  C.push(...rcTab("F4", "Risk–coverage: selective risk at fixed coverage levels for all 21-feature models (10 seeds)", "rc21"));
  C.push(...figure("risk_kapsama.png", "Risk–coverage curves (α fixed, β swept; test set; mean over 10 seeds). The federated models are from the IID split.", 6.5, { key: "rc" }));

  // ---------------- 6.10
  C.push(H2("6.10 The 21-feature device model: federated learning and INT8"));
  const cDev = V.F4.cihaz_tumu;
  const dAno = cDev["A3 · AE + seçici | cihaz||görülmemiş_ANOMALY"], dBil = cDev["A3 · AE + seçici | cihaz||bilinen_ANOMALY"], dSr = cDev["A3 · AE + seçici | cihaz||selective_risk"];
  const dKac = V.own_device.kac_cihaz_eksi_tumu;
  C.push(P("All experiments of Sections 6.5–6.9 were also run for the 21-feature device model, with the same rows, the same code and the same protocols."));
  C.push(...table(["Measure (central AE + three-way)", "53 features", "21 features", "Difference"], [
    ["Parameters", th(V.F3.tiny["Merkezi AE"].parametre), th(V.F4.tiny["Merkezi AE"].parametre), ""],
    ["TFLite INT8 / FP32 (KB)", `${nf(tinyC("F3").tflite_int8_KB)} / ${nf(tinyC("F3").tflite_fp32_KB)}`, `${nf(tinyC("F4").tflite_int8_KB)} / ${nf(tinyC("F4").tflite_fp32_KB)}`, ""],
    ["Unseen ANOMALY", pc(ab("F3", "A3 · AE + seçici", "görülmemiş_ANOMALY").m), pc(ab("F4", "A3 · AE + seçici", "görülmemiş_ANOMALY").m), `+${pt(dAno.fark)} points, ${dAno.a_buyuk}/10, p_Holm = ${pv(dAno.p_holm)}`],
    ["Unseen missed", pc(ab("F3", "A3 · AE + seçici", "görülmemiş_kaçan").m), pc(ab("F4", "A3 · AE + seçici", "görülmemiş_kaçan").m), `+${pt(dKac.fark)} points, ${dKac.a_buyuk}/10, additional test p = ${pv(dKac.p)}`],
    ["Known ANOMALY", pc(ab("F3", "A3 · AE + seçici", "bilinen_ANOMALY").m), pc(ab("F4", "A3 · AE + seçici", "bilinen_ANOMALY").m), `+${pt(dBil.fark)} points, ${dBil.a_buyuk}/10, p_Holm = ${pv(dBil.p_holm)}`],
    ["Normal FPR", pc(ab("F3", "A3 · AE + seçici", "normal_FPR").m, 2), pc(ab("F4", "A3 · AE + seçici", "normal_FPR").m, 2), "not significant"],
    ["Selective risk (test set)", nf(ab("F3", "A3 · AE + seçici", "selective_risk").m, 3), nf(ab("F4", "A3 · AE + seçici", "selective_risk").m, 3), `${nf(dSr.fark, 3)}, ${10 - dSr.a_buyuk}/10 lower, p_Holm = ${pv(dSr.p_holm)}`],
  ], [3000, 1700, 1700, 3238], "Central models with 53 and 21 features (10 seeds)", { key: "device" }));
  const t4max = Math.max(...SCN.flatMap((s) => PROT.map((p) => t4(s, p).p_holm)));
  const t4min = Math.min(...SCN.flatMap((s) => PROT.map((p) => t4(s, p).p_holm)));
  C.push(P(`Despite being smaller, the device model is not worse on unseen attacks: it flags more attacks as ANOMALY and defers fewer, and the missed rates are close. **In federated learning, there is no significant difference in unseen ANOMALY between the central and federated models under any condition** (12 comparisons, p_Holm ${nf(t4min, 2)}–${nf(t4max, 2)}; ${figRef("flcentral")}, right): even P1 gives the same result as the central model (IID: ${pc(fl("F4", KPOOL, "IID", FA("orijinal")).ano)} / ${pc(F4m.ano)}), and at Dirichlet 0.1 the federated models reach ${pc(Math.min(...PROT.map((p) => fl("F4", KPOOL, "Dirichlet=0.1", FA(p)).ano)))}–${pc(Math.max(...PROT.map((p) => fl("F4", KPOOL, "Dirichlet=0.1", FA(p)).ano)))}. A gap appears only on the known families. The validation loss of the device model is very low under all protocols, which suggests that the learning problem is easier and that few steps suffice (not tested separately). In INT8, by contrast, recalibration of the thresholds is mandatory (Section 6.7). Note: with these 21 features, ${pc(V.F4.seen.benign_test)} of the normal test vectors are identical to a vector in the training data; the effect of this on the FPR was not measured.`));
  C.push(...flFull("F4", "All federated, central and local models, 21 features (mean over 10 seeds; ± standard deviation)", "flfull21"));

  // ---------------- 6.11
  C.push(H2("6.11 Leaving out each attack family in turn (LOFO)"));
  C.push(P(`To ensure that the “unseen attack” claim does not depend on the three chosen families, each family was left out in turn following a pre-registered design: 9 folds, in each of which one family is unseen and the other eight are known; 10 separate seeds (10–19). Since the AE is trained on normal traffic only, its result does not change across folds; what changes is the RF trained on the other eight families. All 10 AEs stopped by the convergence rule (${V.F2.ae_epoch[0]}–${th(V.F2.ae_epoch[1])} epochs).`));
  C.push(P("**Success criterion (pre-registered):** AE + host counter must reduce the “missed + deferred” rate at ρ = 1 by at least 30 points while the worst normal host stays within the weekly budget, and this must hold in at least 6 of the 9 folds. **Failure criterion:** if, for families that are dissimilar to the known ones (RF recall < 0.50), the RF alone matches AE + counter (difference ≤ 0.05), the “normal traffic only” claim is withdrawn."));
  C.push(...table(["W (flows)", "F = 1,000 flows/day", "F = 5,000 flows/day", "Criterion"],
    [20, 50, 100].map((W) => [String(W), `${f2ok(W, 1000).başarılı_katman} / 9`, `${f2ok(W, 5000).başarılı_katman} / 9`,
      f2ok(W, 1000).başarı_ölçütü_sağlandı && f2ok(W, 5000).başarı_ölçütü_sağlandı ? "met" : "**not met**"]),
    [1800, 2600, 2600, 2638], "Number of folds meeting the LOFO success criterion (10 seeds)", { key: "lofo" }));
  C.push(...figure("lofo.png", "W = 50, F = 1,000 flows/day: single-flow ANOMALY rate of the AE on the left-out family, single-flow recall of the RF trained on the other eight families, and host detection by AE + host counter at ρ = 1 (10 seeds).", 6.5, { key: "lofo" }));
  const fam = V.F2.aile_W50_F1000, rfr = minmax(fam.map((r) => r["RF_tek_recall_α"]));
  const inj = fam.find((r) => r.aile === "injection"), ddos = fam.find((r) => r.aile === "ddos");
  C.push(B("**At W = 20 the criterion was not met:** in every seed, a single normal host was escalated in every window (350 false escalations per week, budget 1)."));
  C.push(B(`**ddos was not counted as a success in any setting;** the reason is a ceiling effect: since the AE already gives ${pc(ddos.AE_ANOMALY)} ANOMALY on single flows, an improvement of 30 points is not possible. The weakest family is injection (host detection ${pc(inj["karisik_ρ=1.00"])} at W = 50, F = 1,000, ρ = 1).`));
  C.push(B(`**The failure criterion could not be tested:** the RF detected each left-out family at rates of ${pc(rfr[0])}–${pc(rfr[1])}; by this definition, no family “dissimilar” to the known ones exists in TON_IoT. In addition, the RF reaches the level of AE + counter for backdoor, ransomware, scanning and injection.`));
  C.push(P("**Summary for LOFO.** The pre-registered success criterion was met at W = 50 and 100 and not met at W = 20. In TON_IoT, every family is sufficiently similar to the other eight; here, “unseen” means only “a family not used in training”, not “an attack dissimilar to the known ones”. This is a finding about the dataset, not a success or failure of the method; another dataset is required to demonstrate the value of learning from normal traffic alone for genuinely new attacks."));
}

// ======================================================================================
// Discussion / limitations / conclusion bodies (no headings; Turkish §6, §7, §8)
// ======================================================================================
function secDiscussionCore(C) {
  C.push(P("The main lesson drawn from the results is that the conformal threshold keeps the promised false-alarm rate under the condition in which it was computed and, instead of silently missing most new attacks, separates them into a distinct queue. This guarantee, however, does not transfer automatically to another condition: it broke under INT8 for the device model, for small clients under non-IID partitions, and under corrupted input. For IoT, this means that each device or client must validate its threshold under its own condition and recalibrate it if necessary."));
  C.push(P("Operationally, the hierarchical filter between the flow and host levels turns UNCERTAIN decisions from a burden on the analyst into evidence about the trustworthiness of hosts that can accumulate; this, however, works only when the attack makes up a substantial part of the traffic of the host. From the perspective of the edge node, the 21-feature device model provides at least the same detection without application-layer parsing, is unaffected by federated training, and its INT8 size is below the typical capacity of microcontrollers. In federated learning, a fair comparison requires equalising the number of update steps and the optimiser state rather than the number of epochs; under strong non-IID partitions, local models can outperform the federated model."));
}
function secLimitationsCore(C) {
  C.push(B("In TON_IoT, the “unseen” families resemble the known ones (Section 6.11). The value of learning from normal traffic alone for genuinely new attacks cannot be demonstrated with these data [@sommer2010]."));
  C.push(B("Most federated runs stopped at the 1,500-epoch cap while the validation loss was still decreasing; for FedProx, only μ = 0.01 was tested."));
  C.push(B("The FL clients are not real devices; the normal data were split across five clients according to the service column. At Dirichlet 0.1 some clients are very small, so the client FPRs are coarse."));
  C.push(B("The host-counter and sparse-attack experiments are simulations (the data contain no timestamps); the sparse-attack analysis was not pre-registered. The original counter only counts evidence within a window, with no update that discounts old evidence; Phase 10 evaluates such updates (Section 6.12.5)."));
  C.push(B("Latency was measured on the Colab CPU, and RAM is only a rough estimate; no measurement was made on a real microcontroller. The flow-extraction cost of the device feature set was not measured either."));
  C.push(B("Confidence intervals reflect training-seed variability only; the data split was kept fixed. No Holm correction was applied to the comparisons marked as “additional test”."));
}
function secConclusionCore(C) {
  C.push(P(`A three-way detector built from an AE with ${th(sl.ae_32_16_8.parametre)} parameters, trained on normal traffic only, and two conformal thresholds keeps the 1% false-alarm budget on normal traffic while flagging ${pc(F3m.ano)} of the unseen attack flows as immediate alarms, missing ${pc(F3m.kac)} and deferring the remainder; when the deferred flows are accumulated at the host level, hosts carrying dense attacks are detected. The system also operates in federated and INT8 form; however, the thresholds must be validated under every new condition.`));
  C.push(P("Future work:", { after: 60 }));
  C.push(B("Testing the unseen-attack claim on a second dataset (e.g. Edge-IIoTset)."));
  C.push(B("Continuing federated training without a cap until actual convergence; trying other μ values and client-specific layers for non-IID partitions."));
  C.push(B("Making post-INT8 recalibration a default step for the device model; measuring latency and memory on a real microcontroller."));
  C.push(B("Per-host (Mondrian) calibration, evidence decay and sequential accumulation for sparse attacks; these are evaluated in Phase 10 (Section 6.12)."));
}

// ======================================================================================
// Key numbers for the abstract (all from the same accessors; English formatting)
// ======================================================================================
const abstractCoreFacts = (() => {
  const P3 = (s) => fl("F3", KPOOL, s, FA("yakinsama_kalici"));
  const tY = t3("IID", "yakinsama_kalici"), tO = t3("IID", "orijinal"), kY = own("F3", "kac|IID|yakinsama_kalici");
  const i4d = i8("F4", "Merkezi AE", "INT8 skor + devralınan FP32 eşik"), i4r = i8("F4", "Merkezi AE", "INT8 skor + INT8 yeniden kalibrasyon");
  const kq = V.own_device.kac_int8_eksi_fp32_cihaz;
  const t4p = SCN.flatMap((s) => PROT.map((p) => t4(s, p).p_holm));
  const fam = V.F2.aile_W50_F1000, rfr = minmax(fam.map((r) => r["RF_tek_recall_α"]));
  const f = (value, desc) => ({ value, desc });
  return {
    aeParams: f(th(sl.ae_32_16_8.parametre), "Parameters of the 53-feature AE (53-32-16-8-16-32-53)."),
    normalAnomalyRate: f(pc(e1("ae", "ANOMALY").mean, 2), "AE ANOMALY rate on normal traffic over 200 calibration/test re-splits (budget 1%)."),
    normalUncertainRate: f(pc(e1("ae", "UNCERTAIN").mean, 2), "AE UNCERTAIN rate on normal traffic over 200 re-splits (budget 4.03%)."),
    centralUnseenAnomaly: f(pc(F3m.ano), "Central 53-feature AE: share of unseen-family flows (ransomware, xss, mitm) declared ANOMALY (vector level, pooled calibration, mean of 10 seeds)."),
    centralUnseenUncertain: f(pc(ab("F3", "A3 · AE + seçici", "görülmemiş_UNCERTAIN").m), "Central 53-feature AE: share of unseen-family flows declared UNCERTAIN (ablation A3, 10 seeds)."),
    centralUnseenMissed: f(pc(F3m.kac), "Central 53-feature AE: share of unseen-family flows declared NORMAL (missed)."),
    alarmPrecision1pct: f(pc(tierU("three-way α=0.01, β=0.04").precision_alarm_tier), "Precision of immediate alarms (three-way rule, unseen families) re-weighted to a 1% attack share."),
    hostDenseW50: f("100%", "Escalation of hosts whose traffic is entirely malicious at W ≥ 50 (stated in the text of Section 6.4, simulation)."),
    hostSparseMax: f(pc(f5(200, 0.1).pencere_tespit_mean), "Maximum host-window detection when attack flows are 10% of the window (W = 200, simulation); 0% at ρ ≤ 5%."),
    flP1IID: f(pc(fl("F3", KPOOL, "IID", FA("orijinal")).ano), `FedAvg P1 (40 rounds × 5 epochs, Adam reset), IID, unseen ANOMALY; central higher in ${tO.a_buyuk}/10 seeds, p_Holm = ${pv(tO.p_holm)}.`),
    flP3IID: f(pc(P3("IID").ano), `FedAvg P3 (until the 1,500-epoch cap, Adam kept), IID, unseen ANOMALY vs central ${pc(F3m.ano)}; gap ${pt(tY.fark)} points, p_Holm = ${pv(tY.p_holm)} (not significant).`),
    flP3IIDMissedGap: f(`${pt(kY.fark)} points`, `Higher missed rate of FedAvg P3 vs central in IID (${kY.a_buyuk}/10 seeds; additional test p = ${pv(kY.p)}, no Holm correction).`),
    flP3Dir1: f(pc(P3("Dirichlet=1.0").ano), `FedAvg P3 at Dirichlet 1.0, unseen ANOMALY (p_Holm = ${pv(t3("Dirichlet=1.0", "yakinsama_kalici").p_holm)}).`),
    flP3Dir01: f(pc(P3("Dirichlet=0.1").ano), `FedAvg P3 at Dirichlet 0.1, unseen ANOMALY (p_Holm = ${pv(t3("Dirichlet=0.1", "yakinsama_kalici").p_holm)}).`),
    flCapCaveat: f(`${V.valhist_all_cap.n} runs`, "Federated runs that reached the 1,500-epoch cap; none had fallen below the convergence threshold (still improving). FedProx tested only with μ = 0.01."),
    int8SizeKB53: f(`${nf(tinyC("F3").tflite_int8_KB)} KB`, "TFLite INT8 size of the central 53-feature AE (rough RAM estimate " + nf(tinyC("F3").tahmini_RAM_KB_int8) + " KB, excluding the TFLite Micro working area)."),
    int8SizeKB21: f(`${nf(tinyC("F4").tflite_int8_KB)} KB`, "TFLite INT8 size of the central 21-feature device AE (rough RAM estimate " + nf(tinyC("F4").tahmini_RAM_KB_int8) + " KB)."),
    int8DeviceInheritedFPR: f(pc(i4d.fpr, 2), `21-feature AE, INT8 score with inherited FP32 threshold: normal FPR (normal UNCERTAIN ${pc(i4d.unc)}); thresholds break.`),
    int8DeviceRecalFPR: f(pc(i4r.fpr, 2), `21-feature AE after INT8 recalibration: normal FPR (normal UNCERTAIN ${pc(i4r.unc)}).`),
    int8DeviceRecalMissedCost: f(`${pt(kq.fark)} points`, `Increase in missed rate of the device model after INT8 recalibration (${kq.a_buyuk}/10 seeds; additional test p = ${pv(kq.p)}).`),
    int8LatencyNote: f(`${nf(tinyC("F3").gecikme_int8_µs_colab, 2)} µs`, "INT8 latency of the central 53-feature AE measured on the Colab CPU (not a microcontroller value)."),
    deviceUnseenAnomaly: f(pc(F4m.ano), "Central 21-feature device AE: unseen ANOMALY (pooled calibration, 10 seeds)."),
    deviceUnseenMissed: f(pc(F4m.kac), "Central 21-feature device AE: unseen missed."),
    deviceFLpHolmRange: f(`${nf(Math.min(...t4p), 2)}–${nf(Math.max(...t4p), 2)}`, "p_Holm range of the 12 central-vs-federated comparisons for the device model (no significant difference)."),
    lofoFoldsW20: f(`${f2ok(20, 1000).başarılı_katman} / 9`, "LOFO folds meeting the pre-registered success criterion at W = 20, F = 1,000 (criterion not met)."),
    lofoFoldsW50: f(`${f2ok(50, 1000).başarılı_katman} / 9`, "LOFO folds meeting the success criterion at W = 50, F = 1,000."),
    lofoFoldsW100: f(`${f2ok(100, 1000).başarılı_katman} / 9`, "LOFO folds meeting the success criterion at W = 100, F = 1,000."),
    lofoRFRecallRange: f(`${pc(rfr[0])}–${pc(rfr[1])}`, "Single-flow recall of an RF trained on the other eight families, on each left-out family (failure criterion untestable; 'unseen' families resemble known ones)."),
  };
})();
