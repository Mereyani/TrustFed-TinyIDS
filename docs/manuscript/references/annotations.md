# Annotations — TrustFed-TinyIDS reference base

Scope: every 2022–2026 paper in `references_verified.csv` plus every closest-prior-work item. Each note is based ONLY on the title/abstract actually retrieved (Crossref, OpenAlex `abstract_inverted_index`, arXiv API, PMLR/ICML/Zenodo pages). Where no abstract was retrieved this is stated and the note is from the title only. 'Relation' lines describe how the item relates to TrustFed-TinyIDS (federated, TinyML, trust-weighted, per-host conformal p-values with sequential CUSUM/e-value accumulation, leave-one-attack-out evaluation on TON_IoT) and are the author-assistant's interpretation, not claims of the cited paper.

## Closest prior work (Part B)

### [mainuddin2023detecting] Mainuddin et al. (2023) — Detecting Compromised IoT Devices Using Autoencoders with Sequential Hypothesis Testing
*2023 IEEE International Conference on Big Data (BigData)*; conference, peer-reviewed; verified; doi:10.1109/bigdata59044.2023.10386399
*Method/contribution:* CUMAD — autoencoder anomaly detector feeding an SPRT-based sequential hypothesis test per IoT device, so that evidence accumulates before declaring a device compromised; on N-BaIoT the FPR drops from ~3.57% (AE alone) to ~0.5% with detection in <5 observations on average. *Limitation:* SPRT needs assumed likelihoods for the anomaly-event rate; no distribution-free calibration. *Relation:* the closest prior work to our per-host sequential accumulation; our contribution replaces heuristic AE alarms + SPRT with conformal p-values and CUSUM/e-process accumulation with explicit false-alarm control.

### [farsimadan2026confid] Farsimadan et al. (2026) — ConFID: A conformal one-class framework for unsupervised zero-day intrusion detection in IoT networks
*Internet of Things*; journal, peer-reviewed; verified; doi:10.1016/j.iot.2026.102078
*Abstract not retrieved via API (Crossref/OpenAlex have none); content below from the ScienceDirect abstract as summarised by a web search — verify before quoting.* ConFID: one-class framework trained on benign traffic with a hierarchical autoencoder, multi-layer Mahalanobis scoring (Ledoit–Wolf shrinkage) and a conformal calibration stage giving a finite-sample, distribution-free FPR guarantee for zero-day IoT intrusion detection. *Relation:* the closest peer-reviewed one-class conformal IDS; it is per-flow and centralised, with no per-host sequential evidence, federation or trust weighting.

### [rheey2026oran] Rheey & Park (2026) — Toward reliable intrusion monitoring for O-RAN based networks with conformal false alarm control
*The 2nd Workshop of AI4NextG: AI and ML for Next-Generation Wireless, ICML 2026*; workshop, peer review unclear; partially_verified; https://icml.cc/virtual/2026/78428
*Method/contribution (from the ICML 2026 virtual-site abstract):* covariance-aware conformal detector for unsupervised O-RAN intrusion detection — Mahalanobis distance in the autoencoder reconstruction-error space as nonconformity score, split-conformal threshold to keep the false-alarm rate within a budget under exchangeability; exact per-feature decomposition supports alarm triage. *Limitation:* workshop paper; per-sample decisions; exchangeability between benign calibration and future benign traffic is assumed. *Relation:* nearly the same scorer as ours (AE + Mahalanobis + split conformal) but no sequential accumulation, per-host calibration or federation.

### [park2026fedtinyml] Park et al. (2026) — Reliable federated TinyML deployment for IoT security
*arXiv preprint arXiv:2609.27202*; preprint, NOT peer-reviewed; verified; https://arxiv.org/abs/2609.27202
*Method/contribution (arXiv abstract):* studies Federated Learning combined with TinyML compression (knowledge distillation, structured pruning, quantisation) for IoT intrusion detection on microcontroller-class devices; preliminary results stress that training stability is critical and favour server-coordinated strategies. *Limitation:* preprint with preliminary results. *Relation:* closest federated-TinyML IDS work; no conformal calibration, trust weighting or sequential detection.

### [lamaakal2025tcuq] Lamaakal et al. (2025) — TCUQ: single-pass uncertainty quantification from temporal consistency with streaming conformal calibration for TinyML
*arXiv preprint arXiv:2508.12905*; preprint, NOT peer-reviewed; verified; https://arxiv.org/abs/2508.12905
*Method/contribution (arXiv abstract):* TCUQ — single-pass, label-free uncertainty monitor for streaming TinyML that turns short-horizon temporal-consistency signals into a risk score and uses a streaming conformal layer for a budgeted accept/abstain rule; fits kilobyte-scale MCUs. *Limitation:* preprint; evaluated on corrupted in-distribution streams, not network intrusion. *Relation:* shows conformal abstention is feasible on microcontrollers — supports the TinyML side of our design.

### [sugiantoro2026zenodo] Sugiantoro & Akhmad Hafizuddin (2026) — Trustworthy and selective intrusion detection for the Internet of Things: attack-aware conformal prediction, rare-class coverage, and cross-testbed generalization
*Zenodo (software record, v1)*; preprint, NOT peer-reviewed; partially_verified; doi:10.5281/zenodo.23429756
*Method/contribution (from the Zenodo record description; the paper itself was not found):* code and logs for a study of multiclass IoT detection on NF-ToN-IoT-v2, NF-BoT-IoT-v2 and NF-CSE-CIC-IDS2018-v2 with per-class (Mondrian) conformal coverage, a conformal reject option with risk–coverage analysis, and cross-testbed abstention as a shift alarm. *Limitation:* not peer-reviewed; software record only. *Relation:* overlapping ideas (Mondrian CP, reject option) but class-conditional, supervised and not sequential; cite with care (or not at all) until the paper appears.

### [le2026trace] Le et al. (2026) — TRACE: Feature-Space Feasible Action Contracts for Explainable Intrusion Triage
*Electronics*; journal, peer-reviewed; verified; doi:10.3390/electronics15153291
*Method/contribution:* TRACE — split-conformal action sets over triage actions (release/downgrade/defer/fail-open) with feature-space feasibility checks, evaluated on CICIoT2023, CSE-IDS2018, Edge-IIoTset and TON_IoT with supervised XGBoost/CatBoost/RF. *Limitation (stated):* matches the strongest simple selective gate on 6 of 11 pairs and trails on 5; not claimed deployment-ready. *Relation:* supervised conformal triage on TON_IoT — related to our abstention layer but closed-set and per-flow.

