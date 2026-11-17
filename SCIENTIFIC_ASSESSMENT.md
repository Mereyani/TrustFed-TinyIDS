# Critical scientific assessment

## Manuscript v4: empirical reliability study (Option A), 2026-11-17

**Positioning.** The manuscript is now an empirical study of when and why calibrated IoT intrusion detection becomes unreliable. It covers four conditions:
- nominal;
- federated training;
- INT8 quantisation and input corruption;
- host-level aggregation.

No new algorithm is claimed.

**Remaining limitations**
1. **One dataset, without timestamps.** All results come from TON_IoT version B. Host-level results are simulations, and the confirmatory replications reuse the same data.
2. **Held-out families resemble the known ones.** A supervised random forest recognises every left-out family, with 71.5–99.7% recall.
3. **Federated training.**
   - The runs stopped at an epoch cap while still improving.
   - The "no significant IID difference" finding is non-significance, not equivalence.
   - Only one FedProx μ was tried.
4. **Few hosts and clients.**
   - Only 4–24 benign hosts are usable.
   - Worst-host statistics depend on 1–3 hosts.
   - The non-IID clients are very small.
5. **No microcontroller measurements and no adaptive attackers.**

**Journal readiness**
- **Ready for:** submission as an empirical or negative-results study to a journal that accepts single-dataset reliability studies with full disclosure, after the author has read and approved every statement.
- **Main reviewer risks:**
  - a single dataset;
  - simulated host streams;
  - a main text that is near the lower end of the page target;
  - several 2026 references that are recent or preprints and need a final publication-status check.
- **Before submission:**
  - format to the chosen journal's template;
  - consider adding a second dataset with timestamps, if feasible, which would most strengthen the paper;
  - check the two partially verified references and the author names flagged in `docs/manuscript/references/`.

---

## Earlier assessment (after Phase 10b)

All host-level numbers come from simulations on TON_IoT version B, a dataset without timestamps. They are for unseen families, F = 1000 flows per host-day and 10 seeds. Sources: `experiments/phase10/results/`, `experiments/phase10/results_10b/analysis/`, `RESULTS_SUMMARY.md`.

## 1. What genuinely improved?

- **Detection on the original split.**
  - On the split where the framework was developed, evaluating each host against its own benign reference made sparse attacks much easier to detect at the mean false-escalation budget.
  - Host-conditional counter at W = 200: 35.3% at a 5% attack share and 69.9% at 10% (Phase 10). Phase 10b, with new random streams, gave 30.7% and 68.4%.
  - The existing counter gave 1.4–2.0% and 8.7–8.8%.
  - The mean budget was met: 0.11–0.18 false escalations per host-week.
- **Methodology.**
  - Every Phase 10/10b threshold is now set on calibration data only, and the test-tuned diagnostic was withdrawn.
  - The mathematical claims are limited to what holds: marginal, per-flow validity.
  - The most promising configuration was re-tested under a pre-specified confirmatory protocol.
  - The device-model replication rests on a host map that was rebuilt locally and checked against the stored Colab map.
- **A clearer negative result.**
  - There was no evidence that likelihood-ratio e-values, CUSUM, Shiryaev–Roberts, EWMA, evidence decay or adaptive mixtures improve on simple window counting at equal cost at the horizons studied.
  - The anytime-valid thresholds did not control the budget.

## 2. Is the improvement statistically and operationally reliable?

**No.**

- **Statistically:**
  - On the original split the gain is consistent: 5 of 6 Holm-corrected comparisons in Phase 10b, and every seed at W ≥ 100.
  - It was **not reproduced** in any of the three replications: SWAP 2/6, DEVICE 0/6, DEDUP 2/6. The pre-specified verdict is "not reproduced".
- **Operationally:**
  - With the benign splits reversed (SWAP), or with a separately trained detector calibrated on one half of a split and evaluated on the other (DEVICE), every rule exceeded the budget several-fold. The existing counter was no exception: 2.9–11.9 false escalations per host-week across rules.
  - Even on the original split, the worst benign host exceeded the budget in about half of the seeds.
  - Detection is measured per window, not per day.

## 3. What is the defensible scientific contribution?

**Not a new detector.** Every component is established:
- Mondrian conformal calibration;
- the maximum of p-values;
- likelihood-ratio e-values;
- e-detectors;
- CUSUM, EWMA, Higher Criticism and the truncated product method.

**The defensible contribution is empirical and partly negative:**
- **(i) An evaluation protocol.**
  - It runs a pre-specified comparison followed by a confirmatory re-test, with multiple seeds.
  - All host-level rules share one operational false-escalation budget, and both average and worst-host behaviour are reported.
- **(ii) A finding about calibration.** Host-level false-escalation budgets calibrated on one benign sample did not transfer to another sample of the same hosts. A plausible driver is row multiplicity combined with a de-duplicated split.
- **(iii) Evidence on what matters.** On the original split, the reference against which p-values are computed mattered more than the accumulator, but this did not reproduce.
- **(iv) Where the framework's guarantees stop holding:**
  - per host;
  - across benign samples;
  - after INT8 conversion of the device model;
  - for small non-IID federated clients.

**Literature check.** A targeted re-check found per-class (not per-host) conformal calibration in IDS, per-device thresholds without conformal calibration (Hsu & Lin 2026), and per-unit Mondrian conformal anomaly detection outside security (Farouq et al. 2021). It found no IDS work that combines per-host conformal calibration with sequential accumulation. The novelty is therefore in the evaluation, not in the components.

**Positioning.** This could support a carefully framed empirical or negative-results paper. It does not support a claim of a new or superior method.

## 4. What limitations remain?

1. **Data.**
   - There are no timestamps and no second dataset.
   - The three replications reuse TON_IoT, so they can falsify a result but cannot independently confirm one.
2. **Simulated streams.**
   - Host streams are random orderings.
   - Attack windows are synthetic mixtures.
3. **Few hosts.**
   - Only 4–20 hosts are available, depending on W.
   - Worst-host results hinge on 1–3 large hosts.
4. **Non-blind design.** The design was not blind to test-split properties, and the host-conditional counter was found after the test results were seen. Phase 10b mitigates this but does not remove it.
5. **Untested attackers.** Adaptive and reference-poisoning attackers were not evaluated.
6. **Federated training.** The federated models stopped at an epoch cap while still improving, and only one FedProx μ was tried.
7. **No microcontroller measurements.**

## 5. Is the paper ready for SCI/SCIE journal submission?

**No.** Here is what is essential before submission:

- **(a) A dataset with timestamps and host identifiers.**
  - Use a temporal split per host: calibrate on earlier traffic, monitor later traffic.
  - Ideally add a second network.
  - Without this, the central host-level question cannot be answered.
- **(b) A pre-registered design for reference maintenance.** It should cover:
  - refresh;
  - drift detection;
  - poisoning resistance;
  - per-host budgets over time.
- **(c) A decision on the paper's focus.**
  - Option 1: an empirical paper on calibrated IoT detection whose host-level part is presented as a negative result.
  - Option 2: hold the host-level claim until (a) is done.
- **(d) Shortening.** Cut the manuscript to journal length and move the large tables to supplementary material.
- **(e) Final checks.**
  - The author must review every statement.
  - Confirm the current publication status of the 2026 preprints and conference items.
