# English core modules (phases 1–9): notes

Source: `rapor/_head.js`, `rapor/_body.js` (sections 3–8), `rapor/values.json`, `rapor/make_final_values.py`.
Nothing in `rapor/` was modified. All numbers come from the same `values.json` accessors as the Turkish source; only the
display format changed: decimal point, thousands comma, `45.6%`. Rounding is the same (`toFixed`).

## Files

| File | Content |
|---|---|
| `_head_en.js` | English helpers. Exports `P, H1, H2, H3, B, EQ, callout, pageBreak`; `table(head, rows, widths, caption, {key, note, leftAll})` (caption **above**: "Table n."); `figure(file, caption, widthIn, {key})` (caption **below**: "Fig. n."); global counters `TAB`, `FIG`; `XREF`, `tabNum/figNum/tabRef/figRef` (cross-references; a reference to a key that does not exist yet reserves the next number, so use it only when that float is the next of its kind); citations `CITE_ORDER`, `citeNum`, `cite`, `withCites`, `KNOWN_CITE_KEYS`; number formatting `nf, pc, pt, pv, th, seedsOf`; all value accessors (`V, fl, flt, own, ab, i8, rb, f2ok, f5, f5a, cost5, tinyC, e1, e3, b2, tierU, e2r, fst, epo, ...`); labels `SCN, SCN_LAB, PROT, PLAB, PLAB_SHORT, PS`; `EN_STYLES` (Heading1–3) and `EN_NUMBERING` (bullet reference `"bul"`) for the assembler's `Document`. Paths: `EN_DIR` (env `TFT_EN_DIR` → script folder → cwd → fixed path), `FIGDIR = EN_DIR/figs`, `VALUES_PATH = ../../rapor/values.json`. |
| `_core_en.js` | Section functions and `abstractCoreFacts` (below). Defines globals `MLAB, PKEY, TLAB, RCLAB, flFull, tinyTab, rcTab, robTab`; it does **not** define `C`. |
| `make_figs_en.py` | Figure part of `make_final_values.py`, same inputs (`colab_sonuclari/`), same computations, English labels; writes `figs/*.png` (same file names). Only layout change: the "β = 4%" label in `int8_esik.png` was moved right (it overlapped the longer English y-axis label). Run `python -I make_figs_en.py`. |
| `test_build_en.js` | Test assembler: `node test_build_en.js` → `_core_test.docx` (uses `rapor/node_modules` via NODE_PATH). |
| `verify_en.py` | Checks (b) and (c): `python -I verify_en.py`. |