### [verma2026iotsentinel] Verma et al. (2026) — IoT-Sentinel: An Explainable Open-Set Intrusion Detection System with LLM-Assisted Incident Response for IoT Networks
*2026 4th International Conference on Inventive Computing and Informatics (ICICI)*; conference, peer-reviewed; verified; doi:10.1109/icici68773.2026.11580820
*Method/contribution:* IoT-Sentinel — supervised classifier (CICIoT2023, SMOTE) with SHAP explanations, an open-set module for zero-day flags and an LLM-assisted incident-response dashboard. *Limitation:* open-set module details and error guarantees not given in the abstract; venue is a smaller IEEE conference. *Relation:* weak prior work; cite only as an example of open-set + XAI IoT IDS.

## Novelty-critical: conformal / e-value sequential detection

### [vovk2025cusum] Vovk et al. (2025) — Validity and efficiency of the conformal CUSUM procedure
*Proceedings of the Fourteenth Symposium on Conformal and Probabilistic Prediction with Applications (COPA 2025), PMLR*; conference, peer-reviewed; verified; https://proceedings.mlr.press/v266/vovk25b.html
*Method/contribution (PMLR abstract):* studies a conformal version of CUSUM for change detection, which repeatedly tests the IID null; establishes a new validity property and, for the first time, an efficiency property. *Limitation:* methodological; no security application. *Relation:* the most direct theoretical basis for our conformal-CUSUM per host; cite as the method we instantiate for intrusion detection.

### [dong2026ctm] Dong et al. (2026) — Detecting adversarial attacks in image sequences with conformal test martingales
*Proceedings of the Fifteenth Symposium on Conformal and Probabilistic Prediction with Applications (COPA 2026), PMLR*; conference, peer-reviewed; verified; https://proceedings.mlr.press/v329/dong26a.html
*Method/contribution (PMLR abstract):* sequence-level detection of adversarial examples by converting image/target-model nonconformity scores into conformal p-values monitored with conformal test martingales (ImageNet-100, ResNet-50). *Limitation:* vision domain. *Relation:* the closest security application of conformal test martingales found; not network/host intrusion.

### [prinster2025watch] Prinster et al. (2025) — WATCH: adaptive monitoring for AI deployments via weighted-conformal martingales
*Proceedings of the 42nd International Conference on Machine Learning (ICML 2025), PMLR*; conference, peer-reviewed; verified; https://proceedings.mlr.press/v267/prinster25a.html
*Method/contribution (arXiv abstract; ICML 2025, PMLR 267):* weighted conformal test martingales (WCTMs) for online monitoring of deployed ML with false-alarm control, online adaptation to mild shifts and diagnosis of alarm causes. *Limitation (author note):* v5 corrects an omitted assumption (bag sufficiency) in the main theorem. *Relation:* modern anytime-valid conformal monitoring; method-level comparison for our e-process monitor.

### [eliades2021icm] Eliades & Papadopoulos (2021) — Using inductive conformal martingales for addressing concept drift in data stream classification
*Proceedings of the Tenth Symposium on Conformal and Probabilistic Prediction and Applications (COPA 2021), PMLR*; conference, peer-reviewed; verified; https://proceedings.mlr.press/v152/eliades21a.html
*Method/contribution (PMLR abstract):* inductive conformal martingales with a histogram betting function for fast concept-drift detection in stream classification (STAGGER, SEA, ELEC). *Limitation:* synthetic/benchmark streams. *Relation:* efficient betting function suitable for MCU-side martingales.

### [bhattacharyya2026optimal] Bhattacharyya & Ramdas (2026) — Optimal distribution-free sequential change detection with conformal martingales
*arXiv preprint arXiv:2609.27179*; preprint, NOT peer-reviewed; verified; https://arxiv.org/abs/2609.27179
*Method/contribution (arXiv abstract, preprint):* theory of conformal p-values under a changepoint; shows standard conformal test martingales/e-detectors are provably suboptimal (delays Ω(T) or Ω(√ARL)) and constructs new conformal e-processes/e-detectors with learned scores. *Limitation:* preprint; i.i.d. observations assumed. *Relation:* directly relevant to the efficiency of our conformal CUSUM/e-detector; check status before submission.

### [li2026robustconformal] Li (2026) — Robust conformal intrusion detection via traffic-aware calibration and attack-orbit invariance
*arXiv preprint arXiv:2609.19241*; preprint, NOT peer-reviewed; verified; https://arxiv.org/abs/2609.19241
*Method/contribution (arXiv abstract, preprint):* shows clean-traffic conformal calibration fails when attackers perturb controllable features, and proposes traffic-aware calibration plus exclusion of attacker-controllable features for exact coverage, on three IDS benchmarks with fine-tuned LLMs. *Limitation:* preprint; LLM-based detectors. *Relation:* adversarial-robustness caveat for our conformal guarantees.

## Topic 1 — Federated learning for IoT intrusion detection

### [arisdakessian2023survey] Arisdakessian et al. (2023) — A Survey on IoT Intrusion Detection: Federated Learning, Game Theory, Social Psychology, and Explainable AI as Future Directions
*IEEE Internet of Things Journal*; journal, peer-reviewed; verified; doi:10.1109/jiot.2022.3203249
*Method/contribution:* survey of IoT intrusion detection with a two-level taxonomy (detection approach, then sub-technique) that also covers IoT–fog–cloud communication, and proposes a framework combining XAI, FL, game theory and social psychology. *Limitation (stated/implicit):* the combined framework is a future-direction proposal, not an evaluated system. *Relation:* background citation for FL-based IoT IDS and for positioning trust/explainability as open directions.

### [khraisat2025survey] Khraisat et al. (2025) — Survey on Federated Learning for Intrusion Detection System: Concept, Architectures, Aggregation Strategies, Challenges, and Future Directions
*ACM Computing Surveys*; journal, peer-reviewed; verified; doi:10.1145/3687124
*Method/contribution:* survey of FL for IDS covering architectures, aggregation strategies, privacy-preserving techniques and security protocols, with strengths/limitations of each. *Limitation:* survey; no new empirical evidence. *Relation:* recent high-venue survey to cite when motivating FedAvg/FedProx choices and aggregation design.

### [lavaur2022evolution] Lavaur et al. (2022) — The Evolution of Federated Learning-Based Intrusion Detection and Mitigation: A Survey
*IEEE Transactions on Network and Service Management*; journal, peer-reviewed; verified; doi:10.1109/tnsm.2022.3177512
*Method/contribution:* structured literature survey of FL-based IDS (2016–2021) with a reference architecture and taxonomy validated against existing works. *Limitation:* stated that common comparison criteria were missing in the field; coverage ends in 2021. *Relation:* supports the claim that FL-IDS lacks standard evaluation criteria (motivating our leave-one-attack-out and per-host reporting).

