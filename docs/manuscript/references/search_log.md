# Search and verification log — TrustFed-TinyIDS reference base

Date of searches: 2026-11-16. Tools: Python `requests` (generic User-Agent `TrustFed-TinyIDS-refcheck/1.0`, no e-mail, ~0.4 s between calls, responses cached), WebSearch/WebFetch for pages the APIs do not cover. Scripts and raw API caches: `C:/Users/moham/AppData/Local/Temp/claude/aaa9cd04642cf698/a7acfc37-471a-4f4b-bdcc-ca88207a8ace/scratchpad/refs/` (`partA*.py`, `partB*.py`, `partC*.py`, `verify_recent.py`, `build.py`, `cache/`). No PDFs were downloaded.

## Totals

- Records in `references_verified.csv`: **127**
- By category: A:conformal-and-e-values: 15, A:datasets-and-IDS: 7, A:federated-learning: 4, A:selective-classification: 2, A:sequential-detection: 12, A:statistics: 4, A:tinyml-and-quantisation: 2, A:trust-and-reputation: 2, B:closest-prior-work: 8, C1:federated-IDS: 11, C2:zero-day/unseen: 11, C3:conformal/uncertainty-IDS: 11, C4:trust/reputation: 11, C5:sequential/low-rate: 11, C6:TinyML/lightweight: 10, C7:novelty-conformal-sequential: 6
- Verification status: verified: 125, partially_verified: 2; NOT_VERIFIED items are listed below and were **not** added to the CSV.
- Peer review: yes: 119, no: 7, unclear: 1

## Part A — foundational references

Method: Crossref `/works/<DOI>` for every listed DOI (all 36 resolved). Items without DOI were checked on PMLR volume pages (v54, v60, v152), MLSys/NeurIPS proceedings pages and their BibTeX files, the USENIX Security '22 page (BibTeX), arXiv API, OpenAlex title search and the Royal Holloway research portal. DBLP was **not** usable: the DBLP API returned a bot-protection challenge page (HTTP 202 'Making sure you're not a bot'); it was not bypassed.

Details that differ from, or add to, the request:
- **Shin, Ramdas, Rinaldo** — NEJSDS **vol. 2, no. 2, pp. 229–260, 2024** (online 1 Dec 2023; Crossref lacks volume/issue, taken from the NEJSDS article page).
- **Tartakovsky et al. 2006** — four authors: Tartakovsky, Rozovskii, Blazek, Kim; vol. 54, no. 9, pp. 3372–3382.
- **Tartakovsky, Nikiforov, Basseville 2014** — Crossref/OpenAlex title is just 'Sequential Analysis'; full subtitle confirmed by Google Books/ACM DL listings (ISBN 978-1-4398-3820-4).
- **Wang, Zhang, Shin (INFOCOM 2002)** — Crossref has no date; vol. 3, pp. 1530–1539; OpenAlex dates it 2003 (online). Kept 2002 (conference year).
- **Laxhammar & Falkman** — online 2013, issue 2015, vol. 74, no. 1–2, pp. 67–94.
- **Kairouz et al.** — Crossref lists only 2 authors; full author list (OpenAlex) used, vol. 14, no. 1–2, pp. 1–210.
- **Vovk, Gammerman, Shafer 2005** — Crossref record has no authors; authors from OpenAlex.
- **Volkhonskiy et al. 2017** — PMLR author order is Volkhonskiy, **Burnaev**, Nouretdinov, Gammerman, Vovk (arXiv order differs); PMLR 60:132–153 (COPA 2017 is a 'Workshop').
- **Vovk et al. 2021 (Retrain or not retrain)** — PMLR 152:191–210.
- **Fedorova et al. 2012** — Proc. 29th ICML, pp. 1639–1646, Omnipress (Royal Holloway portal; arXiv:1204.3251). No DOI.
- **Vovk, Nouretdinov, Gammerman 2003** — Proc. 20th ICML, pp. 768–775, AAAI Press. No DOI.
- **McMahan et al. 2017** — PMLR 54:1273–1282.
- **Li et al. 2020 (FedProx)** — Proc. MLSys, vol. 2, pp. 429–450.
- **Arp et al. 2022** — USENIX Security '22, pp. 3971–3988, eight authors.
- **Banbury et al. 2021** — NeurIPS Datasets & Benchmarks, vol. 1; proceedings list 19 authors, arXiv lists 22.
- **Geifman & El-Yaniv 2017** — NIPS 30; proceedings BibTeX has no pages.
- **Holm 1979** — Scand. J. Statist. 6, 65–70. The DOI 10.2307/4615733 shown by OpenAlex is **not registered** (Crossref and doi.org return 404): cite without DOI.
- **Wilcoxon 1945** — Crossref/OpenAlex give only first page 80 (end page not in metadata).
- **Liu, Ting, Zhou 2008** — Crossref gives 'Zhou, Z.'; standard 'Z.-H. Zhou' used. **Chow 1970** — Crossref 'C. Chow'; 'C. K. Chow' used.
- **Mondrian confidence machine** — exists as Vovk, Lindsay, Nouretdinov, Gammerman, *Working Paper 4*, On-line Compression Modelling project, Royal Holloway, March 2003 (Royal Holloway portal). Citable as a technical report (not peer-reviewed); pair it with the 2005/2022 book.
- **Hsu, Qi, Brown 2019** — confirmed preprint (arXiv:1909.06335, no journal_ref).