Citation syntax in any helper text (paragraphs, bullets, headings, captions, table cells, notes): `[@key]`, `[@k1,k2]` → `[n]`, `[n, m]`, numbered by first appearance across the whole manuscript (so the assembler's Introduction/Related Work, if called first through the same helpers, get the lower numbers). Equation helper `EQ(text, {label})` gives a centred line with optional "(label)".

## Functions and subsection numbers

| Function | Subsections | Source |
|---|---|---|
| `secFramework(C)` | 3.1 Model and training · 3.2 Conformal p-value and three-way decision rule (2 `EQ` lines) · 3.3 UNCERTAIN resolution: host trust signal · 3.4 Federated learning (P1–P4 bullets) · 3.5 TinyML, robustness and ablation design | §4.1–4.5 |
| `secSetup(C)` | 5.1 Dataset and preprocessing (incl. 21-feature device set) · 5.2 Data split (table) · 5.3 Leakage check · 5.4 Evaluation protocol and statistical analysis · 5.5 Computing environment → **N = 5** (5.6 free) | §3, §4.6 (+ the Colab/T4 sentence of §1) |
| `secResults(C)` | 6.1–6.11, same order and content as §5.1–5.11 (6.4 = host signal and sparse attacks, unchanged) → ends at **6.11** | §5.1–5.11 |
| `secDiscussionCore(C)` | 2 paragraphs, no heading | §6 |
| `secLimitationsCore(C)` | 6 bullets, no heading | §7 |
| `secConclusionCore(C)` | 1 paragraph + "Future work:" + 4 bullets, no heading | §8 |

H2 is used for the subsections; the assembler supplies the H1 titles ("3. The TrustFed-TinyIDS Framework", "5. Experimental Setup and Evaluation Protocol", "6. Results and Comparative Analysis"). Internal references point to the new numbering (Section 6.x). The Turkish callout boxes ("Federe öğrenme için sonuç", "LOFO için sonuç") became bold-lead paragraphs ("Summary for federated learning.", "Summary for LOFO."). Appendix A (run folders) and the §1 summary table are not included.

## Tables and figures (numbers if no float precedes Section 3; numbering is dynamic)

Tables: 1 data split (5.2, key `split`) · 2 baseline models (6.1, `baseline`) · 3 alarm/review load (6.3, `tiering`) · 4 host-window detection vs ρ (6.4, `sparse`) · 5 FL diagnostic, seed 0 (6.5, `fldiag`) · 6 unseen ANOMALY by protocol/split, 53 features (6.5, `flmain`) · 7 all FL/central/local models, 53 features (6.5, `flfull53`) · 8 TinyML size/RAM/latency/Spearman (6.7, `tiny`) · 9 INT8 threshold validity (6.7, `int8`) · 10 corrupted input FPR/missed (6.8, `robfpr`) · 11 corrupted input F1/coverage/risk, 53 (6.8, `rob53`) · 12 same, 21 (6.8, `rob21`) · 13 ablation, 53 (6.9, `abl53`) · 14 ablation, 21 (6.9, `abl21`) · 15 risk–coverage, 53 (6.9, `rc53`) · 16 risk–coverage, 21 (6.9, `rc21`) · 17 53 vs 21 features (6.10, `device`) · 18 all FL/central/local models, 21 features (6.10, `flfull21`) · 19 LOFO folds meeting criterion (6.11, `lofo`). **19 tables.**

Figures: 1 per-family decisions `aile_kararlari.png` (6.2, key `families`; referenced from 6.1 by pre-assignment) · 2 sparse attacks `seyrek.png` (6.4, `sparse`) · 3 FL vs central `fl_merkezi.png` (6.5, `flcentral`; referenced again in 6.10 "right") · 4 validation loss at cap `val_hist.png` (6.5, `valhist`) · 5 INT8 UNCERTAIN `int8_esik.png` (6.7, `int8`) · 6 risk–coverage `risk_kapsama.png` (6.9, `rc`) · 7 LOFO `lofo.png` (6.11, `lofo`). **7 figures.** Keys are in separate namespaces for tables and figures; Phase 10 code should use other keys.

## Citations used (key → place)

vovk2005alrw, bates2023outliers → 3.2 p-value · angelopoulos2023 → 3.2 marginal guarantee · chow1970 → 3.2 deferral (UNCERTAIN) · liu2008iforest → 3.2 Isolation Forest (first mention) · hsu2019noniid → 3.4 Dirichlet split · mcmahan2017, li2020fedprox → 3.4 protocols · jacob2018quant → 3.5 INT8 conversion · moustafa2021toniot, alsaedi2020toniot → 5.1 TON_IoT · arp2022 → 5.3 leakage · wilcoxon1945, holm1979 → 5.4 · geifman2017 → 5.4 coverage/selective risk · kairouz2021 → 6.5 hypothesis H3 · banbury2021mlperftiny → 6.7 MCU RAM range · sommer2010 → limitations bullet 1. All 18 keys used once.
Order of first appearance in the test build: vovk2005alrw, bates2023outliers, angelopoulos2023, chow1970, liu2008iforest, hsu2019noniid, mcmahan2017, li2020fedprox, jacob2018quant, moustafa2021toniot, alsaedi2020toniot, arp2022, wilcoxon1945, holm1979, geifman2017, kairouz2021, banbury2021mlperftiny, sommer2010.

## abstractCoreFacts

`{ key: { value, desc } }`, values formatted in English: aeParams 4,829 · normalAnomalyRate 0.98% · normalUncertainRate 4.01% · centralUnseenAnomaly 45.6% · centralUnseenUncertain 37.7% · centralUnseenMissed 16.7% · alarmPrecision1pct 38.8% · hostDenseW50 100% · hostSparseMax 4.6% · flP1IID 2.1% · flP3IID 40.1% (p_Holm 0.193) · flP3IIDMissedGap 3.1 points (additional test) · flP3Dir1 35.7% · flP3Dir01 11.3% · flCapCaveat 95 runs · int8SizeKB53 12.9 KB · int8SizeKB21 10.0 KB · int8DeviceInheritedFPR 1.40% · int8DeviceRecalFPR 0.85% · int8DeviceRecalMissedCost 4.8 points · int8LatencyNote 1.75 µs (Colab CPU) · deviceUnseenAnomaly 52.7% · deviceUnseenMissed 18.4% · deviceFLpHolmRange 0.77–1.00 · lofoFoldsW20 0 / 9 · lofoFoldsW50 8 / 9 · lofoFoldsW100 8 / 9 · lofoRFRecallRange 71.5%–99.7%.

## Wording decisions

- First person → third person/passive. "ek test" → "additional test" (no Holm correction, stated in 5.4). "Aşama 5–9" → "the experiments of Sections 6.5–6.9".
- Turkish file names (`*_ozet.csv`, `F3_fl_istemci_tum_tohumlar.csv`, `F4_…`) replaced by "the summary CSV files of the output folders" and "the per-client result files of the output folders (53- and 21-feature models)". Internal run labels F3/F4 replaced by "53-feature"/"21-feature".
- `PLAB` (text, Table 6, bullets in 3.4) = faithful long labels; `PLAB_SHORT` (figure legends) = the short labels requested.
- Negative differences keep the hyphen-minus as in the source (e.g. "-9.0 points").
- Caveats kept in place: FL runs stopped at the cap while improving (6.5, limitations); FedProx only μ = 0.01 (6.5, limitations); host experiments are simulations and sparse analysis exploratory (3.3, 6.4, limitations); latency on Colab CPU, RAM a rough estimate (6.7, Table 8 note, limitations); additional tests without Holm (5.4, limitations); RC curves for IID FL models only (Tables 15–16 note, Fig. 6 caption); 2.8% duplicated benign test vectors in the 21-feature set (6.10).

## Verification (node test_build_en.js; python -I verify_en.py)

(a) Builds without error: 19 tables, 7 figures, 18 citations.
(b) Multiset of numbers, Turkish report sections 3–8 vs English core (Turkish decimal comma → point, thousands removed; section, table, figure and citation numbers and software version strings excluded; digits glued to letters such as P1/F3/A3 excluded): 1,649 vs 1,650. Remaining differences, all genuine (no translation errors):
- English +2 × "10": sentence from the Turkish §1 summary added to 5.5 ("10 training seeds", "10 separate seeds" for LOFO).
- English +2 × "21", +1 × "53": "(53- and 21-feature models)" replaces the file names F3_/F4_ in 6.6; "the 21-feature set" replaces "F4’te" in the Table 14 caption.
- Turkish +2 × "5", +2 × "9": "Aşama 5–9" (twice) became "Sections 6.5–6.9" (section numbers are excluded from the count).
During checking, one extra "1" from an added paraphrase ("divided by n + 1") was removed by rewording ("n plus one").
(c) No Turkish characters (ğ ş ı İ ç ö ü), no Turkish words from a 40-word list, no "draft"/"taslak", "NaN", "undefined", "null", "Infinity", "midterm", "professor"; no "we"/"I".
