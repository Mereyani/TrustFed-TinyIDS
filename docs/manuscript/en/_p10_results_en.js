// Phase 10 results (subsection 6.12 of the manuscript). All numbers come from _p10_values_en.js accessors.
function secPhase10Results(C) {
  const S = "6.12";
  C.push(H2(`${S} Phase 10: host-level evidence accumulation under sparse attacks`));
  C.push(P("All results in this subsection come from the Phase 10 simulation of Section 5.6. Unless stated otherwise they refer to F = 1000 flows per host per day and to the unseen families (ransomware, xss, mitm), averaged over the ten seeds. Section 6.4 reported the existing counter under the original sparse-attack protocol. The numbers here use the Phase 10 protocol, in which the benign part of an attacked window comes from one benign host rather than from the pooled benign traffic, so they differ from Section 6.4 (for example ${pc(d10(KEY_EXIST, 200, 0.10).mean)} instead of ${pc(f5(200, 0.10).pencere_tespit_mean)} for the existing counter at W = 200, ρ = 0.10)."));

  // ---------------------------------------------------------------- heterogeneity
  C.push(H3(`${S}.1 Benign hosts are not exchangeable with the pooled calibration set`));
  const h1 = het10("H1", "benign_test"), h2v = het10("H2", "benign_val"), h2t = het10("H2", "benign_test"),
    h4v = het10("H4", "benign_val"), h4t = het10("H4", "benign_test");
  C.push(P(`${figRef("p10het")} shows, for every benign host with at least 100 flows, the share of its benign flows that the pooled conformal rule places in the UNCERTAIN or ANOMALY region (p ≤ α + β). Most hosts lie far below the nominal 5%; the host with the most traffic (H1) averages ${pc(h1.f05_mean)} on benign_test. One host (H2) averages ${pc(h2v.f05_mean)} on benign_val and ${pc(h2t.f05_mean)} on benign_test, with one seed reaching ${pc(h2t.f05_max)}. Another (H4) has ${pc(h4v.f01_mean)} of its benign_val flows at p ≤ α but ${pc(h4t.f01_mean)} of its benign_test flows. The pooled guarantee is marginal over hosts, so it does not hold host by host. A host-level threshold calibrated on pooled benign traffic is set by the noisiest hosts, and the share of a host's flows in the low-p region also differs between benign_val and benign_test. TON_IoT was de-duplicated before splitting, so each distinct flow vector lies in one split only, together with all its repeated rows; a host whose rows concentrate on a few vectors can therefore look different in the two splits. This second effect limits how well any benign_val calibration can transfer to benign_test at host level.`));
  C.push(...figure("p10_fig_host_heterogeneity.png", "Per-host share of benign flows with pooled conformal p ≤ α + β (UNCERTAIN or ANOMALY), benign_val and benign_test, one dot per seed. Hosts with at least 100 benign_test flows, labelled H1–H13 by traffic. The dotted line marks the nominal 5%.", 6.5, { key: "p10het" }));

  // ---------------------------------------------------------------- validation
  C.push(H3(`${S}.2 Selection on validation data`));
  const sel = V10.selection.selected, vb = val10("host", "W_HC", 0.01), ve = val10("pooled", "W_COUNT_AU", 0.01),
    vh = val10("host", "W_COUNT_AU", 0.01);
  const candRows = V10.validation.filter((r) => ["W_EVID", "E_CUSUM", "E_SR", "E_CUSUM_LEAKY", "E_SR_ADAPT"].includes(r.method))
    .sort((a, b) => b.mean - a.mean);
  const bestOf = (ref, m) => candRows.filter((r) => r.ref === ref && r.method === m)[0];
  const vrows = [];
  for (const ref of ["host", "pooled"]) for (const m of ["W_EVID", "E_CUSUM", "E_SR", "E_CUSUM_LEAKY", "E_SR_ADAPT"]) {
    const r = bestOf(ref, m); if (r) vrows.push([`${ML10[m]} [${RL10[ref]}]`, nf(r.rho0, 2), `${pc(r.mean)} ± ${pt(r.std)}`, f2(r.val_fe_week_mean), "candidate"]);
  }
  for (const [ref, m] of [["pooled", "W_COUNT_AU"], ["host", "W_COUNT_AU"], ["host", "W_HC"], ["pooled", "BCUSUM"], ["host", "BCUSUM"]]) {
    const rs = V10.validation.filter((r) => r.ref === ref && r.method === m).sort((a, b) => b.mean - a.mean)[0];
    vrows.push([`${ML10[m]} [${RL10[ref]}]`, ["W_COUNT_AU", "W_HC"].includes(m) ? "–" : nf(rs.rho0, 2), `${pc(rs.mean)} ± ${pt(rs.std)}`, f2(rs.val_fe_week_mean), "baseline"]);
  }
  C.push(P(`The pre-specified rule selected the **host-conditional LR e-value window with ρ₀ = ${nf(sel.rho0, 2)}** (called P10 below; criterion ${pc(sel.criterion_mean)} ± ${pt(sel.criterion_sd)}). ${tabRef("p10val")} lists the best ρ₀ of every candidate together with the main baselines. Two observations were already visible on validation data. First, every candidate with the host-conditional reference scored far above every candidate with the pooled reference. Second, the strongest configuration overall was not a candidate but a baseline: Higher Criticism with the host-conditional reference (${pc(vb.mean)}). As the protocol requires, it was not selected, and it is reported as a secondary comparison. The existing counter scored ${pc(ve.mean)} with the pooled reference and ${pc(vh.mean)} with the host-conditional one.`));
  C.push(...table(["Configuration [reference]", "ρ₀", "Validation criterion", "Validation false esc./week", "Role"], vrows,
    [3400, 900, 2100, 1800, 1438],
    "Validation-stage selection (benign_val streams and known-family dev_val attacks; held-out families unused). Criterion: mean known-family detection at ρ ∈ {0.05, 0.10} over W ∈ {20, 50, 100, 200}, F = 1000, mean ± sd over 10 seeds. For each rule the best ρ₀ is shown.",
    { key: "p10val", note: "The selection constraint was a validation false-escalation rate ≤ 1 per host-week (unrounded). Several rows shown exceed it slightly, including the host-conditional e-CUSUM, e-SR, leaky e-CUSUM and adaptive e-SR at the ρ₀ displayed, and were therefore ineligible; no host-conditional e-SR or adaptive e-SR configuration met the constraint at any ρ₀." }));

  // ---------------------------------------------------------------- test: detection at calibrated thresholds
  C.push(H3(`${S}.3 Test stage: detection and false escalations at the calibrated thresholds`));
  const keys = [KEY_EXIST, "pooled|W_EVID", "pooled|E_CUSUM", KEY_HCOUNT, KEY_P10, "host|W_TPM", "host|W_HC", "host|BCUSUM",
    "host|EWMA_FLAG", "host|E_CUSUM", "host|E_SR", "host|E_SR_ADAPT", "host|E_SR_TH"];
  const drows = keys.map((k) => [lab10(k) + (k === KEY_P10 ? " (P10)" : k === KEY_EXIST ? " (existing)" : ""),
    pc(d10(k, 50, 0.05).mean), pc(d10(k, 50, 0.10).mean), pc(d10(k, 50, 0.25).mean),
    pc(d10(k, 200, 0.05).mean), pc(d10(k, 200, 0.10).mean), pc(d10(k, 200, 0.25).mean),
    f2(cW(k, 200).fe_mean), nf(cW(k, 200).worst_mean, 1), `${cW(k, 200).seeds_mean_over}/10`]);
  C.push(...table(["Rule [reference]", "W50 ρ.05", "W50 ρ.10", "W50 ρ.25", "W200 ρ.05", "W200 ρ.10", "W200 ρ.25",
    "False esc./wk (mean)", "Worst host /wk", "Seeds over budget"], drows,
    [2700, 700, 700, 700, 760, 760, 760, 900, 830, 828],
    "Test stage: host-level detection of unseen-family sparse attacks and benign_test false escalations, with every threshold calibrated on benign_val for 1 false escalation per host-week except the theory-threshold row, which uses log(7F/B) without calibration (F = 1000; mean of 10 seeds; simulation).",
    { key: "p10test", note: "False-escalation columns refer to W = 200 for window and W-dependent rules and to the single threshold of the other sequential rules. Worst host: mean over seeds of the largest per-host weekly rate. Seeds over budget: seeds whose traffic-weighted mean exceeds 1. Full tables for all 18 rules, both references, both traffic levels and known families are in the repository." }));
  const pr = V10.primary_comparison, nsig = pr.filter((r) => r.p_holm < 0.05).length;
  const p200a = prim10(200, 0.05), p200b = prim10(200, 0.10), p20a = prim10(20, 0.05);
  C.push(P(`**Primary comparison.** At the calibrated thresholds P10 detected more unseen-family sparse attacks than the existing counter at every one of the eight (W, ρ) points, and the difference was significant after Holm correction at ${nsig} of 8 (${tabRef("p10prim")}). At W = 200 the means were ${pc(p200a.P10_mean)} versus ${pc(p200a.existing_mean)} at ρ = 0.05 and ${pc(p200b.P10_mean)} versus ${pc(p200b.existing_mean)} at ρ = 0.10; the smallest window gave little to either rule (${pc(p20a.P10_mean)} versus ${pc(p20a.existing_mean)} at W = 20, ρ = 0.05).`));
  const cp = (W) => c10(KEY_P10, W), ce = (W) => c10(KEY_EXIST, W), ch = (W) => c10(KEY_HCOUNT, W);
  C.push(P(`**The budget was not met.** On benign_test hosts P10 escalated benign hosts ${f2(cp(50).fe_mean)}–${f2(Math.max(cp(100).fe_mean, cp(200).fe_mean))} times per host-week on average for W ≥ 50, above the budget of 1, with ${cp(200).seeds_mean_over} of 10 seeds over budget at W = 200 and a worst host at ${nf(cp(200).worst_mean, 1)} per week (mean over seeds). The worst host was H4 in 9 of 10 seeds; its benign_test flows reach p ≤ α more often than its benign_val reference (Section ${S}.1). At F = 5000 the overshoot was larger (${f2(c10(KEY_P10, 200, 5000).fe_mean)} per host-week at W = 200). Under the pre-specified protocol, a rule that exceeds the budget on benign_test cannot be credited with a detection gain at equal cost, so **the primary hypothesis is not supported**: the detection advantage in ${tabRef("p10prim")} is partly bought with extra false escalations. The existing counter was not exactly within budget either: its traffic-weighted mean was ${f2(ce(200).fe_mean)} per week at W = 200 but ${f2(ce(20).fe_mean)} at W = 20, where one benign host was escalated in every seed (worst host ${nf(ce(20).worst_mean, 0)} per week), the failure already reported in Section 6.4.`));
  C.push(...table(["W", "ρ", "P10", "Existing counter", "Difference", "95% CI", "Seeds P10 better", "p (Wilcoxon)", "p (Holm)"],
    pr.map((r) => [r.W, nf(r.rho, 2), pc(r.P10_mean), pc(r.existing_mean), pt(r.diff_mean), `[${pt(r.ci_low)}, ${pt(r.ci_high)}]`,
      `${r.seeds_P10_better}/10`, pvh(r.p_wilcoxon), pvh(r.p_holm)]),
    [500, 600, 1000, 1300, 1050, 1500, 1200, 1250, 1238],
    "Primary comparison (pre-specified): unseen-family detection of P10 versus the existing counter at the calibrated thresholds, F = 1000. Differences in percentage points; 95% percentile-bootstrap CI over seeds; two-sided Wilcoxon signed-rank tests, Holm-corrected over the 8 comparisons.",
    { key: "p10prim", note: "Both rules exceeded the false-escalation budget on benign_test in some settings (Table " + tabNum("p10test") + "); the comparison is therefore not at equal realised cost." }));

  // ---------------------------------------------------------------- what drives the gain
  C.push(H3(`${S}.4 What drives the gain: the reference, not the accumulator`));
  const e200a = ex10(KEY_HCOUNT, KEY_EXIST, 200, 0.05, false), e200b = ex10(KEY_HCOUNT, KEY_EXIST, 200, 0.10, false),
    e50b = ex10(KEY_HCOUNT, KEY_EXIST, 50, 0.10, false);
  const nex = V10.exploratory_comparisons.filter((x) => x.analysis.startsWith("EXPLORATORY") && x.p_holm < 0.05).length;
  C.push(P(`Two further analyses were added after the test stage; they are labelled exploratory and were not part of the protocol. The first applies the host-conditional reference to the **existing count rule**, which needs no likelihood ratio and no attack data. At the benign_val-calibrated thresholds it raised unseen-family detection from ${pc(e200a.B_mean)} to ${pc(e200a.A_mean)} at W = 200, ρ = 0.05, from ${pc(e200b.B_mean)} to ${pc(e200b.A_mean)} at W = 200, ρ = 0.10 and from ${pc(e50b.B_mean)} to ${pc(e50b.A_mean)} at W = 50, ρ = 0.10 (significant after Holm correction at ${nex} of 8 points). It did so while staying within the mean budget on benign_test (${f2(ch(200).fe_mean)} and ${f2(ch(50).fe_mean)} false escalations per host-week at W = 200 and W = 50, no seed above budget for W ≥ 50), although the worst host still exceeded the budget in ${ch(200).seeds_worst_over} of 10 seeds at W = 200 (mean ${nf(ch(200).worst_mean, 2)} per week).`));
  const mfk = [KEY_EXIST, KEY_HCOUNT, "pooled|W_EVID", KEY_P10, "host|W_TPM", "host|W_HC", "host|BCUSUM", "host|E_CUSUM", "host|E_SR_ADAPT"];
  const mrows = mfk.map((k) => [lab10(k), pc(mf10(k, 50, 0.05).mean), pc(mf10(k, 50, 0.10).mean), pc(mf10(k, 200, 0.05).mean),
    pc(mf10(k, 200, 0.10).mean), pc(mf10(k, 200, 0.25).mean), f2(mf10(k, 200, 0.10).realised_fe)]);
  C.push(P(`The second analysis removes the confound of unequal realised false-alarm rates. For each rule, the threshold is set **on the benign_test hosts** so that the realised traffic-weighted rate is at most one false escalation per host-week, and detection is measured at that operating point. These thresholds use test data and are not deployable; the analysis only compares the statistics at equal realised cost (${tabRef("p10matched")}, ${figRef("p10trade")}).`));
  C.push(...table(["Rule [reference]", "W50 ρ.05", "W50 ρ.10", "W200 ρ.05", "W200 ρ.10", "W200 ρ.25", "Realised false esc./wk"], mrows,
    [3300, 1000, 1000, 1050, 1050, 1050, 1188],
    "Diagnostic (oracle): unseen-family detection when every threshold is tuned on benign_test so that the realised false-escalation rate is at most 1 per host-week (F = 1000, mean of 10 seeds). Not deployable; used only to compare the statistics at equal realised cost. The last column gives the realised rate at W = 200.",
    { key: "p10matched", note: "Rules with discrete or tied statistics (counts, Higher Criticism, truncated product) reach the budget only approximately, so their realised rate is below 1, which works against them." }));
  const o1 = ex10(KEY_P10, KEY_HCOUNT, 200, 0.05, true), o2 = ex10(KEY_P10, KEY_HCOUNT, 200, 0.10, true),
    o3 = ex10("host|E_CUSUM", KEY_HCOUNT, 200, 0.10, true), o4 = ex10(KEY_HCOUNT, KEY_EXIST, 200, 0.05, true),
    o5 = ex10(KEY_HCOUNT, KEY_EXIST, 50, 0.10, true);
  C.push(P(`At equal realised cost the ranking is clear. For ρ ∈ {0.05, 0.10}, the host-conditional count rule was the best rule at every point with W ≥ 50 except W = 50, ρ = 0.05, where no rule exceeded ${pc(mf10(KEY_P10, 50, 0.05).mean)}: ${pc(o1.B_mean)} at W = 200, ρ = 0.05 and ${pc(o2.B_mean)} at ρ = 0.10. The host-conditional LR e-value window (P10) reached ${pc(o1.A_mean)} and ${pc(o2.A_mean)}, significantly lower (Holm-corrected p = ${pvh(o1.p_holm)} and ${pvh(o2.p_holm)}). e-CUSUM with the same reference reached ${pc(o3.A_mean)} at W = 200, ρ = 0.10. The likelihood-ratio weighting was better only where every rule detected little (W = 20, and W = 50 at ρ = 0.05; significant at W = 20). At ρ = 0.25 and above, several rules, including the pooled counter, were within about one point of the host-conditional counter. Against the existing pooled counter at equal realised cost, the host-conditional reference added ${pt(o4.diff)} percentage points at W = 200, ρ = 0.05 and ${pt(o5.diff)} at W = 50, ρ = 0.10. Higher Criticism, the best rule on validation data, collapsed at equal realised cost on benign_test: its host-conditional version reached only ${pc(mf10("host|W_HC", 200, 0.10).mean)} at W = 200, ρ = 0.10, and with calibrated thresholds it escalated benign hosts ${nf(c10("host|W_HC", 200).fe_mean, 1)} times per week. Statistics that react to a few extreme p-values transfer worst from benign_val to benign_test.`));
  C.push(...figure("p10_fig_tradeoff.png", "Diagnostic trade-off between unseen-family detection and realised false escalations per host-week on benign_test, obtained by sweeping each window rule's threshold on the test hosts (F = 1000, mean of 10 seeds). Solid lines: host-conditional reference; dashed: pooled reference. The dotted line marks the budget.", 6.6, { key: "p10trade" }));
  C.push(...figure("p10_fig_detection_vs_rho.png", "Unseen-family detection versus the attack share ρ for selected rules, with thresholds calibrated on benign_val for one false escalation per host-week (F = 1000, mean of 10 seeds). The realised false-escalation rates of these rules on benign_test differ (Table " + tabNum("p10test") + ").", 6.6, { key: "p10rho" }));

  // ---------------------------------------------------------------- sequential rules
  C.push(H3(`${S}.5 Sequential accumulation, evidence decay and theory thresholds`));
  const dc = dl10("host|E_CUSUM", 200, 0.10), da = dl10("host|E_SR_ADAPT", 200, 0.10), dbc = dl10("host|BCUSUM", 200, 0.10),
    dc50 = dl10("host|E_CUSUM", 50, 0.25);
  const th1 = c10("pooled|E_SR_TH", "all"), th2 = c10("host|E_SR_TH", "all"), th3 = c10("pooled|E_SR_ADAPT_TH", "all");
  C.push(P(`Continuous monitoring did not translate into more detections within the attack window. With the host-conditional reference, e-CUSUM, e-SR, leaky e-CUSUM and adaptive e-SR detected ${pc(d10("host|E_CUSUM", 200, 0.05).mean)}, ${pc(d10("host|E_SR", 200, 0.05).mean)}, ${pc(d10("host|E_CUSUM_LEAKY", 200, 0.05).mean)} and ${pc(d10("host|E_SR_ADAPT", 200, 0.05).mean)} at W = 200, ρ = 0.05, less than P10 (${pc(d10(KEY_P10, 200, 0.05).mean)}) and the host-conditional truncated product (${pc(d10("host|W_TPM", 200, 0.05).mean)}) and close to the host-conditional counter (${pc(d10(KEY_HCOUNT, 200, 0.05).mean)}), and they exceeded the budget on benign_test in ${c10("host|E_CUSUM_LEAKY", 200).seeds_mean_over}–${Math.max(c10("host|E_CUSUM", "all").seeds_mean_over, c10("host|E_SR", "all").seeds_mean_over, c10("host|E_SR_ADAPT", "all").seeds_mean_over)} of 10 seeds (${tabRef("p10test")}). With the pooled reference all of them stayed below 10% at ρ ≤ 0.10. Their single advantage is timing: when they did escalate within a 200-flow window at ρ = 0.10, they did so after a mean of ${nf(dc.delay_mean, 0)} (e-CUSUM), ${nf(da.delay_mean, 0)} (adaptive e-SR) and ${nf(dbc.delay_mean, 0)} (Bernoulli CUSUM) flows, whereas a window rule decides only at flow 200; at W = 50, ρ = 0.25 e-CUSUM escalated after ${nf(dc50.delay_mean, 0)} flows on average. Evidence decay (leaky e-CUSUM) changed little relative to e-CUSUM, and averaging over design shares (adaptive e-SR) performed about as well as the selected single ρ₀.`));
  C.push(P(`The calibration-free e-detector thresholds (log R ≥ log 7F) did not control the budget. With the pooled reference, e-SR escalated benign hosts ${f2(th1.fe_mean)} times per host-week on average (worst host ${nf(th1.worst_mean, 0)}), and adaptive e-SR ${f2(th3.fe_mean)} times. The anytime-valid bound assumes independent, super-uniform p-values for every benign host, and the hosts of Section ${S}.1 violate it. With the host-conditional reference the same threshold was conservative on average (${f2(th2.fe_mean)} per week), but some hosts still exceeded it (worst host ${nf(th2.worst_mean, 1)} on average), and detection fell to ${pc(d10("host|E_SR_TH", 200, 0.10).mean)} at W = 200, ρ = 0.10.`));

  // ---------------------------------------------------------------- families
  C.push(H3(`${S}.6 Per-family results`));
  const fk = [KEY_EXIST, KEY_HCOUNT, KEY_P10, "host|E_CUSUM"];
  const frows = [];
  for (const fm of ["ransomware", "xss", "mitm"]) for (const k of fk)
    frows.push([fm, lab10(k), pc(fam10(k, 200, 0.05, fm).mean), pc(fam10(k, 200, 0.10, fm).mean), pc(fam10(k, 200, 0.25, fm).mean),
      pc(fam10(k, 50, 0.10, fm).mean), pc(fam10(k, 50, 0.25, fm).mean)]);
  C.push(...table(["Family", "Rule [reference]", "W200 ρ.05", "W200 ρ.10", "W200 ρ.25", "W50 ρ.10", "W50 ρ.25"], frows,
    [1200, 3400, 1000, 1000, 1000, 1000, 1038],
    "Detection per held-out family at the calibrated thresholds (F = 1000, mean of 10 seeds). The false-escalation caveats of Table " + tabNum("p10test") + " apply.",
    { key: "p10fam" }));
  C.push(P(`The families differ in where their p-values lie (Section 6.2). MITM is the hardest family: about half of its flows have p > α + β. At W = 200, ρ = 0.05 the host-conditional counter detected ${pc(fam10(KEY_HCOUNT, 200, 0.05, "mitm").mean)} of MITM windows and P10 ${pc(fam10(KEY_P10, 200, 0.05, "mitm").mean)}, against ${pc(fam10(KEY_HCOUNT, 200, 0.05, "ransomware").mean)} and ${pc(fam10(KEY_P10, 200, 0.05, "ransomware").mean)} for ransomware. Ransomware flows fall almost entirely inside the UNCERTAIN band, where the count rule is already efficient. XSS has a large share of flows at p ≤ 0.01, inside the region to which the fitted likelihood ratio gives its largest weight (p ≤ 0.02), whereas the count rule weighs all flags up to p = 0.05 equally (P10 ${pc(fam10(KEY_P10, 200, 0.05, "xss").mean)} versus ${pc(fam10(KEY_HCOUNT, 200, 0.05, "xss").mean)} for the host-conditional counter at W = 200, ρ = 0.05).`));

  // ---------------------------------------------------------------- overhead
  C.push(H3(`${S}.7 Computational and memory cost`));
  const ob = ov10("p-value"), oc20 = ov10("W_COUNT_AU, W=20"), oe200 = ov10("W_EVID, W=200"), oh200 = ov10("W_HC, W=200"),
    ocu = ov10("BCUSUM"), osr = ov10("E_SR_ADAPT");
  C.push(...table(["Rule", "Update time per flow (ns, laptop CPU)", "Per-host state (bytes)", "Lookup table (bytes)"],
    V10.overhead.map((r) => [r.rule.replace("p-value -> bin", "p-value → bin").replace("W_COUNT_AU", "Count p ≤ α+β").replace("W_EVID", "LR e-value window").replace("W_HC", "Higher Criticism").replace("BCUSUM / E_CUSUM", "Bernoulli CUSUM / e-CUSUM").replace("E_SR_ADAPT", "Adaptive e-SR").replace("E_SR", "e-SR").replace("EWMA_FLAG", "EWMA (flag)").replace("W=", "W = "), nf(r.ns_per_flow_this_cpu, 1), r.state_bytes_per_host, r.table_bytes]),
    [3600, 2400, 1800, 1838],
    "Cost of the host-level rules: numba-compiled update time per flow on a laptop CPU (best of 5 runs over 2 million flows; not a microcontroller measurement) and memory in a float32/uint8 C layout.",
    { key: "p10cost", note: `The host-conditional reference adds ${ov10("p-value").host_reference_bytes_per_host} bytes per host for the binned rules (one threshold per bin edge on the pooled p-value). For the count rule it reduces to a single per-host threshold: p′ ≤ α + β holds exactly when p ≤ α + β and p is below a host-specific value fixed by the reference.` }));
  C.push(P(`All binned rules cost a few nanoseconds per flow on the measurement machine (${nf(ocu.ns_per_flow_this_cpu, 1)} ns for e-CUSUM, ${nf(oc20.ns_per_flow_this_cpu, 1)} ns for the counter, plus ${nf(ob.ns_per_flow_this_cpu, 1)} ns to bin the p-value) and need at most a few hundred bytes per host (${oe200.state_bytes_per_host} bytes for the e-value window at W = 200). Higher Criticism needs the W p-values and a sort per window (${nf(oh200.ns_per_flow_this_cpu, 1)} ns per flow, ${oh200.state_bytes_per_host} bytes at W = 200), and adaptive e-SR multiplies the e-SR cost by the number of components (${nf(osr.ns_per_flow_this_cpu, 1)} ns). None of these costs is significant next to the autoencoder inference of Section 6.7; they were not measured on a microcontroller.`));

  // ---------------------------------------------------------------- targets
  C.push(H3(`${S}.8 Research targets`));
  const f5r = (rho) => f5(200, rho);
  const tgt = [
    ["Detection, W = 200, ρ = 0.05", "≥ 20%", pc(f5r(0.05).pencere_tespit_mean), pc(d10(KEY_EXIST, 200, 0.05).mean), pc(d10(KEY_P10, 200, 0.05).mean), pc(d10(KEY_HCOUNT, 200, 0.05).mean)],
    ["Detection, W = 200, ρ = 0.10", "≥ 40%", pc(f5r(0.10).pencere_tespit_mean), pc(d10(KEY_EXIST, 200, 0.10).mean), pc(d10(KEY_P10, 200, 0.10).mean), pc(d10(KEY_HCOUNT, 200, 0.10).mean)],
    ["Detection, W = 200, ρ = 0.25", "maintain or improve", pc(f5r(0.25).pencere_tespit_mean), pc(d10(KEY_EXIST, 200, 0.25).mean), pc(d10(KEY_P10, 200, 0.25).mean), pc(d10(KEY_HCOUNT, 200, 0.25).mean)],
    ["False esc. per host-week, W = 200 (mean)", "≤ 1", nf(cost5(200).normal_haftalik_ort_mean, 2), f2(ce(200).fe_mean), f2(cp(200).fe_mean), f2(ch(200).fe_mean)],
    ["Seeds with worst host over budget, W = 200", "0", "1/10", `${ce(200).seeds_worst_over}/10`, `${cp(200).seeds_worst_over}/10`, `${ch(200).seeds_worst_over}/10`],
  ];
  C.push(...table(["Quantity (unseen families, F = 1000)", "Target", "Existing counter, Sec. 6.4 protocol", "Existing counter, Phase 10 protocol", "P10 (pre-specified)", "Host-conditional counter (exploratory)"], tgt,
    [2700, 1150, 1450, 1450, 1400, 1488],
    "Phase 10 against the research targets stated in the Phase 10 brief, at the benign_val-calibrated thresholds (mean of 10 seeds; simulation).",
    { key: "p10tgt", note: "The worst-host entry of the Section 6.4 protocol counts seeds whose worst host exceeded 1 per week in that run (9 of 10 seeds were within budget at W = 200)." }));
  C.push(P(`The detection targets were met numerically by both P10 and the host-conditional counter. The false-escalation target was not met by P10, and was met by the host-conditional counter only on average, not for every host and seed. The targets are therefore only partly achieved.`));
}