### [saezdecamara2023clustered] Sáez-de-Cámara et al. (2023) — Clustered federated learning architecture for network anomaly detection in large scale heterogeneous IoT networks
*Computers & Security*; journal, peer-reviewed; verified; doi:10.1016/j.cose.2023.103299
*Method/contribution:* FL architecture for network anomaly detection with an unsupervised device-clustering step integrated in the FL pipeline to tackle heterogeneity; evaluated on an emulated testbed (100 devices) with Mirai lifecycle, Merlin C2 botnet and scanning. *Limitation:* evaluation on an emulated testbed. *Relation:* closest FL work handling device heterogeneity by grouping devices — related to our per-host (Mondrian-style) calibration, but it clusters models rather than calibrating per-host p-values.

### [decarvalhobertoli2023generalizing] de Carvalho Bertoli et al. (2023) — Generalizing intrusion detection for heterogeneous networks: A stacked-unsupervised federated learning approach
*Computers & Security*; journal, peer-reviewed; verified; doi:10.1016/j.cose.2023.103106
*Abstract not retrieved — annotated from title only:* appears to address cross-network generalisation of unsupervised FL-based IDS via stacking. *Relation:* related to non-IID / cross-site generalisation in our FL evaluation (verify content before citing for specifics).

### [yan2025global] Yan et al. (2025) — Global or Local Adaptation? Client-Sampled Federated Meta-Learning for Personalized IoT Intrusion Detection
*IEEE Transactions on Information Forensics and Security*; journal, peer-reviewed; verified; doi:10.1109/tifs.2024.3516548
*Method/contribution:* PerFLID, personalised federated meta-learning for NIDS with client selection by clustering local-gradient similarity; theoretical convergence-speed analysis; +10.11% local-adaptation accuracy over the best baseline on three traffic datasets. *Limitation:* not stated in abstract. *Relation:* strong personalisation baseline; our design instead personalises at the calibration/decision layer (per-host conformal thresholds) rather than model weights.

### [sun2025robust] Sun et al. (2025) — Robust intrusion detection based on personalized federated learning for IoT environment
*Computers & Security*; journal, peer-reviewed; verified; doi:10.1016/j.cose.2025.104442
*Abstract not retrieved — title only.* Personalised FL IDS for IoT with robustness focus. *Relation:* personalisation baseline for non-IID IoT clients.

### [singh2024evaluating] Singh et al. (2024) — Evaluating Federated Learning-Based Intrusion Detection Scheme for Next Generation Networks
*IEEE Transactions on Network and Service Management*; journal, peer-reviewed; verified; doi:10.1109/tnsm.2024.3385385
*Method/contribution:* Fed-IDS that addresses class imbalance at local and global levels, evaluated under IID and non-IID splits. *Limitation (stated):* existing Fed-IDSs perform poorly because evaluation and real data are highly imbalanced. *Relation:* supports our concern that class imbalance and non-IID splits must be reported explicitly.

### [nguyen2024federated] Nguyen et al. (2024) — Federated PCA on Grassmann Manifold for IoT Anomaly Detection
*IEEE/ACM Transactions on Networking*; journal, peer-reviewed; verified; doi:10.1109/tnet.2024.3423780
*Method/contribution:* federated PCA (FedPE in Euclidean space, FedPG on Grassmann manifolds) via ADMM for non-IID IoT anomaly detection, with convergence rates under sub-sampling; tested on UNSW-NB15 and TON_IoT. *Limitation:* linear (PCA) model; detection comparable to, not better than, non-linear baselines. *Relation:* lightweight unsupervised FL anomaly detector on TON_IoT — directly comparable baseline for a TinyML-friendly federated detector.

### [zhao2023semisupervised] Zhao et al. (2023) — Semisupervised Federated-Learning-Based Intrusion Detection Method for Internet of Things
*IEEE Internet of Things Journal*; journal, peer-reviewed; verified; doi:10.1109/jiot.2022.3175918
*Method/contribution:* semi-supervised FL IDS using knowledge distillation on unlabelled data, a CNN that doubles as classifier and discriminator, and hard-label voting to cut communication under non-IID data. *Limitation:* supervised/semi-supervised; targets known classes. *Relation:* example of non-IID FL-IDS; contrasts with our benign-only (one-class) training needed for unseen attacks.

### [hernandezramos2025intrusion] Hernandez-Ramos et al. (2025) — Intrusion Detection Based on Federated Learning: A Systematic Review
*ACM Computing Surveys*; journal, peer-reviewed; verified; doi:10.1145/3731596
*Method/contribution:* systematic review and taxonomy of FL-enabled IDS (2018–2022): models, datasets, aggregation functions, libraries, challenges. *Limitation:* coverage to 2022. *Relation:* survey citation for FL-IDS landscape and dataset usage.

## Topic 2 — Unseen / zero-day attack detection

### [yang2025lightweight] Yang et al. (2025) — A Lightweight and Dynamic Open-Set Intrusion Detection for Industrial Internet of Things
*IEEE Transactions on Information Forensics and Security*; journal, peer-reviewed; verified; doi:10.1109/tifs.2025.3546849
*Method/contribution:* lightweight dynamic open-set IDS for IIoT with an update stage that learns newly detected unknown attacks; reports >65% detection-time and >80% memory reduction vs retraining, ~96% accuracy on four datasets. *Limitation:* not stated in abstract. *Relation:* open-set IIoT baseline; our approach instead gives finite-sample FPR control on unknowns via conformal p-values.

### [yu2024deep] Yu et al. (2024) — Deep Q -Network-Based Open-Set Intrusion Detection Solution for Industrial Internet of Things
*IEEE Internet of Things Journal*; journal, peer-reviewed; verified; doi:10.1109/jiot.2023.3333903
*Method/contribution:* DC-IDS: DQN for fine-grained known-class classification plus CVAE reconstruction error to flag unknown attacks; evaluated on TON_IoT. *Limitation:* thresholding of reconstruction error is heuristic (no stated error guarantee). *Relation:* TON_IoT open-set baseline; our conformal calibration replaces heuristic reconstruction-error thresholds.

### [soltani2023adaptable] Soltani et al. (2023) — An adaptable deep learning-based intrusion detection system to zero-day attacks
*Journal of Information Security and Applications*; journal, peer-reviewed; verified; doi:10.1016/j.jisa.2023.103516
*Abstract not retrieved — title only:* adaptable deep-learning IDS for zero-day attacks. *Relation:* zero-day baseline (check content before specific claims).

### [souza2025novel] Souza et al. (2025) — A novel open set Energy-based Flow Classifier for Network Intrusion Detection
*Computers & Security*; journal, peer-reviewed; verified; doi:10.1016/j.cose.2025.104569
*Abstract not retrieved — title only:* open-set energy-based flow classifier for NIDS. *Relation:* energy-score open-set baseline; contrast with conformal p-values.

