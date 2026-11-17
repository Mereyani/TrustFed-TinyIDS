// Phase 10b: confirmatory re-test of host-conditional calibration (Sections 5.7 and 6.13).
// Every number comes from p10b_values.json (phase10/make_p10b_values.py, which reads phase10/results_10b/analysis/).
const V10B = JSON.parse(fs.readFileSync(path.join(EN_DIR, "p10b_values.json"), "utf8").replace(/\bNaN\b/g, "null"));
const VB = V10B.verdict.verdict_per_setting;
const SETS = ["MAIN", "SWAP", "DEVICE", "DEDUP"];
const SETLAB = { MAIN: "MAIN", SWAP: "SWAP", DEVICE: "DEVICE", DEDUP: "DEDUP" };
const RULELAB = { EXIST: "count [pooled] (existing)", HCOUNT: "count [host-cond.]", P10: "LR e-value window [host-cond.] (P10)",
  "CUSUM-P": "Bernoulli CUSUM [pooled]", "CUSUM-H": "Bernoulli CUSUM [host-cond.]", "eCUSUM-H": "e-CUSUM [host-cond.]",
  "EWMA-P": "EWMA (flag) [pooled]", "EWMA-H": "EWMA (flag) [host-cond.]" };
const pb = (s, W, rho) => V10B.primary_HCOUNT_vs_EXIST.find((r) => r.setting === s && r.W === W && near(r.rho, rho));
const ab10 = (s, rule, B = 1.0, F = 1000) => V10B.all_rules_by_budget.find((r) => r.setting === s && r.rule === rule && near(r.B, B) && r.F === F);
const sb = (s, b, W, rho) => V10B.secondary_HCOUNT_vs_rules.find((r) => r.setting === s && r.B_rule === b && r.W === W && near(r.rho, rho));
const g10 = (o, k) => o[k];
const dpt = (v) => { const t = pt(v); return t === "-0.0" ? "0.0" : t; };

function secPhase10bSetup(C, num) {
  C.push(H2(`${num} Phase 10b: confirmatory protocol`));
  C.push(P("The host-conditional counter of Section 6.12.4 was identified after the Phase 10 test results had been seen. Phase 10b tests it again with every rule frozen, in settings where the conclusion could fail. The protocol, including the success criteria, was written before any Phase 10b run and is archived with the code. Eight rules were compared: the existing counter (pooled), the host-conditional counter, P10, a Bernoulli CUSUM and an EWMA chart on the flag p ≤ α + β (each with pooled and host-conditional p-values), and the host-conditional e-CUSUM. Their definitions, ρ₀ = 0.01 and all simulation constants are those of Phase 10. Thresholds were calibrated on the calibration units only, for nominal budgets B ∈ {0.5, 1, 2} false escalations per host-week at F = 1000 and B = 1 at F = 5000, with W ∈ {50, 100, 200}, ρ ∈ {0.05, 0.10, 0.25}, ten seeds and new random streams. No threshold was set with evaluation data."));
  C.push(...table(["Setting", "Detector", "Calibration units", "Evaluation benign units", "What differs from Phase 10"], [
    ["MAIN", "53-feature AE", "benign_val rows", "benign_test rows", "nothing but new random streams (a re-estimation, not a replication)"],
    ["SWAP", "53-feature AE", "benign_test rows", "benign_val rows", "roles of the two benign splits reversed"],
    ["DEVICE", "21-feature device AE (separately trained)", "half A of the benign_test vectors", "half B of the benign_test vectors", "independent detector and feature set; the likelihood ratio is fitted on half of the dev_test vectors and known-family detection uses the other half"],
    ["DEDUP", "53-feature AE", "distinct benign_val vectors", "distinct benign_test vectors", "one unit per distinct vector, removing the repeated rows"],
  ], [1200, 1900, 1900, 1900, 2738], "Phase 10b settings. None is a second dataset or a temporal split: TON_IoT version B has no timestamps, and no second dataset with host identifiers was available without new data collection and retraining.", { key: "p10bset", leftAll: true }));
  C.push(P("For DEVICE, the row-to-host map of the device model was rebuilt locally with the saved preprocessing objects; applied to the 53-feature model, the same procedure reproduced the stored map exactly. **Primary hypothesis (per setting).** At B = 1 and F = 1000 the host-conditional counter detects more unseen-family sparse attacks than the existing counter (W ∈ {50, 100, 200} × ρ ∈ {0.05, 0.10}; paired two-sided Wilcoxon tests over seeds, Holm-corrected within the setting). A setting supports the hypothesis if (a) at least 4 of the 6 comparisons are significant in favour of the host-conditional counter and (b) its seed-mean realised false-escalation rate on the evaluation hosts is within the budget for every W. The advantage is called **reproducible** if the hypothesis is supported in MAIN and in at least two of SWAP–DEDUP. Worst-host behaviour is reported for every rule."));
}

