# Phase 10 protocol: host-level evidence accumulation for sparse attacks

Written on 2026-11-16, before any test-stage run of Phase 10. Validation-stage runs had already started. This file fixes:

- the selection rule;
- the primary comparisons;
- the reporting rules.

Changes made after this point are logged in the "Deviations" section at the end.

## 1. What was known when this protocol was written (disclosure)

**Results already seen.** The designer had already seen the following before writing this protocol:

- the F5 sparse-attack results (existing host counter);
- the flow-level conformal p-value rates per family, which phases 3–9 already reported;
- the per-host benign flag rates in benign_val and benign_test for seeds 0 and 3. These were inspected on 2026-11-16 to understand the F5 budget violations.

**What that inspection showed.** Benign hosts are heterogeneous. Host 192.168.1.195 flags 13–35% of its flows at p ≤ 0.05, while most hosts flag 0–3%. This motivated the host-conditional reference.

**Smoke-run problem.** A first smoke run used a calibration estimator that assumed homogeneous hosts. Its false-escalation estimates were wrong, so it was replaced (see Deviations). No test-stage detection numbers have been computed.

## 2. Unchanged components

These components are reused exactly as they are:

- the AE scores per seed (0–9), the benign_cal conformal p-values, α = 0.01 and β = 0.04;
- the host map (`artifacts/resolution/host_rows.csv.gz`);
- the operational budget: B = 1 false escalation per host per week, at F = 1000 and F = 5000 flows per day;
- the F5 window sampling.

Nothing is retrained.

## 3. Factors

**ref**
- `pooled` is the existing p-value.
- `host` is p′ = max(p_pooled, p_host).
  - p_host is computed against the host's own benign_val flows. It is cross-fitted in two folds.
  - Hosts with fewer than 20 reference flows per fold share a "low-traffic" reference built from all such hosts (a Mondrian category).

**Evidence and accumulator**

| Group | Methods |
|---|---|
| Window rules (fixed W) | W_COUNT_AU (existing rule), W_COUNT_A, W_FISHER, W_TPM (τ = 0.05), W_MINP, W_HC (HC+), W_EVID (sum of log LR e-values) |
| Sequential rules (reset after each alarm) | BCUSUM (Bernoulli CUSUM on the p ≤ 0.05 flag, with the same LR construction on two bins), EWMA_FLAG (λ = 2/(W+1)), EWMA_NLP (EWMA of −log p), E_CUSUM, E_SR, E_CUSUM_MIX (Vovk–Wang mixture calibrator, no attack data), E_CUSUM_LEAKY (decay 1 − λ), E_SR_ADAPT (average of e-SR over ρ0 ∈ {0.01, 0.02, 0.05, 0.10, 0.25, 0.50}) |
| Theory thresholds | E_CUSUM_TH, E_SR_TH, E_SR_ADAPT_TH: log R ≥ log(7F/B), the e-detector bound ARL ≥ 7F/B, with no data-driven calibration |

**Likelihood ratio.** The LR is fitted on the dev_val p-values of the six known families, with equal weight per family. It is made isotonic (non-increasing). The held-out families (ransomware, xss, mitm) are never used.

**ρ0 (design attack share)** ∈ {0.01, 0.02, 0.05, 0.10, 0.25}.

## 4. Calibration (identical budget for all methods)

**Window rules**
- Each rule uses a split-conformal quantile on 5,000 subsampled benign_val windows, at α_w = B·W/(7F). This is the F5 procedure.

**Sequential rules**
- Each rule uses the smallest threshold with (alarms + 1) / flows × 7F ≤ B.
- The threshold is found by bisection, counting alarms with reset, on 200 benign_val streams.
  - Each stream lasts 14 days and comes from one host, chosen in proportion to its benign_val flows.
  - Flows are drawn with replacement.
  - Hosts need at least 20 rows.

**Test data.** Benign_test is never used for calibration.

## 5. Validation stage (selection)

**Data**
- benign_val streams;
- dev_val known-family attack flows, using half B of a seed-specific random split of the dev_val vectors, drawn in proportion to their multiplicity;
- the LR is fitted on half A.

**Settings.** F = 1000; W ∈ {20, 50, 100, 200}; ρ ∈ {0.01, 0.05, 0.10, 0.25, 0.50}; seeds 0–9.

**Selection rule**
- **Candidates:** the Phase-10 family {W_EVID, E_CUSUM, E_SR, E_SR_ADAPT, E_CUSUM_LEAKY} × ref × ρ0.
- **Criterion:** mean known-family detection over ρ ∈ {0.05, 0.10} and W ∈ {20, 50, 100, 200}, averaged over seeds.
- **Constraint:** the seed-mean validation false escalation (weighted by host traffic) must be ≤ B.
- **Ties:** ties within 0.5 percentage points go to the simpler rule, in this order: W_EVID < E_CUSUM < E_SR < E_CUSUM_LEAKY < E_SR_ADAPT.
- **Result:** the selected configuration is called **P10** below. All other configurations are still reported.

## 6. Test stage

**Data.** Thresholds are calibrated on benign_val. Benign false escalations are measured on benign_test hosts. Attack flows come from dev_test (known) and heldout_test (unseen).

**Attack streams.** The F5 composition is kept: round(ρW) attack flows at random positions inside W flows.
- The W flows follow a 1,000-flow benign warm-up of the same host, used by the sequential rules.
- Window rules see the window aligned with the attack onset. This is the F5 protocol, and it favours window rules.

