# Feasibility: per-host accumulation of UNCERTAIN evidence (exploratory, 2026-11-05)

**Question.** When the detector says UNCERTAIN, what should happen next? We test one answer: keep a counter per source host and escalate when suspicion accumulates.

**Status.**
- The design of the rules is in the docstring of `host_accumulation.py`, written before any window-level result was seen.
- Only cached v5.2 AE scores are used (`local_run_v52`, 10 seeds); there is no retraining.
- The mixed-window sensitivity (`host_accumulation_mixed.py`) was added *after* the pure-window results.

**Setup.**
- **Window:** W flows from one `src_ip` and one traffic class. The flows are drawn at random, because version B has no timestamps. `src_ip` is used only as a grouping key, never as a model feature.
- **Counter:** K is the number of flows in the window with p ≤ α + β = 0.05, i.e. the ANOMALY plus UNCERTAIN flows. The counter is a single integer per host, so it is cheap enough for TinyML.
- **R-cal threshold:** k_cal is a split-conformal threshold on benign_val windows, with a window-level budget of 1%. **R-bin:** a binomial threshold that assumes independent flows.
- **Data:** every raw row keeps the p-value of its model vector, so repeated flows stay in. 110,023 rows match a used split: benign_val, benign_test, dev_test and heldout_test.

## Result 1: pure windows (10-seed mean, R-cal)

| W | k_cal | Benign windows escalated | Held-out macro, per flow (ANOMALY) | Held-out macro, per window | Known macro, per window |
|---|---|---|---|---|---|
| 5 | 3.7 | 0.46% | 9.8% | 70.1% | 66.9% |
| 10 | 5.3 | 0.71% | 9.8% | 80.9% | 69.6% |
| 20 | 6.1 | 1.29% | 9.8% | 96.4% | 79.4% |
| 50 | 10.1 | 1.17% | 9.8% | 99.2% | 88.4% |

Per held-out family at W = 20, the per-flow ANOMALY rate becomes the per-window escalation rate as follows:
- ransomware: 2.3% → **100%**;
- xss: 21.9% → 100%;
- mitm: 5.1% → 89.2%.

The per-flow rates here are row-weighted, so they differ from the per-vector E3 rates.

## Result 2: hosts that mix attack and benign flows (W = 20, R-cal, 500 windows per seed and family)

| Share of attack flows ρ | Held-out (mean ± SD over seeds) | Known |
|---|---|---|
| 0.10 | 0.4% | 0.4% |
| 0.25 | 22.8% ± 18.9% | 25.2% |
| 0.50 | 76.5% ± 5.7% | 68.5% |
| 1.00 | 96.8% | 79.1% |

Injection and password stay hard even in pure windows (13% and 61%), because their flows look benign: their p-values are not small.

## Result 3: the cost is concentrated on rare benign hosts

- **Pooled rate.** The pooled benign escalation is near the 1% budget: 0.5–1.3% with R-cal, and 0.8–1.6% with R-bin. For W ≥ 20 it is slightly above budget, so the independence assumption behind R-bin is too optimistic.
- **Concentration.** The false escalations are not spread out. They fall on a few rare or unusual hosts, which are escalated almost every time:
  - 192.168.1.6: 90% of its windows at W = 20;
  - an IPv6 host: 100% at W = 5;
  - 192.168.1.195: 7.9% of its 53 windows at W = 20.
- **Why.** The window-level guarantee is *marginal over windows, not per host*. A benign host whose normal behaviour is unusual becomes a persistent false alarm.

## Result 4: is the UNCERTAIN level needed? (ablation, computed after the main results)

This compares the same rule, counting only ANOMALY flows (p ≤ 0.01), with its own k_cal. It uses 10 seeds and W = 20.

| Counter | Benign escalated | Held-out macro | ransomware | xss | mitm | Known macro |
|---|---|---|---|---|---|---|
| ANOMALY only | 0.2% | 30.5% | 3.2% | 77.9% | 10.2% | 30.4% |
| ANOMALY + UNCERTAIN | 1.3% | 96.4% | 100% | 100% | 89.2% | 79.4% |

The two counters are not matched on benign rate, because the ANOMALY-only counter is discrete and sits under budget. Even so, the gap (ransomware 3% vs 100%) is far too large to be explained by that. **The weak-evidence level is what makes accumulation work.** This gives the three-way decision a concrete purpose beyond relabelling.

**Prior art.**
- Per-host sequential testing is old: TRW (Jung, Paxson, Berger and Balakrishnan, IEEE S&P 2004) and CUMAD (AE + SPRT).
- The new part here is narrower: thresholds calibrated with a stated guarantee, for a benign-only detector on held-out families, plus the per-host validity gap.

## Reading

1. **Accumulation works.** It turns the deferred mass into detections when a host's traffic is mostly malicious: ransomware goes from about 1% to 100%. It does almost nothing when attack flows are under about 25% of a host's traffic.
2. **The real open problem is per-host validity.** A per-host guarantee needs per-host (per-client) calibration. That links directly to the planned FL phase (C4: global vs per-client calibration).
3. **Limits:**
   - there is no time order (version B), so these windows are not true time windows;
   - the lab attackers use dedicated IPs;
   - this is a single split;
   - the k_cal values are coarse, because there are only 55–653 benign_val windows.

Files: `local_run_v52/experiments/host_accumulation_{summary,windows,mixed}.csv`.