## Part B — closest prior works

| Item | Outcome |
|---|---|
| CUMAD (arXiv 2404.13690) | Verified: Mainuddin, Duan, Dong, 'Detecting Compromised IoT Devices Using Autoencoders with Sequential Hypothesis Testing', IEEE BigData 2023, pp. 1344–1351, doi:10.1109/BigData59044.2023.10386399 (arXiv is the preprint). |
| Sugiantoro 2026 (Zenodo 23429756) | **Partially verified**: Zenodo record exists (resource type *software*, 2026-10-17, Sugiantoro & Akhmad Hafizuddin) with code/logs 'for the paper'; the paper itself was not found in Crossref, OpenAlex or arXiv. v2 = record 23430077. |
| ConFID 2026 | Verified: Farsimadan, Moradi, Palmieri, *Internet of Things* vol. 40, art. 102078, 2026, doi:10.1016/j.iot.2026.102078. No abstract via API; ScienceDirect page returned 403. |
| Rheey & Park, ICML 2026 workshop | **Partially verified**: 'Toward Reliable Intrusion Monitoring for O-RAN Based Networks with Conformal False Alarm Control', poster at the 2nd AI4NextG Workshop, ICML 2026 (icml.cc/virtual/2026/78428). No DOI/proceedings record. A GLOBECOM 2026 version listed on the author's homepage was not verified. |
| Park et al. arXiv 2609.27202 | Verified preprint: Park, Bae, Ramachandran Prabhu, Saha, Li, 'Reliable Federated TinyML Deployment for IoT Security' (23 Sep 2026). |
| TCUQ arXiv 2508.12905 | Verified preprint: Lamaakal, Yahyati, El Makkaoui, Ouahbi, Maleh (Aug 2025). Generic streaming TinyML, not IDS. |
| TRACE | Verified: Le, Arifuzzaman, Bao, 'TRACE: Feature-Space Feasible Action Contracts for Explainable Intrusion Triage', *Electronics* 15(15):3291, 2026, doi:10.3390/electronics15153291. |
| IoT-Sentinel | Verified: Verma, Kumar, Geetha, Grace Shalini, ICICI 2026, pp. 242–249, doi:10.1109/ICICI68773.2026.11580820. |

Queries used: arXiv API id_list lookups; Zenodo API `/api/records/<id>`; Crossref `query.bibliographic` with the exact titles; WebSearch for 'ConFID one-class autoencoder conformal …', 'Rheey Park ICML 2026 workshop …', 'TRACE conformal triage intrusion detection TON_IoT'; WebFetch of the ICML virtual page.

## Part C — OpenAlex topic searches