function secPhase10bResults(C) {
  const S = "6.13";
  C.push(H2(`${S} Phase 10b: is the advantage of host-conditional calibration reproducible?`));
  const nrep = V10B.verdict.replications_supported;
  C.push(P(`**Outcome.** The pre-specified criterion was met in MAIN and in ${nrep} of the three replications, so **the advantage of the host-conditional counter was not reproduced** (${tabRef("p10bverdict")}). The result in MAIN confirms, with new random streams, what Phase 10 found on the original split. In SWAP and DEVICE no rule, including the existing counter, stayed near the budget, and in DEDUP the host-conditional counter was significantly better at only ${VB.DEDUP.significant_HCOUNT_better} of 6 points.`));
  const vrows = SETS.map((s) => { const v = VB[s];
    return [SETLAB[s], `${v.significant_HCOUNT_better}/6`, ["50", "100", "200"].map((w) => f2(v.HCOUNT_fe_mean_by_W[w])).join(" / "),
      ["50", "100", "200"].map((w) => f2(v.EXIST_fe_mean_by_W[w])).join(" / "),
      ["50", "100", "200"].map((w) => `${v.HCOUNT_seeds_worst_host_over_budget_by_W[w]}`).join(" / "), v.supported ? "supported" : "not supported"]; });
  C.push(...table(["Setting", "Significant (of 6)", "Host-cond. counter: false esc./wk (W 50 / 100 / 200)", "Existing counter: false esc./wk (W 50 / 100 / 200)", "Host-cond.: seeds with worst host > B (W 50 / 100 / 200)", "Primary hypothesis"], vrows,
    [1300, 1100, 2000, 2000, 2000, 1238],
    "Phase 10b primary hypothesis at B = 1 false escalation per host-week, F = 1000: host-conditional counter versus existing counter, unseen families, 10 seeds. False escalations are realised on the evaluation hosts (traffic-weighted mean over hosts, mean over seeds).",
    { key: "p10bverdict" }));
  const prow = [];
  for (const s of SETS) for (const rho of [0.05, 0.10]) for (const W of [50, 100, 200]) { const r = pb(s, W, rho);
    prow.push([SETLAB[s], W, nf(rho, 2), pc(r.A_mean), pc(r.B_mean), dpt(r.diff), `${r.seeds_A_better}/10`, pvh(r.p_holm)]); }
  C.push(...table(["Setting", "W", "ρ", "Host-cond. counter", "Existing counter", "Difference", "Seeds better", "p (Holm)"], prow,
    [1500, 700, 700, 1500, 1500, 1200, 1200, 1338],
    "Phase 10b primary comparisons: unseen-family detection at the calibrated thresholds (B = 1, F = 1000). Differences in percentage points; Holm correction within each setting. In SWAP and DEVICE both rules exceeded the budget (previous table), so their detection rates are not comparable at equal cost.",
    { key: "p10bprim" }));

  C.push(H3(`${S}.1 All rules under the same nominal budget`));
  const keys = ["EXIST", "HCOUNT", "P10", "CUSUM-P", "CUSUM-H", "eCUSUM-H", "EWMA-P", "EWMA-H"];
  const arows = [];
  for (const s of SETS) for (const k of keys) { const r = ab10(s, k);
    arows.push([SETLAB[s], RULELAB[k], pc(g10(r, "unseen_W200_r0.05")), pc(g10(r, "unseen_W200_r0.1")), pc(g10(r, "unseen_W50_r0.1")),
      f2(g10(r, "fe_mean_W200")), nf(g10(r, "fe_worst_mean_W200"), 1), `${g10(r, "seeds_mean_over_W200")}/10`, `${g10(r, "seeds_worst_over_W200")}/10`]); }
  C.push(...table(["Setting", "Rule [reference]", "W200 ρ.05", "W200 ρ.10", "W50 ρ.10", "False esc./wk (mean)", "Worst host /wk", "Seeds mean > B", "Seeds worst > B"], arows,
    [1050, 2700, 760, 760, 760, 950, 900, 880, 878],
    "All Phase 10b rules at the same nominal budget B = 1 per host-week (F = 1000), calibrated on calibration units only: unseen-family detection, realised false escalations on the evaluation hosts at W = 200 (sequential rules other than EWMA have one threshold for all W), and worst-host behaviour (mean of 10 seeds).",
    { key: "p10ball", note: "Results for B = 0.5, 2 and for F = 5000, known-family detection and detection delays are in the repository." }));
  const m = (k) => ab10("MAIN", k), d = (k) => ab10("DEDUP", k);
  C.push(P(`Comparisons are meaningful only where the rules stayed close to the budget, that is in MAIN and DEDUP. In MAIN the host-conditional counter detected ${pc(m("HCOUNT")["unseen_W200_r0.05"])} and ${pc(m("HCOUNT")["unseen_W200_r0.1"])} of unseen-family windows at W = 200 (ρ = 0.05 and 0.10) with a mean of ${f2(m("HCOUNT").fe_mean_W200)} false escalations per host-week. P10 detected more at ρ = 0.05 (${pc(m("P10")["unseen_W200_r0.05"])}) but again exceeded the budget (${f2(m("P10").fe_mean_W200)}), and the sequential rules detected less (Bernoulli CUSUM ${pc(m("CUSUM-H")["unseen_W200_r0.05"])}, EWMA ${pc(m("EWMA-H")["unseen_W200_r0.05"])}, e-CUSUM ${pc(m("eCUSUM-H")["unseen_W200_r0.05"])}). In DEDUP every rule stayed near or below the budget on average except the host-conditional counter at W = 200 (${f2(d("HCOUNT").fe_mean_W200)}); there, the host-conditional counter detected ${pc(d("HCOUNT")["unseen_W200_r0.05"])} at ρ = 0.05 against ${pc(d("EXIST")["unseen_W200_r0.05"])} for the existing counter and ${pc(d("P10")["unseen_W200_r0.05"])} for P10, but this difference was not significant after Holm correction. **Worst-host control failed for almost every rule:** even where the mean was within budget, the worst evaluation host exceeded the budget in at least half of the seeds for every rule in every setting, with two exceptions: the existing counter in MAIN (${ab10("MAIN", "EXIST").seeds_worst_over_W200} of 10 seeds) and the pooled EWMA chart in SWAP (${ab10("SWAP", "EWMA-P").seeds_worst_over_W200} of 10 seeds, while its mean exceeded the budget).`));
  C.push(...figure("p10b_budget_curves.png", "Phase 10b: unseen-family detection against realised benign false escalations per host-week at W = 200 for ρ = 0.05 (top) and 0.10 (bottom). Each point is a nominal budget (0.5, 1, 2 per host-week) calibrated on the calibration units only; the dotted line marks one false escalation per host-week (F = 1000, mean of 10 seeds). In SWAP and DEVICE every rule lies far to the right of the budget.", 6.8, { key: "p10bfig" }));

  C.push(H3(`${S}.2 Why the replications fail`));
  C.push(P(`The failures share one mechanism: **host-level false-escalation budgets calibrated on one set of benign units did not transfer to another.** In SWAP and DEVICE, both rules exceeded the budget by large factors (existing counter ${f2(VB.SWAP.EXIST_fe_mean_by_W["200"])} and ${f2(VB.DEVICE.EXIST_fe_mean_by_W["200"])} false escalations per host-week at W = 200; host-conditional counter ${f2(VB.SWAP.HCOUNT_fe_mean_by_W["200"])} and ${f2(VB.DEVICE.HCOUNT_fe_mean_by_W["200"])}). The excess came from one to three large hosts: H2 in SWAP, H1 and H4 (and H2) in DEVICE, and H1 and H2 in DEDUP (the hosts of Section 6.12.1). At W = 200 only 4 evaluation hosts remained in SWAP and DEVICE, 6 in DEDUP and 10 in MAIN, so a single host whose benign behaviour differs between the two sets of units dominates the traffic-weighted rate. DEVICE is the clearest case: its two halves come from the same split and differ only in which distinct vectors (each with all its repeated rows) fall on each side, yet the budget failed for both counters by a factor of about four to seven, and for the other rules by up to about twelve. Removing the repeated rows (DEDUP) brought most rules back near the budget, which supports the explanation that row multiplicity and the de-duplicated split drive the transfer failure, but it also removed most of the host-conditional counter's advantage. The host-conditional reference does not address this mechanism: it adapts each host to its own calibration units, and when those units are not representative of the host's later traffic it can make the host's threshold less conservative, not more.`));
  C.push(P(`**Conclusion of Phase 10b.** On the split on which it was discovered, the host-conditional counter gives a large and repeatable gain at the mean budget. Across the three replications available here it neither kept the budget nor beat the existing counter reliably. Host-conditional calibration therefore does **not** have an established reproducible advantage under realistic false-escalation constraints; establishing one requires data in which each host's calibration period precedes and represents its monitored period, which TON_IoT version B cannot provide.`));
}