**Settings.** 300 streams per (family, ρ, W); F ∈ {1000, 5000}; all methods; both refs; ρ0 = the selected value.
- A ρ0 sensitivity analysis on the test set is reported as sensitivity only, never as selection.

**Metrics**
- host-level detection within the W attack-window flows;
- false escalations per host per week: the traffic-weighted mean, the worst host, and the number of hosts over budget;
- detection delay in flows, for detected streams; window rules decide at flow W;
- per-family detection for ransomware, xss and mitm;
- compute and memory per flow.

## 7. Primary comparisons and statistics

**Primary comparison (P1).** P10 vs the existing counter (W_COUNT_AU, pooled ref).
- Outcome: unseen-family detection at F = 1000.
- Grid: ρ ∈ {0.05, 0.10} × W ∈ {20, 50, 100, 200}, for 8 comparisons.
- Test: paired Wilcoxon signed-rank test over the 10 seeds, two-sided, with Holm correction over the 8 comparisons.
- Reported alongside: the mean difference and a 95% percentile bootstrap CI over seeds (10,000 resamples).

**Secondary comparisons.** P10 vs every other method on the same grid, with Holm correction within each comparison family. These are labelled secondary.

**Budget equivalence.** For every method the report states:
- whether the seed-mean false escalation on benign_test is ≤ B;
- the worst-host value;
- the number of hosts and seeds over budget.

A method that misses the budget on benign_test is reported as such, and its detection is not counted as a win.

**Simulation statement.** TON_IoT version B has no timestamps, so every host stream is a random ordering of the host's flows. All Phase 10 results are simulations, not deployment measurements.

## 8. Deviations

- 2026-11-16 (before any test run): the first calibration estimator for sequential rules took one first-passage time per stream. That assumes the same alarm rate on every host, and it badly underestimated the alarm rate on the noisy host. It was replaced by direct alarm counting with reset, plus bisection.
- 2026-11-16 (before any test run): the host-conditional reference (ref = host) and its low-traffic fallback category were added after the smoke run showed that pooled-reference sequential rules accumulate drift on one benign host.
- 2026-11-16, after validation and before the test run: two edge cases in `trustids/phase10.py` were fixed after unit tests found them.
  - First, `conformal_threshold` now matches `resolution.k_threshold` when the budget cannot be met with n calibration windows: it alarms only above every calibration value, where it previously never alarmed.
  - Second, likelihood-ratio bins without any conformal p-value are merged; such bins only occur when n_cal is small.
  - Neither change can affect the real-data runs. There, n_cal = 3,348, which gives every bin non-zero null mass, and there are 5,000 calibration windows, so (n + 1)·α_w ≥ 3.
- Validation result (`results/validation_selection.json`, applied by `select_phase10.py`):
  - **Selected P10:** ref = host, W_EVID, ρ0 = 0.01. Its criterion is 0.317 ± 0.056 (mean ± sd over seeds). The candidate with ρ0 = 0.02 was tied within 0.5 pp.
  - **Strongest validation result overall:** a baseline outside the candidate family, ref = host with W_HC (Higher Criticism), at 0.367. It is reported as a secondary comparison, as the protocol requires.

## 9. Test-stage outcome and post-test analyses (added after the test stage)

**Test-stage outcome (pre-specified analysis)**

The test run is `results/*_phase10_test_s0..s9`, analysed in `results/20261116-213748_phase10_test_s0/analysis/`.

- **Primary comparison:** P10 detected more unseen-family attacks than the existing counter at all 8 (W, ρ) points. The difference was significant after Holm correction at 7 of 8.
- **Benign false escalations:** P10 exceeded the budget on benign_test. For W ≥ 50 it averaged 1.32–1.78 per host-week, and at W = 200 7 of 10 seeds were over budget.
- **Conclusion:** under section 7 the detection gain is not credited, so the primary hypothesis is **not supported**.

**Post-test analyses.** These were defined after the test results were seen. They are exploratory, and every output is labelled as such.

1. `host_heterogeneity.py`: per-host benign flag rates, benign_val against benign_test. This is descriptive only.
2. `analyze_extra_phase10.py`: the host-conditional reference applied to the existing count rule, at the benign_val-calibrated thresholds, with Wilcoxon and Holm over the same 8 points. It improved detection over the pooled counter at 5 of 8 points and stayed within the mean budget for W ≥ 50. The worst host was still over budget in 3–6 of 10 seeds.
3. `tradeoff_phase10.py`: a matched-cost **oracle** diagnostic.
   - Thresholds are tuned **on benign_test** so that the realised false escalations stay at or below 1 per host-week. The thresholds are not deployable.
   - Result: the host-conditional counter was best at W ≥ 50, apart from W = 50, ρ = 0.05. The LR e-value window and e-CUSUM were significantly lower there.

## 10. Withdrawal (2026-11-17)

The matched-cost oracle diagnostic of section 9, item 3 (`tradeoff_phase10.py`), set its thresholds on benign_test. It is **withdrawn** from the manuscript, because no threshold may be tuned on test data.

- Its output files remain in `results/diagnostic_tradeoff/`, so that the history is complete.
- The exploratory host-conditional counter (item 2) was calibrated on benign_val only. It is re-tested with frozen rules in Phase 10b (`PROTOCOL_PHASE10B.md`).
