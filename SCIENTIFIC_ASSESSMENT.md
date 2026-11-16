# Critical scientific assessment (Phase 10 and manuscript readiness)

All numbers below are unseen families, F = 1000 flows per host-day, mean of 10 seeds. They come from a simulation on TON_IoT, a dataset without timestamps. The sources are `experiments/phase10/results/` and `RESULTS_SUMMARY.md`.

## 1. Did Phase 10 improve sparse-attack detection?

**In detection, yes. At the required false-escalation cost, not for the pre-specified configuration.**

**The pre-specified configuration (P10)** combined host-conditional p-values with a likelihood-ratio e-value window.
- At W = 200 it raised detection from 1.4% to 47.0% at a 5% attack share, and from 8.7% to 69.9% at 10%.
- It beat the existing counter at 7 of 8 points (Wilcoxon with Holm correction).
- It produced 1.32–1.78 false escalations per host-week on benign_test hosts for W ≥ 50, against a budget of 1. At W = 200, 7 of 10 seeds were over budget.
- The protocol does not credit a gain obtained above budget, so the pre-specified hypothesis is **not supported**.

**An exploratory, post-test analysis** applied the host-conditional reference to the existing count rule.
- Detection was 35.3% and 69.9% at W = 200.
- False escalations averaged 0.11 per host-week.
- The worst host was still over budget in 4 of 10 seeds.

## 2. Are the improvements statistically and operationally meaningful?

**Statistically.** At the calibrated thresholds, both the P10 gains and the exploratory host-conditional-counter gains are large and consistent across seeds. At W ≥ 100, P10 beat the existing counter in all 10 seeds, and the host-conditional counter beat it in 9–10 of 10 seeds. Two caveats apply:
- The exploratory comparison was defined after the test results were seen.
- The equal-cost diagnostic tunes its thresholds on test data, so it is an oracle.

**Operationally.** The host-conditional counter is plausible for deployment:
- it needs one stored threshold per host;
- it stays within the mean budget;
- it detects a third to two thirds of windows with a 5–10% attack share.

It is not yet demonstrated, for three reasons:
- worst-host budgets were violated;
- the streams are simulated, without real timing;
- detection is measured per window, not per day.

**Negative findings.** Sequential accumulators (CUSUM, Shiryaev–Roberts, EWMA, evidence decay, adaptive mixtures) added no detection at equal cost. Their only benefit was earlier alarms. Anytime-valid theory thresholds failed when benign hosts were heterogeneous.

## 3. Is there a defensible methodological contribution?

**No new detector is proposed.** Every ingredient is established:
- Mondrian conformal calibration;
- the maximum of p-values;
- likelihood-ratio e-values;
- e-CUSUM and e-SR (e-detectors);
- Higher Criticism and the truncated product method.

The reference search (127 verified records) found no study that applies per-host conformal calibration and sequential conformal evidence to intrusion alarms under an operational budget. Even so, combining existing techniques is not by itself novel.

**The defensible contribution is empirical:**
- a pre-specified, multi-seed comparison at equal budget;
- the finding that the per-host reference matters more than the accumulator;
- documented failure modes:
  - pooled guarantees per host;
  - transfer of calibration from validation to test;
  - theory thresholds;
  - INT8 thresholds for the device model;
  - federated calibration on small non-IID clients.

## 4. Remaining scientific weaknesses

1. **No timestamps.** Host streams are random orderings, and attack windows are synthetic mixtures.
2. **Calibration transfer failure.** This is likely worsened by de-duplication before splitting. It was not tested on temporally split data.
3. **Few benign hosts.** Only 4–20 had calibration data, depending on W. Worst-host results hinge on two hosts.
4. **The best configuration is exploratory.** It needs confirmation on independent data.
5. **One dataset in which families are similar.** Leave-one-family-out shows that a supervised model recognises every held-out family.
6. **No adaptive attacker, and no poisoning of the host reference.**
7. **The federated models were stopped at an epoch cap while still improving.** FedProx was tried with only one value of μ.
8. **No microcontroller measurements.** Latency was measured on Colab and laptop CPUs.

## 5. Is the manuscript ready for journal submission?

**No.** It is a complete, honest foundation, but the following work is essential first:

- **Data and validity**
  - (a) Confirm the host-conditional counter on data with real timestamps and a temporal split, preferably on a second dataset such as Edge-IIoTset (already pre-registered in the earlier proposal).
  - (b) Pre-specify and test reference maintenance (refresh, drift detection, resistance to poisoning), and report worst-host budgets over time.
- **Robustness and deployment**
  - (c) Evaluate adaptive low-rate attackers.
  - (d) Run the federated models to convergence and test more FedProx/personalisation settings.
  - (e) Measure the full pipeline on a real microcontroller.
- **Manuscript**
  - (f) Shorten the manuscript to journal length, moving the per-family and full-protocol tables to supplementary material.
  - (g) The author must review the generative-AI disclosure and every statement.
  - (h) Check the two partially verified references and the recent 2026 items for their final publication status.
