# Results summary

All numbers below are copied from the files named in each section. They are means over 10 seeds unless stated otherwise. Detailed tables are in `docs/manuscript/TrustFed-TinyIDS_Manuscript_EN.docx`.

## Phases 1–9: the framework

Source: `results/colab_runs/`. Values were extracted with `docs/previous_versions/final_report_tr/make_final_values.py`.

**Detector and decision rule**
- **Central AE** (53 features, 4,829 parameters), on unseen families (ransomware, xss, mitm):
  - 45.6% of flows flagged ANOMALY;
  - 16.7% missed (NORMAL);
  - the rest UNCERTAIN.
- **Benign rates:** ANOMALY 0.98% (target 1%), UNCERTAIN 4.01% (target 4%).

**Federated learning**
- Under the original protocol, IID FedAvg reaches only 2.1% ANOMALY on unseen families.
- With matched training (persistent optimiser, run to the cap) IID FedAvg reaches 40.1%. This is not significantly different from the central model. It misses more attacks in 9 of 10 seeds (additional test, no Holm correction).
- At Dirichlet 0.1 FedAvg reaches 11.3%.
- Every federated run that stopped at the 1,500-epoch cap was still improving.

**TinyML (INT8)**
- 53-feature model: inherited thresholds keep the ANOMALY level, but the UNCERTAIN band drifts.
- 21-feature device model: inherited thresholds break (benign ANOMALY rate 1.40%). Recalibration fixes this at a cost of 4.8 points more missed attacks.

**Leave-one-family-out**
- A supervised Random Forest recognises every held-out family (recall 71.5–99.7%). In TON_IoT, "unseen" therefore does not mean "dissimilar".

## Phase 10: host-level evidence accumulation (simulation)

Source: `experiments/phase10/results/`. Settings: F = 1000 flows per host-day, unseen families, W = 200.

| Configuration | Status | Detection at ρ = 0.05 | Detection at ρ = 0.10 | Benign false escalations per host-week (mean) |
|---|---|---|---|---|
| Existing counter, pooled reference | baseline | 1.4% | 8.7% | 0.50 |
| P10: host-conditional reference + LR e-value window, ρ₀ = 0.01 | pre-specified, selected on validation | 47.0% | 69.9% | 1.76 (over budget) |
| Host-conditional reference + existing count rule | exploratory | 35.3% | 69.9% | 0.11 |

**Pre-specified outcome**
- P10 beat the existing counter at 7 of 8 points (Wilcoxon with Holm correction).
- It exceeded the false-escalation budget on benign_test hosts, so the pre-specified hypothesis is **not supported**.

**Withdrawn.** An earlier matched-cost diagnostic set its thresholds on test data. It has been withdrawn.

**Sequential and anytime-valid rules**
- CUSUM, Shiryaev–Roberts, EWMA, evidence decay and adaptive e-SR detected no more than the window rules.
- Their advantage was earlier alarms within the window.
- The calibration-free anytime-valid thresholds did not control the budget under the pooled reference.

**Cost**
- Every binned rule needs a few ns per flow on a laptop CPU and at most a few hundred bytes per host.
- The host-conditional count rule needs one stored threshold per host.

**Limits**
- All host-level numbers come from a simulation: TON_IoT version B has no timestamps, so host streams are random orderings of flows.
- Budgets calibrated on benign_val did not transfer fully to benign_test.

## Phase 10b: confirmatory re-test (frozen rules, new streams)

Source: `experiments/phase10/results_10b/analysis/`. All rates are at B = 1 false escalation per host-week and F = 1000.

| Setting | Host-conditional counter better (Holm, of 6) | Host-conditional counter, mean false esc./wk (W 50 / 100 / 200) | Existing counter, mean false esc./wk | Verdict |
|---|---|---|---|---|
| S1 MAIN (original split, new streams) | 5 | 0.27 / 0.22 / 0.18 | 1.76 / 0.94 / 0.53 | supported |
| S2 SWAP (benign splits reversed) | 2 | 9.04 / 8.48 / 8.08 | 4.23 / 7.37 / 6.91 | not supported |
| S3 DEVICE (21-feature detector, halves of benign_test) | 0 | 5.51 / 5.44 / 6.60 | 3.75 / 3.80 / 4.79 | not supported |
| S4 DEDUP (distinct vectors only) | 2 | 0.27 / 0.45 / 1.64 | 0.39 / 0.49 / 0.83 | not supported |

**Pre-specified overall verdict: not reproduced.**

- **Calibration transfer.** Host-level false-escalation budgets calibrated on one benign sample did not hold on another. In SWAP and DEVICE every rule failed the budget several-fold.
- **Worst hosts.** The worst host exceeded the budget in at least half of the seeds for every rule and setting. The one exception was the existing counter in MAIN.
- **Other rules.** Sequential rules did not outperform window counting.