Query form: `https://api.openalex.org/works?filter=title_and_abstract.search:<terms>,publication_year:>2021&per-page=50[&sort=cited_by_count:desc]`. (The `from_publication_year` filter in the request is no longer accepted by OpenAlex — HTTP 400 — so `publication_year:>2021` was used. OpenAlex's anonymous daily budget is limited, so the query set was kept small.) 'Hits' = OpenAlex total count; 'Screened' = results returned and screened by title/venue.

| Topic | Query | Hits | Screened |
|---|---|---|---|
| T1 | `federated learning intrusion detection IoT` | 1614 | 50 |
| T1 | `federated intrusion detection non-IID heterogeneous` | 232 | 50 |
| T1 | `federated learning intrusion detection survey` | 222 | 50 |
| T2 | `zero-day attack detection autoencoder` | 469 | 50 |
| T2 | `unseen attack intrusion detection one-class` | 76 | 50 |
| T2 | `open-set intrusion detection unknown attacks` | 99 | 50 |
| T3 | `conformal prediction intrusion detection` | 38 | 38 |
| T3 | `conformal anomaly detection network traffic` | 31 | 31 |
| T3 | `uncertainty quantification intrusion detection calibration` | 22 | 22 |
| T4 | `trust-based intrusion detection IoT` | 751 | 50 |
| T4 | `trust management attack detection Internet of Things` | 320 | 50 |
| T5 | `low-rate DDoS attack detection` | 685 | 50 |
| T5 | `change-point detection network attack CUSUM` | 6 | 6 |
| T5 | `conformal martingale change detection` | 18 | 18 |
| T5 | `e-detector sequential change detection anytime-valid` | 1 | 1 |
| T6 | `TinyML intrusion detection` | 119 | 50 |
| T6 | `lightweight intrusion detection microcontroller quantization` | 14 | 14 |
| T6 | `model compression intrusion detection IoT knowledge distillation pruning` | 8 | 8 |
| NOV | `conformal martingale anomaly detection` | 5 | 5 |
| NOV | `conformal p-value CUSUM` | 1 | 1 |
| NOV | `Mondrian conformal prediction security` | 3 | 3 |
| NOV | `e-values anomaly detection` | 292 | 50 |
| NOV | `sequential conformal detection intrusion` | 5 | 5 |
| T5 | `CUSUM intrusion detection` | 27 | 27 |
| T5 | `quickest change detection cyber attack` | 2 | 2 |
| T5 | `sequential probability ratio test compromised devices` | 5 | 5 |
| T5 | `low-rate denial of service detection` | 781 | 50 |
| T5 | `stealthy attack sequential detection` | 66 | 50 |
| T5 | `EWMA attack detection network` | 39 | 39 |
| T4 | `reputation-based intrusion detection` | 205 | 50 |
| T4 | `trust score device intrusion detection IoT` | 117 | 50 |
| T4 | `trust-aware federated learning intrusion detection` | 143 | 50 |
| T2 | `leave-one-attack-out` | 1279 | 50 |
| T2 | `zero-day attack detection evaluation unseen attack families` | 34 | 34 |
| T1 | `federated anomaly detection IoT autoencoder unsupervised` | 26 | 26 |
| T1 | `personalized federated learning intrusion detection` | 120 | 50 |
| T3 | `conformal prediction abstention intrusion` | 2 | 2 |
| T3 | `conformal prediction anomaly detection false alarm` | 24 | 24 |
| T6 | `quantized neural network intrusion detection edge` | 62 | 50 |
| NOV | `conformal martingale` | 69 | 50 |
| NOV | `device-specific calibration anomaly detection IoT threshold` | 2 | 2 |
| NOV | `Mondrian conformal` | 232 | 50 |
| NOV | `e-process` | 219102 | 50 |

Additional targeted searches (novelty):
- arXiv API: `all:conformal AND all:CUSUM` (7), `all:conformal AND all:martingale AND all:attack` (2), `all:conformal AND all:martingale AND all:intrusion` (0), `all:"e-values" AND all:intrusion` (0), `all:"e-process" AND all:anomaly` (3, all physics), `all:conformal AND all:"Shiryaev"` (3), `all:conformal AND all:intrusion AND all:sequential` (2), `all:Mondrian AND all:conformal AND all:intrusion` (0), `all:conformal AND all:"change detection" AND all:network` (2), `abs:"conformal" AND abs:"intrusion detection"` (18).
- PMLR index scans: COPA 2021 (v152), COPA 2024 (v230), COPA 2025 (v266), COPA 2026 (v329), ICML 2025 (v267) — titles filtered for martingale/anomaly/intrusion/drift/attack/CUSUM/Mondrian.
- WebSearch: 'conformal p-values CUSUM OR conformal martingale OR e-values network intrusion detection sequential per-host IoT'; 'Validity and efficiency of the conformal CUSUM procedure …'.
- Every selected DOI was then cross-checked with Crossref `/works/<DOI>` (all resolved) and its abstract taken from Crossref or reconstructed from OpenAlex `abstract_inverted_index`.

### Inclusion / exclusion rules applied
- Included: 2022–2026, peer-reviewed journal or established conference preferred (IEEE/ACM Transactions, IoT-J, TIFS, TNSM, TDSC, Computers & Security, Computer Networks, Ad Hoc Networks, Automatica, Machine Learning, ACM CSUR, ICCPS/TCPS, GLOBECOM, ICC, COPA/PMLR, ICML); MDPI/Scientific Reports/IEEE Access/smaller IEEE conferences only when topically unique. Preprints only when directly novelty-relevant, and marked `preprint`, `peer_reviewed=no`.
- Excluded (examples): Zenodo/Figshare software or data records (e.g., 'conformal prediction for network intrusion detection' Zenodo 21441773/21781543, 'Label-Efficient Conformal Recovery…' 23422187, PULSE 23855473) — not peer-reviewed; SSRN/Research Square/Preprints.org postings; retracted items flagged by OpenAlex (e.g., 10.1109/tnse.2022.3191601, 10.1145/3523283); journals of uncertain standing (e.g., IJSRMT, IJISRT, 'Iconic Research and Engineering Journals'); off-topic hits from broad queries (biometric presentation-attack 'leave-one-out', physics 'e-process', medical/clinical conformal papers, SLE 'conformal martingales' in probability theory); dataset papers outside scope (Edge-IIoTset kept out of the CSV although highly cited — add if you use it).
- Considered but not added (could be added if needed): CRISP (MLISE 2026), ConformIDS (IJIES 2026), SAGE-IDS, SpikeGuard-LF, HADAR-UAV (CMC 2026), 'Conformalized Time Series Anomaly Thresholding' and 'nonconform' (COPA 2026, PMLR 329), 'Multivariate Change-Point Detection Using Feature-Based ICM' (PMLR 329:633–651), 'Detect Adversarial Examples with Exchangeability Martingale' (PMLR 266:758–761, 4-page short paper), 'Testing For Distribution Shifts with Conditional Conformal Test Martingales' (arXiv 2602.13848), 'Anytime-Valid Distribution Shift Detection via Predictive Rank Martingales' (arXiv 2609.00536), Edge-IIoTset (IEEE Access 2022).

## NOT_VERIFIED

None of the listed items ended NOT_VERIFIED. Two are only partially verified (Sugiantoro Zenodo software record; Rheey & Park ICML workshop poster). Items whose content is known only from a title (no abstract retrievable): ConFID, RESS 2026 conformal CPS paper, Computer Networks 2026 trust-aware federated IDS, JISA 2023 adaptable IDS, C&S 2025 energy-based open-set classifier, C&S 2023 stacked-unsupervised FL, C&S 2025 personalized FL, HawkEye, J. Process Control 2025, Microprocessors & Microsystems 2025, WCCST 2026 entropy-CUSUM — flagged in `annotations.md`.

## Novelty assessment (conformal p-values / e-values + CUSUM / SR / martingales at host level for IDS)

No peer-reviewed or preprint work was found that (i) converts per-flow anomaly scores into conformal p-values, (ii) calibrates them per host/device (Mondrian-style groups) and (iii) accumulates them with conformal CUSUM, Shiryaev–Roberts, test martingales or e-detectors to raise host-level intrusion alarms. Closest items:
1. **CUMAD** (Mainuddin et al., IEEE BigData 2023) — per-device AE + SPRT evidence accumulation; not conformal, parametric SPRT.
2. **Tartakovsky et al. 2006** (IEEE TSP) — CUSUM/SR change-point detection for network intrusions; parametric, not conformal.
3. **Vovk, Nouretdinov, Gammerman 2025** (COPA, PMLR 266) — conformal CUSUM theory; no security application.
4. **Shin, Ramdas, Rinaldo 2024** (NEJSDS) and **Bhattacharyya & Ramdas 2026** (arXiv) — e-detectors / conformal e-processes; generic.
5. **Volkhonskiy et al. 2017; Vovk et al. 2021; Eliades & Papadopoulos 2021/2024; Prinster et al. 2025 (WATCH)** — conformal martingales for change/drift detection; not IDS.
6. **Dong, Li, Boström 2026** (COPA, PMLR 329) — conformal test martingales to detect adversarial attacks on image sequences; security but not network/host IDS.
7. **FIRCE 2026 / FADES 2026** — conformal evaluation for drift detection in streaming IDS (retraining trigger, not attack alarm); **Begum & Mishra 2026** (ICSIT) — conformal martingale used for drift adaptation in network anomaly detection.
8. **ConFID 2026, Rheey & Park 2026, CASSIDY 2026, Massaad et al. ICC 2026, HTCCA-Conformal 2026, UAR-IDS 2026** — per-flow/per-sample conformal FPR control in IDS, no sequential accumulation.
9. Per-group calibration in security exists only as **class-conditional** (Mondrian by class): Zöller & Lawall CSR 2026 (Mondrian CP with TabPFN), UAR-IDS 2026 (class-conditional conformal rejection), Sugiantoro 2026 (Zenodo, per-class Mondrian) — none per host.
10. **Laxhammar & Falkman 2015** — sequential inductive conformal anomaly detection, but for trajectories.
Caveat: absence of evidence from API searches is not proof of absence; an IoT IDS survey (arXiv 2012.01174) reportedly mentions tracking per-device conformity values over time — the underlying primary source was not identified and should be checked.