### [arthur2025empirical] Arthur et al. (2025) — Empirical Study of Hierarchical Intrusion Detection Systems for Unknown Attacks
*IEEE Transactions on Network and Service Management*; journal, peer-reviewed; verified; doi:10.1109/tnsm.2025.3600378
*Method/contribution:* enhanced multi-tier (hierarchical) IDS with optimised heterogeneous classifiers for zero-day detection, tested on WUSTL, CIC-IDS2017, 5G and UNR. *Limitation:* not stated. *Relation:* hierarchical unknown-attack pipeline; comparable evaluation goal.

### [fawaz2026detecting] Fawaz et al. (2026) — Detecting Zero-Day Attacks via Reconstruction of Feature Influence and Model Uncertainty
*IEEE Transactions on Network and Service Management*; journal, peer-reviewed; verified; doi:10.1109/tnsm.2026.3731401
*Method/contribution:* zero-day identification combining XAI feature-influence reconstruction error with ensemble predictive uncertainty; evaluated with a leave-one-attack-out protocol on CICIoT2023, NF-TON-IoT and CIC-DDoS2019. *Limitation:* gains vary by dataset (abstract reports best-case and near-neutral worst-case). *Relation:* directly supports our leave-one-attack-out protocol; it uses uncertainty but not conformal error control or sequential accumulation.

### [yao2023lightweight] Yao et al. (2023) — A Lightweight Intelligent Network Intrusion Detection System Using One-Class Autoencoder and Ensemble Learning for IoT
*Sensors*; journal, peer-reviewed; verified; doi:10.3390/s23084141
*Method/contribution:* one-class BiGRU autoencoder trained on normal data plus soft-voting ensemble to map unknown attacks to the most similar known class (WSN-DS, UNSW-NB15, KDD99). *Limitation:* older datasets; no FPR guarantee. *Relation:* lightweight one-class AE design similar to our TinyML scorer.

### [jin2023federated] Jin et al. (2023) — Federated Incremental Learning based Evolvable Intrusion Detection System for Zero-Day Attacks
*IEEE Network*; journal, peer-reviewed; verified; doi:10.1109/mnet.018.2200349
*Method/contribution:* EIDS — federated incremental learning that aggregates knowledge from distributed detectors to update an open-set IDS without full retraining (>90% update-time reduction). *Limitation:* open-set accuracy ~0.86 reported. *Relation:* federated + unseen-attack setting closest in spirit to our FL pipeline.

### [yang2022griffin] Yang et al. (2022) — Griffin: Real-Time Network Intrusion Detection System via Ensemble of Autoencoder in SDN
*IEEE Transactions on Network and Service Management*; journal, peer-reviewed; verified; doi:10.1109/tnsm.2022.3175710
*Method/contribution:* Griffin, SDN NIDS using an ensemble of autoencoders on clustered sequential packet features, with differential privacy during training; ~40% lower complexity than prior NIDS. *Limitation:* AUC drops up to 9% under evasion. *Relation:* Kitsune-style AE ensemble successor; baseline for unsupervised AE scoring.

### [pourahmadi2023spotting] Pourahmadi et al. (2023) — Spotting Anomalies at the Edge: Outlier Exposure-Based Cross-Silo Federated Learning for DDoS Detection
*IEEE Transactions on Dependable and Secure Computing*; journal, peer-reviewed; verified; doi:10.1109/tdsc.2022.3224896
*Method/contribution:* FedOE, cross-silo FL with an outlier-exposure autoencoder that uses ~50 labelled attack flows per edge server and generalises to zero-day DDoS. *Limitation:* requires some labelled outliers. *Relation:* FL + AE + zero-day; differs from our benign-only calibration.

### [hung2026explainable] Hung (2026) — An Explainable XGBoost-Based Framework for IoT Attack Detection with Unseen Attack Family Evaluation
*Sensors*; journal, peer-reviewed; verified; doi:10.3390/s26103005
*Method/contribution:* explainable XGBoost/RF framework for IoT attack detection with unseen-attack-family evaluation and calibrated false-alarm-rate (FAR) operating points. *Limitation:* supervised models; model choice depends on deployment objective (stated). *Relation:* recent example of unseen-family evaluation under a FAR constraint — close to our evaluation protocol.

## Topic 3 — Conformal prediction / uncertainty-aware IDS

### [datta2026cassidy] Datta et al. (2026) — CASSIDY: A Continual Adaptive System for Secure and Interpretable Drift-Aware IoT Anomaly Detection
*Computers, Materials & Continua*; journal, peer-reviewed; verified; doi:10.32604/cmc.2026.090581
*Method/contribution:* CASSIDY — a very small dense autoencoder with conformal p-values for a bounded false-positive rate, decoder-only test-time adaptation for drift, and intrinsic feature-deviation attribution; evaluated on TON_IoT (AUC 0.9911) with sub-millisecond inference. *Limitation:* drift is simulated; exchangeability must be restored after adaptation (the paper describes a procedure for this). *Relation:* very close to our TinyML + conformal scorer on TON_IoT, but decisions are per-sample — no sequential evidence accumulation, per-host calibration or federation.

### [massaad2026beyond] Massaad et al. (2026) — Beyond Arbitrary Thresholds: Conformal Prediction for Trustworthy CAN Bus Intrusion Detection
*ICC 2026 - IEEE International Conference on Communications*; conference, peer-reviewed; verified; doi:10.1109/icc59461.2026.11587647
*Method/contribution:* shows that the common 'percentile of benign reconstruction error' threshold is equivalent to split-conformal calibration under exchangeability, compares MSE/MAE/MaxAE nonconformity scores, and adds an online adaptive-threshold calibration for drift (CAN bus, HCRL Car-Hacking). *Limitation:* in-vehicle CAN domain; per-message decisions. *Relation:* supports our framing of AE thresholds as conformal p-values; we extend from per-sample thresholds to sequential (CUSUM/e-value) accumulation per host.

### [younas2026operationally] Younas (2026) — Operationally calibrated open-world zero-day intrusion detection using hybrid conformal abstention
*Journal of Computer Virology and Hacking Techniques*; journal, peer-reviewed; verified; doi:10.1007/s11416-026-00692-3
*Method/contribution:* HTCCA-Conformal — benign-calibrated UNKNOWN gate at a fixed FPR budget (entropy, Isolation Forest, PCA reconstruction, extreme-value tails) followed by class-conditional conformal prediction that routes ambiguous cases to REVIEW; leave-one-family-out evaluation. *Limitation (stated by results):* at 1% FPR, mean unknown-alert detection is only 30.6%, weak for Botnet, WebAttack and BruteForce. *Relation:* strong evidence that single-flow conformal gates miss low-volume attacks at strict FPR — the gap that our sequential per-host accumulation targets.

