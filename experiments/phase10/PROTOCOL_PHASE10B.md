# Phase 10b protocol: confirmatory test of host-conditional calibration

Written on 2026-11-17, before any Phase 10b run. The Phase 10 results, including the exploratory host-conditional counter and the withdrawn test-tuned diagnostic, were known when this protocol was written. Phase 10b exists to test that exploratory finding with rules that are now frozen, in settings where the conclusion could fail.

## 1. Question

Does host-conditional (Mondrian) calibration of the conformal p-values give a reproducible advantage in sparse-attack detection under a realistic false-escalation budget?

- No threshold is ever set with evaluation data.
- Average and worst-host behaviour are both reported.

## 2. Frozen rules (definitions identical to Phase 10; nothing is tuned)

| Code | Rule | Reference |
|---|---|---|
| EXIST | count of p ≤ α + β in a window of W flows (existing counter) | pooled |
| HCOUNT | the same count rule | host-conditional p′ = max(p, p_host) |
| P10 | sum of log LR e-values in the window, ρ₀ = 0.01 (selected in Phase 10) | host-conditional |
| CUSUM-P / CUSUM-H | Bernoulli CUSUM on the flag p ≤ α + β (ρ₀ = 0.01) | pooled / host-conditional |
| eCUSUM-H | e-CUSUM with the LR e-values (ρ₀ = 0.01) | host-conditional |
| EWMA-P / EWMA-H | EWMA chart on the flag, λ = 2/(W + 1) | pooled / host-conditional |

**Fixed parameters**
- α = 0.01 and β = 0.04.
- The host reference uses two-fold cross-fitting on the calibration split. A host needs at least 20 reference units per fold; hosts with fewer share one low-traffic fallback reference.
- 5,000 calibration windows for window rules.
- Sequential thresholds are found by bisection on (alarms + 1)/flows × 7F ≤ B, using 200 calibration streams of 14 days.
- Attacked streams: 300 per (family, ρ, W), each with a 1,000-flow warm-up.

## 3. Settings

| Setting | Detector | Calibration units (thresholds and host reference) | Evaluation benign units | LR fitted on | Independence from Phase 10 |
|---|---|---|---|---|---|
| S1 MAIN | 53-feature AE, seeds 0–9 | benign_val rows | benign_test rows | dev_val (known families) | none in data; new random streams only. A re-estimation, not a replication |
| S2 SWAP | 53-feature AE | benign_test rows | benign_val rows | dev_val | roles of the two benign splits reversed |
| S3 DEVICE | 21-feature device AE, trained separately (seeds 0–9) | half A of the benign_test vectors (random per seed; all rows of a vector stay in one half) | half B of the benign_test vectors | half A of the dev_test vectors (known families); known-family detection uses half B only | independent detector and feature set; same dataset. The device model has no saved benign_val or dev_val scores, so both roles come from disjoint halves of benign_test |
| S4 DEDUP | 53-feature AE | benign_val distinct vectors (one unit per vector, host of its representative row) | benign_test distinct vectors | dev_val | removes the repeated rows suspected of causing the calibration-transfer failure |

**What none of these settings is.** None is a second dataset or a temporal split. TON_IoT version B has no timestamps, and no second dataset with host identifiers is available in the project without new downloads and retraining. This limitation is stated wherever Phase 10b results are reported.

**Attacks.** Held-out families (ransomware, xss, mitm) come from heldout_test. Known families come from dev_test, or from half B of dev_test in S3.

**Grid**
- Budgets B ∈ {0.5, 1, 2} false escalations per host-week at F = 1000 flows/day, and B = 1 at F = 5000.
- W ∈ {50, 100, 200}.
- ρ ∈ {0.05, 0.10, 0.25}.

**Random streams.** They are new and come from the generator seeded with 5,000,000 + 100,000·setting + seed. The host-reference folds come from 6,000,000 + seed.

## 4. Primary hypothesis and success criteria (per setting)