### [zhao2026riskcontrolled] Zhao & Zhan (2026) — Risk-Controlled Lightweight IoT Intrusion Detection via SHAP-Guided Feature Pruning and Conformal Prediction
*2026 IEEE International Conference on Smart Internet of Things (SmartIoT)*; conference, peer-reviewed; verified; doi:10.1109/smartiot70864.2026.00014
*Method/contribution:* LightGBM backbone reduced by SHAP-guided feature pruning (46→15 features) plus split conformal prediction as a selective (accept singleton / defer otherwise) decision rule on CICIoT2023 (coverage 0.899 at 90% target, reject rate 0.080). *Limitation:* supervised, closed-set 8-class setting. *Relation:* conformal reject option for lightweight IoT IDS — related to our abstention/risk–coverage analysis.

### [zoller2026reliable] Zöller & Lawall (2026) — Reliable Intrusion Detection via Conformalized Tabular Foundation Models
*2026 IEEE International Conference on Cyber Security and Resilience (CSR)*; conference, peer-reviewed; verified; doi:10.1109/csr69374.2026.11759915
*Method/contribution:* TabPFN tabular foundation model for cross-dataset NIDS (CIC-IDS2017 ↔ CSE-CIC-IDS2018) with APS and Mondrian conformal prediction; prediction sets expand under domain shift and serve as an untrustworthiness signal. *Limitation:* supervised; set size as a diagnostic, not a controlled alarm. *Relation:* one of the few IDS papers using Mondrian CP — but class-conditional, not per-host.

### [yuan2026conformal] Yuan et al. (2026) — Conformal machine learning for reliable anomaly detection in industrial cyber-physical systems
*Reliability Engineering & System Safety*; journal, peer-reviewed; verified; doi:10.1016/j.ress.2026.112417
*Abstract not retrieved — annotated from title only:* conformal ML for reliable anomaly detection in industrial cyber-physical systems (Reliability Engineering & System Safety). *Relation:* high-quality-venue evidence that conformal anomaly detection is being adopted for CPS; check content before citing specifics.

### [kaur2023codit] Kaur et al. (2023) — CODiT: Conformal Out-of-Distribution Detection in Time-Series Data for Cyber-Physical Systems
*Proceedings of the ACM/IEEE 14th International Conference on Cyber-Physical Systems (with CPS-IoT Week 2023)*; conference, peer-reviewed; verified; doi:10.1145/3576841.3585931
*Method/contribution:* CODiT uses deviation from in-distribution temporal equivariance as the nonconformity measure, combines several conformal detectors with Fisher's method, and obtains bounded false alarms for OOD detection in CPS time series. *Limitation (stated):* prior work either ignores temporal relations or lacks guarantees; CODiT works on fixed windows. *Relation:* precedent for combining conformal p-values across detectors with an error guarantee — analogous to our p-value combination step.

### [kaur2024outofdistribution] Kaur et al. (2024) — Out-of-distribution Detection in Dependent Data for Cyber-physical Systems with Conformal Guarantees
*ACM Transactions on Cyber-Physical Systems*; journal, peer-reviewed; verified; doi:10.1145/3648005
*Method/contribution:* journal extension of CODiT to dependent data and variable-length traces, combining Fisher values over sliding windows with four merging functions and comparing their false-alarm guarantees. *Limitation:* applied to autonomous driving and gait CPS, not networks. *Relation:* closest methodological precedent for merging p-values over windows with FAR guarantees; our work instead uses CUSUM/e-processes on per-host conformal p-values.

### [barrett2026fades] Barrett et al. (2026) — FADES: Adaptive Drift Estimation via Conformal Signals for Streaming Intrusion Detection
*Electronics*; journal, peer-reviewed; verified; doi:10.3390/electronics15102114
*Method/contribution:* FADES (journal extension of FIRCE) — conformal-evaluation-based drift estimation for streaming IDS, with an approximate cross-conformal evaluator and comparison of prediction-space vs representation-space (CADE) drift detection on UNSW-NB15, CICIDS2018 and an IoT testbed. *Limitation (stated):* CADE is costly under repeated retraining. *Relation:* closest streaming-conformal IDS work; it targets model drift/retraining triggers, not anytime-valid attack alarms per host.

### [gulappagol2026uncertaintyaware] Gulappagol et al. (2026) — Uncertainty-Aware Rejection of Unknown Attacks in MQTT Networks via Class-Conditional Conformal Calibration in Embedding Space
*2026 7th International Conference On Computational Vision and Bio Inspired Computing (ICCVBIC)*; conference, peer-reviewed; verified; doi:10.1109/iccvbic71195.2026.11689442
*Method/contribution:* UAR-IDS — class-conditional split conformal calibration on Mahalanobis distances in an MLP embedding (CCC-R) for rejecting unknown MQTT attacks; leave-one-attack-out on MQTTEEB-D (mean unknown AUROC 0.746). *Limitation:* modest unknown-attack AUROC; per-class (not per-device) calibration. *Relation:* close to our Mahalanobis/AE + conformal design and leave-one-attack-out protocol; differs by lacking sequential accumulation and per-host groups.

### [barrett2026firce] Barrett et al. (2026) — FIRCE: A Framework for Intrusion Response and Conformal Evaluation
*2026 International Conference on Smart Applications, Communications and Networking (SmartNets)*; conference, peer-reviewed; verified; doi:10.1109/smartnets69662.2026.11604738
*Method/contribution:* FIRCE — augments supervised IDS with conformal evaluation (inductive, cross, approximate transductive, approximate cross-conformal) and adaptive chunking to detect drift and trigger retraining; IoT testbed of 10 devices plus CICIDS2018/UNSW-NB15. *Limitation:* supervised base classifiers. *Relation:* conformal drift monitoring in IDS; complementary to our attack-alarm use of conformal p-values.

## Topic 4 — Trust- and reputation-aware IDS

### [hayawi2025false] Hayawi et al. (2025) — A False Positive Resilient Distributed Trust Management Framework for Collaborative Intrusion Detection Systems
*IEEE Transactions on Services Computing*; journal, peer-reviewed; verified; doi:10.1109/tsc.2025.3539202
*Method/contribution:* blockchain-based trust management for collaborative IDS combining device genome attestation, dynamic system parameters and a false-positive-resilient reputation mechanism, with analysis of penalty/recovery phases and the effect of false positives on node reputation. *Limitation:* evaluation centres on blockchain platform performance (Fabric vs Ethereum). *Relation:* directly relevant to our concern that false positives should not destroy a host's trust score.

### [dhelim2023trust] Dhelim et al. (2023) — Trust2Vec: Large-Scale IoT Trust Management System Based on Signed Network Embeddings
*IEEE Internet of Things Journal*; journal, peer-reviewed; verified; doi:10.1109/jiot.2022.3201772
*Method/contribution:* Trust2Vec — random-walk signed-network embeddings and community detection to detect/block large-scale trust attacks (self-promoting, bad-mouthing) in IoT (up to 94% mitigation in simulation). *Limitation:* simulation-only. *Relation:* trust-management background; our trust is derived from detector evidence rather than peer ratings.

### [hassan2024letmiot] Hassan et al. (2024) — LETM-IoT: A lightweight and efficient trust mechanism for Sybil attacks in Internet of Things networks
*Ad Hoc Networks*; journal, peer-reviewed; verified; doi:10.1016/j.adhoc.2024.103576
*Method/contribution:* LETM-IoT, lightweight trust mechanism against three Sybil attack types in RPL networks (Cooja simulation), improving delivery ratio, TPR, energy and memory vs RPL baselines. *Limitation:* 5% extra storage; simulation. *Relation:* example of lightweight trust on constrained devices.

### [wardana2024lightweight] Wardana et al. (2024) — Lightweight, Trust-Managing, and Privacy-Preserving Collaborative Intrusion Detection for Internet of Things
*Applied Sciences*; journal, peer-reviewed; verified; doi:10.3390/app14104109
*Method/contribution:* lightweight collaborative IDS for IoT with trust management and privacy preservation, evaluated on CICIoT2023 (accuracy ~97.65%). *Limitation:* supervised; metrics only on one dataset. *Relation:* combines trust management with collaborative (federated-style) IDS — closest in spirit to our trust-weighted FL.

### [bampatsikos2025trust] Bampatsikos et al. (2025) — Trust Score Prediction and Management in IoT Ecosystems Using Markov Chains and MADM Techniques
*IEEE Transactions on Consumer Electronics*; journal, peer-reviewed; verified; doi:10.1109/tce.2025.3531045
*Method/contribution:* trust-score prediction for IoT devices via Markov chains and multi-attribute decision-making, in an architecture combining a trust management server, an IDS and DLT. *Limitation (stated):* adaptability to zero-day attacks left to future work. *Relation:* statistical (not deep) device trust scores fed by IDS — conceptually close to our IDS-evidence-driven host trust.

### [baykara2025zetros] Baykara et al. (2025) — ZETROS: A zero-trust IoT network security framework using distributed blacklisting, trust scoring and smart contracts
*Computer Networks*; journal, peer-reviewed; verified; doi:10.1016/j.comnet.2025.111601
*Method/contribution:* ZETROS zero-trust framework: distributed blacklisting, ML-based intrusion/anomaly detection against insiders, and smart-contract feedback for trust scoring; resilient even with half the devices compromised (simulation). *Limitation:* simulation-based. *Relation:* trust scoring + IDS in IoT; supports trust-aware aggregation motivation.

### [rasagna2026zam] Rasagna et al. (2026) — ZAM: Z-Score Anomaly Detection and Mitigation for Ballot Stuffing and On-Off Attacks in Fog Networks
*IEEE Internet of Things Journal*; journal, peer-reviewed; verified; doi:10.1109/jiot.2026.3731207
*Method/contribution:* ZAM detects ballot-stuffing and on-off trust attacks in fog networks using Pearson-gated fusion of QoS and peer ratings, MAD-scaled Student-t bounds and per-node EWMA residuals (window-level FPR <2% up to 50 nodes). *Limitation:* simulation (RayCloudSim). *Relation:* per-node EWMA temporal accumulation for trust attacks — a sequential-statistics precedent at node level.

### [ahmadi2024trust] Ahmadi & Javidan (2024) — A Trust Based Anomaly Detection Scheme Using a Hybrid Deep Learning Model for IoT Routing Attacks Mitigation
*IET Information Security*; journal, peer-reviewed; verified; doi:10.1049/2024/4449798
*Method/contribution:* trust-based anomaly detection for RPL routing attacks (DIS flooding, version number, decreased rank) using a hybrid deep model comparing real vs predicted routing behaviour; trust scores move opposite to attack frequency (Cooja). *Limitation:* routing-layer attacks in simulation. *Relation:* device trust driven by anomaly evidence over time.

### [houichi2026trustaware] Houichi et al. (2026) — A trust-aware federated intrusion detection framework for privacy-preserving smart city IoT networks
*Computer Networks*; journal, peer-reviewed; verified; doi:10.1016/j.comnet.2026.112616
*Abstract not retrieved — title only:* trust-aware federated intrusion detection framework for privacy-preserving smart-city IoT networks (Computer Networks 2026). *Relation:* probably the closest trust-aware FL-IDS in a strong venue; read before claiming novelty for trust-weighted aggregation.

### [javeed2024federated] Javeed et al. (2024) — A federated learning-based zero trust intrusion detection system for Internet of Things
*Ad Hoc Networks*; journal, peer-reviewed; verified; doi:10.1016/j.adhoc.2024.103540
*Method/contribution:* FL-based 'zero-trust' IDS with a CNN–BiLSTM model trained on edge devices (CICIDS2017, Edge-IIoTset). *Limitation:* 'zero trust' refers to keeping data local, not to explicit trust scores. *Relation:* widely cited FL-IDS for IoT; useful contrast with explicit per-host trust.

### [alghofaili2023dynamic] Alghofaili & Rassam (2023) — A Dynamic Trust-Related Attack Detection Model for IoT Devices and Services Based on the Deep Long Short-Term Memory Technique
*Sensors*; journal, peer-reviewed; verified; doi:10.3390/s23083814
*Method/contribution:* LSTM-based dynamic trust-related attack detection model for IoT devices/services that identifies and isolates untrusted entities (~99% accuracy). *Limitation:* evaluation data samples are not well specified in the abstract. *Relation:* trust-related attack detection background.

## Topic 5 — Sequential evidence accumulation and low-rate/stealthy attacks

### [rios2022detection] Rios et al. (2022) — Detection and Mitigation of Low-Rate Denial-of-Service Attacks: A Survey
*IEEE Access*; journal, peer-reviewed; verified; doi:10.1109/access.2022.3191430
*Method/contribution:* survey with a taxonomy of low-rate DoS attacks (QoS, slow-rate, service-queue) and detection/mitigation methods for eight LDoS types. *Limitation:* survey. *Relation:* background for stealthy/low-rate attacks whose per-flow signals are weak — motivating evidence accumulation.

### [lei2025hawkeye] Lei et al. (2025) — HawkEye: An end-host method to detect the Low-rate Denial-of-Service attack of cross-traffic over bottleneck links
*Computer Networks*; journal, peer-reviewed; verified; doi:10.1016/j.comnet.2024.110951
*Abstract not retrieved — title only:* HawkEye, an end-host method for detecting low-rate DoS on cross-traffic over bottleneck links (Computer Networks 2025). *Relation:* end-host (host-level) LDoS detection — conceptually aligned with our per-host monitoring.