**H1.** At B = 1 and F = 1000, HCOUNT detects more unseen-family sparse attacks than EXIST.

**Grid of comparisons.** W ∈ {50, 100, 200} × ρ ∈ {0.05, 0.10}, which gives 6 comparisons.

**Test.** Paired two-sided Wilcoxon signed-rank tests over the 10 seeds, Holm-corrected within the setting.

**A setting supports H1 if both of the following hold:**
- (a) HCOUNT > EXIST with Holm p < 0.05 in at least 4 of the 6 comparisons;
- (b) the seed-mean traffic-weighted realised false-escalation rate of HCOUNT on the evaluation hosts is ≤ B for every W ∈ {50, 100, 200}.

**Worst host (secondary, always reported).** The number of seeds whose worst evaluation host exceeds B.

**Overall conclusion "reproducible advantage".** H1 is supported in S1 and in at least two of S2–S4. If H1 is supported in S1 but in fewer than two of S2–S4, the advantage is called "not reproduced". Every outcome is reported.

## 5. Secondary analyses (descriptive, Holm within each family of tests)

1. **All eight rules at each budget:**
   - detection on unseen and known families;
   - realised mean and worst-host false escalations;
   - hosts and seeds over budget;
   - detection delay for sequential rules.
2. **Detection plotted against realised false escalations**, with one point per nominal budget, calibrated on the calibration split only.
3. **HCOUNT against P10, CUSUM-H, EWMA-H and eCUSUM-H** at B = 1, on the same grid.

No threshold, budget, rule or parameter is chosen with evaluation data.

## 6. Withdrawn analysis

The Phase 10 "matched realised false-escalation" diagnostic (`tradeoff_phase10.py`) set its thresholds on benign_test. It is withdrawn from the manuscript. Its files stay in the repository, marked as withdrawn, so that the history is complete.

## 7. Deviations

None. Every setting ran as specified: 10 seeds each, 40 runs. The run logs are in `logs_10b/`.

## 8. Outcome (added after the runs; computed by `analyze_phase10b.py`)

The table gives, for each setting, the result at B = 1 and F = 1000. All false-escalation rates are realised per host-week.

| Setting | HCOUNT > EXIST (Holm p < 0.05) | (a) | HCOUNT mean rate | (b) | EXIST mean rate | HCOUNT: seeds with worst host over budget | H1 |
|---|---|---|---|---|---|---|---|
| MAIN | 5/6 | met | W50 0.27, W100 0.22, W200 0.18 | met | W50 1.76, W100 0.94, W200 0.53 | W50 9/10, W100 6/10, W200 5/10 | **supported** |
| SWAP | 2/6 | not met | W50 9.04, W100 8.48, W200 8.08 | not met | W50 4.23, W100 7.37, W200 6.91 | W50 10/10, W100 10/10, W200 10/10 | **not supported** |
| DEVICE | 0/6 | not met | W50 5.51, W100 5.44, W200 6.60 | not met | W50 3.75, W100 3.80, W200 4.79 | W50 9/10, W100 8/10, W200 7/10 | **not supported** |
| DEDUP | 2/6 | not met | W50 0.27, W100 0.45, W200 1.64 | not met | W50 0.39, W100 0.49, W200 0.83 | W50 5/10, W100 5/10, W200 6/10 | **not supported** |

**Overall result (pre-specified rule): not reproduced.** H1 is supported in S1 MAIN. It is supported in 0 of the 3 replications (S2–S4), and the protocol required 2.

- **SWAP and DEVICE:** every rule, the existing counter included, exceeded the budget at B = 1, by a factor of about 3 to 12 (2.9–11.9 false escalations per host-week, depending on rule and W). Calibration on one benign split does not control false escalations on the other at host level.
- **DEDUP:** the budgets were roughly met. HCOUNT beat EXIST at only 2 of 6 points, and HCOUNT exceeded the budget at W = 200.