### [ali2023low] Ali et al. (2023) — Low Rate DDoS Detection Using Weighted Federated Learning in SDN Control Plane in IoT Network
*Applied Sciences*; journal, peer-reviewed; verified; doi:10.3390/app13031431
*Method/contribution:* weighted federated learning to detect low-rate DDoS in the SDN control plane of IoT networks (MATLAB experiments). *Limitation:* simulation; supervised. *Relation:* FL applied to low-rate attacks — closest FL + LDoS precedent.

### [naha2023quickest] Naha et al. (2023) — Quickest detection of deception attacks on cyber–physical systems with a parsimonious watermarking policy
*Automatica*; journal, peer-reviewed; verified; doi:10.1016/j.automatica.2023.111147
*Method/contribution:* quickest detection of deception attacks in networked control systems using a parsimonious watermarking policy; optimal two-threshold rule on the Shiryaev posterior, with asymptotic ADD/FAR expressions via non-linear renewal theory. *Limitation:* parametric CPS model. *Relation:* modern Shiryaev-type quickest detection for cyber attacks; contrasts with our distribution-free (conformal) inputs.

### [eliades2024icm] Eliades & Papadopoulos (2024) — ICM ensemble with novel betting functions for concept drift
*Machine Learning*; journal, peer-reviewed; verified; doi:10.1007/s10994-024-06593-0
*Method/contribution:* inductive conformal martingales (ICM) with an improved CAUTIOUS betting function, new density estimators and ICM ensembles for concept-drift detection on four benchmarks. *Limitation:* generic streams, not security. *Relation:* betting-function design for conformal martingales, reusable for our host-level martingale.

### [zhang2025semisupervised] Zhang et al. (2025) — Semi-supervised concept drift detection and adaptation based on conformal martingale framework
*Journal of Process Control*; journal, peer-reviewed; verified; doi:10.1016/j.jprocont.2025.103374
*Abstract not retrieved — title only:* semi-supervised concept drift detection and adaptation based on a conformal martingale framework (process control). *Relation:* conformal martingales for drift in industrial streams.

### [yu2024renyi] Yu et al. (2024) — Renyi entropy-driven network traffic anomaly detection with dynamic threshold
*Cybersecurity*; journal, peer-reviewed; verified; doi:10.1186/s42400-024-00249-1
*Method/contribution:* Rényi-entropy traffic anomaly detection with a fixed time window and improved EWMA for dynamic thresholds. *Limitation:* thresholds are heuristic (no stated error control). *Relation:* EWMA-based network anomaly detection — baseline for our EWMA/CUSUM comparison.

### [anilkumar2026generative] Anil Kumar et al. (2026) — Generative Adversarial Networks Based Low-Rate Denial of Service Attack Detection and Mitigation in Software-Defined Networks
*IEEE Transactions on Network and Service Management*; journal, peer-reviewed; verified; doi:10.1109/tnsm.2025.3625278
*Method/contribution:* real-time LDoS detection and mitigation in SDN with a GAN-based detector and flow filtering in the controller (>99.98% accuracy, 8.58 s response). *Limitation:* SDN-specific; supervised evaluation. *Relation:* recent LDoS detector in a strong venue.

### [hung2025lowrate] Hung et al. (2025) — Low-Rate Denial-of-Service Attack Detection in Open Radio Access Network: Integrating Federated Learning
*IEEE Vehicular Technology Magazine*; journal, peer-reviewed; verified; doi:10.1109/mvt.2025.3623298
*Method/contribution:* FL-based detection of unseen low-rate and high-rate DoS across O-RAN private networks (11 attack types, two 5G environments). *Limitation:* emulated dataset. *Relation:* federated + low-rate + unseen attack evaluation — close to our scope.

### [g2026lightweight] G & S (2026) — A Lightweight Entropy-Based CUSUM Framework for Intrusion Detection in WSN Environments
*2026 World Conference on Computational Science and Technology (WcCST)*; conference, peer-reviewed; verified; doi:10.1109/wccst67302.2026.11496167
*Abstract not retrieved — title only:* lightweight entropy-based CUSUM framework for intrusion detection in WSNs. *Relation:* recent CUSUM-on-entropy IDS (not conformal) — shows CUSUM still used heuristically in IDS.

### [begum2026conceptdrift] Begum & Mishra (2026) — Concept-Drift Aware Network Anomaly Detection Using Attention-LSTM and Multi-Dilated Densenet with Conformal Martingale
*2026 International Conference on Sustainability, Innovation & Technology (ICSIT)*; conference, peer-reviewed; verified; doi:10.1109/icsit70359.2026.11765575
*Method/contribution:* attention-LSTM + multi-dilated DenseNet anomaly detector with ADWIN drift detection, after which a conformal martingale framework adapts the model. *Limitation:* the martingale is used for drift adaptation, not for attack alarms; smaller conference. *Relation:* one of very few network-anomaly papers mentioning conformal martingales; not host-level sequential attack detection.

## Topic 6 — TinyML and lightweight IDS

### [ortizgarces2026nasoptimized] Ortiz-Garcés et al. (2026) — NAS-Optimized tinyML intrusion detection for ultralow-power IoT edge devices
*Internet of Things*; journal, peer-reviewed; verified; doi:10.1016/j.iot.2026.102034
*Method/contribution:* NAS-optimised TinyML IDS trained on a feature-aligned multi-domain dataset (TON_IoT, IoT-23, Edge-IIoTset, controlled data); 2.48 ms latency, <20 KB RAM, 0.39 mJ per inference on hardware. *Limitation:* supervised; closed-set. *Relation:* strongest recent TinyML IDS deployment numbers including TON_IoT — direct comparison point for our MCU footprint.

### [c2025tinymlbased] C et al. (2025) — TinyML-based intrusion detection systems for sustainable and energy-constrained IoT devices
*Results in Engineering*; journal, peer-reviewed; verified; doi:10.1016/j.rineng.2025.108013
*Method/contribution:* GraBoost-AAGT model deployed via TinyML for energy-constrained IoT intrusion detection (accuracy 99.5%, lower energy/CPU than edge ML). *Limitation:* dataset details vague in abstract. *Relation:* TinyML IDS background.

### [hamdouchi2025evaluating] Hamdouchi & Idri (2025) — Evaluating the performance of TinyML singular and ensemble techniques for intrusion detection in IoT networks
*Microprocessors and Microsystems*; journal, peer-reviewed; verified; doi:10.1016/j.micpro.2025.105172
*Abstract not retrieved — title only:* evaluates TinyML single and ensemble techniques for IoT intrusion detection. *Relation:* TinyML IDS benchmarking reference.

### [im2025tinymlbased] Im & Lee (2025) — TinyML-Based Intrusion Detection System for In-Vehicle Network Using Convolutional Neural Network on Embedded Devices
*IEEE Embedded Systems Letters*; journal, peer-reviewed; verified; doi:10.1109/les.2024.3475470
*Method/contribution:* low-complexity CNN IDS for CAN deployed on an nRF52840 MCU with TensorFlow Lite Micro (20.44 kB flash, 26.44 kB RAM, no quantisation). *Limitation:* in-vehicle domain. *Relation:* concrete MCU deployment figures for an NN-based IDS.

### [wang2023lightweight] Wang et al. (2023) — A lightweight intrusion detection method for IoT based on deep learning and dynamic quantization
*PeerJ Computer Science*; journal, peer-reviewed; verified; doi:10.7717/peerj-cs.1569
*Method/contribution:* DL-BiLSTM IDS with incremental PCA and dynamic quantisation for IoT (CIC-IDS2017, N-BaIoT, CICIoT2023). *Limitation:* dynamic quantisation, not full INT8 MCU deployment. *Relation:* quantisation for IoT IDS.

### [panopio2026from] Panopio et al. (2026) — From Sensor to Server: Deployable Lightweight ML for IoT Intrusion Detection Across Network Layers
*IEEE Internet of Things Journal*; journal, peer-reviewed; verified; doi:10.1109/jiot.2026.3680712
*Method/contribution:* deployable lightweight ML for IoT IDS across network layers, comparing ensembles vs simpler models, ONNX vs native C/C++ and quantisation on diverse hardware; releases an end-to-end pipeline. *Limitation (stated):* quantisation can increase latency/power for already-small models. *Relation:* important caution for our INT8 claims.

### [nassef2026lightweight] Nassef et al. (2026) — Lightweight and Energy-Aware Intrusion Detection for Industrial IoT Using TinyML and Edge AI
*Scientific Reports*; journal, peer-reviewed; verified; doi:10.1038/s41598-026-50690-0
*Method/contribution:* TinyML/edge-AI IIoT IDS with a GAT-based model, XAI and FL (20% lower communication in a 10-node simulation). *Limitation (stated):* 120–180 ms/sample on Raspberry Pi 4 limits real-time use; further compression and real deployment needed. *Relation:* FL + TinyML IDS with honest latency limits.

### [debernardis2026lightweight] De Bernardis et al. (2026) — Lightweight Machine Learning Intrusion Detection for IoT/IIoT Networks: Quantisation Strategies and Physical Deployment on Resource-Constrained Microcontrollers
*Electronics*; journal, peer-reviewed; verified; doi:10.3390/electronics15132869
*Method/contribution:* quantised classical ML IDS models deployed on Arduino Mega (8 KB SRAM) and ESP32-C3, with bit-exact firmware/float agreement; LightGBM INT8 best accuracy–size trade-off. *Limitation (stated):* large cross-domain shift to CIC-IoT2023 shows an open generalisation gap. *Relation:* rigorous MCU deployment methodology to mirror in our TinyML evaluation.

### [anuva2025lidit] Anuva et al. (2025) — LIDIT: Low-Latency Intrusion Detection in IoMT Devices using TinyML
*GLOBECOM 2025 - 2025 IEEE Global Communications Conference*; conference, peer-reviewed; verified; doi:10.1109/globecom59602.2025.11432258
*Method/contribution:* LIDIT, low-latency IoMT IDS with input segmentation, FP16/INT8 post-training quantisation (0.19 MB) and real-time SYN-flood detection on Raspberry Pi Zero 2 W (15.25 ms). *Limitation:* single-board computer, not MCU. *Relation:* INT8 PTQ IDS reference.

### [li2025cognitive] Li et al. (2025) — Cognitive IoT and Edge Computing for Intrusion Detection with Federated TinyML
*2025 IEEE World AI IoT Congress (AIIoT)*; conference, peer-reviewed; verified; doi:10.1109/aiiot65859.2025.11105231
*Method/contribution:* three-layer architecture (TinyML inference on IoT, training at edge, FL in cloud) on N-BaIoT with outlier-resistant scaling, feature reduction and quantisation; FL over the intersection of reduced features beats local models. *Limitation:* N-BaIoT only. *Relation:* federated TinyML IDS architecture close to ours.

## Recent (2022–2026) foundational references from Part A

### [vovk2022algorithmic] Vovk et al. (2022) — Algorithmic Learning in a Random World
*Springer International Publishing*; book, peer-reviewed; verified; doi:10.1007/978-3-031-06649-8
*Contribution:* second edition of the conformal prediction monograph, including conformal testing/test martingales (chapters on testing exchangeability and efficiency of conformal testing appear in OpenAlex). *Relation:* primary reference for conformal p-values, Mondrian conformal predictors and conformal test martingales.

### [shin2024edetectors] Shin et al. (2024) — E-detectors: A Nonparametric Framework for Sequential Change Detection
*The New England Journal of Statistics in Data Science*; journal, peer-reviewed; verified; doi:10.51387/23-nejsds51
*Method/contribution (Crossref abstract):* e-detectors — sums of e-processes started at consecutive times — give nonparametric sequential change detection with non-asymptotic average-run-length (false-alarm) bounds, with Shiryaev–Roberts- and CUSUM-style constructions and near-optimal delay in some cases. *Relation:* core theory for our e-value accumulation per host.

### [ramdas2023gametheoretic] Ramdas et al. (2023) — Game-Theoretic Statistics and Safe Anytime-Valid Inference
*Statistical Science*; journal, peer-reviewed; verified; doi:10.1214/23-sts894
*Contribution:* review of game-theoretic statistics and safe anytime-valid inference (test martingales, e-values, betting). *Relation:* theoretical background for anytime-valid alarms.

### [bates2023testing] Bates et al. (2023) — Testing for outliers with conformal p-values
*The Annals of Statistics*; journal, peer-reviewed; verified; doi:10.1214/22-aos2244
*Method/contribution:* conformal p-values for nonparametric outlier detection from a multiple-testing view; proves they are positively dependent and enable exact (marginal-sense) FDR control, and introduces conditionally valid, independent p-values via concentration inequalities. *Relation:* justifies treating AE scores as conformal p-values and combining them.

### [angelopoulos2023conformal] Angelopoulos & Bates (2023) — Conformal Prediction: A Gentle Introduction
*Foundations and Trends® in Machine Learning*; journal, peer-reviewed; verified; doi:10.1561/2200000101
*Contribution:* tutorial on conformal prediction: distribution-free, finite-sample-valid uncertainty sets usable with any pre-trained model. *Relation:* accessible conformal reference for readers.

### [arp2022dos] Arp et al. (2022) — Dos and don'ts of machine learning in computer security
*31st USENIX Security Symposium (USENIX Security 22)*; conference, peer-reviewed; verified; https://www.usenix.org/conference/usenixsecurity22/presentation/arp
*Contribution (title/venue only; abstract not retrieved from USENIX page):* identifies common pitfalls of ML in security research. *Relation:* justifies our leakage controls and realistic evaluation (leave-one-attack-out, per-host splits).
