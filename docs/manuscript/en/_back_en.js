// Discussion (7), Limitations (8), Conclusion (9), declarations and the reference list.
function secDiscussion(C) {
  C.push(H1("7. Discussion"));
  C.push(H2("7.1 The original framework"));
  secDiscussionCore(C);
  C.push(H2("7.2 Host-level evidence accumulation"));
  const ch = c10(KEY_HCOUNT, 200), cp = c10(KEY_P10, 200);
  const mH = ab10("MAIN", "HCOUNT");
  C.push(P("**What improved?** On the split on which the framework was developed, detection of sparse unseen-family attacks improved substantially when each host's flows were evaluated against that host's own benign reference. The gain came mainly from the reference and not from the accumulator. The pre-specified P10 rule detected more but exceeded the budget, while the existing count rule with host-conditional p-values kept the mean budget, and Phase 10b reproduced this with new random streams. There was no evidence that evidence weighting by likelihood-ratio e-values or sequential accumulation (CUSUM, Shiryaev–Roberts, EWMA, evidence decay, adaptive mixtures) improves on window counting at equal cost at the horizons studied: P10 detected more on the original split but only by exceeding the budget, and where the rules stayed near the budget (S4) the differences were not significant. The sequential rules' clear advantage was earlier alarms."));
  C.push(P(`**Is the improvement reliable?** Statistically, on the original split, yes: the host-conditional counter beat the existing counter in 9 or 10 of 10 seeds at W ≥ 100 in Phase 10 and in all 10 seeds at W ≥ 100 in Phase 10b. Across settings, no. When the roles of the benign splits were reversed, or a separately trained detector was calibrated and evaluated on two halves of one split, every rule, including the existing counter, exceeded the budget several-fold, and on de-duplicated streams the gain was significant at only two of six points. Operationally, even on the original split the worst benign host exceeded the budget in about half of the seeds (Phase 10b: ${mH.seeds_worst_over_W200} of 10 at W = 200), detection is measured per window rather than per day, and all streams are simulated. The improvement is therefore not established as reliable under realistic false-escalation constraints.`));
  C.push(P("**Why do host-level budgets not transfer?** A host-level rule is calibrated on a sample of benign traffic and must hold on the host's later traffic. In TON_IoT version B these are two random partitions of de-duplicated vectors: each distinct flow vector, with all its repeated rows, lies on one side only, and a few large hosts account for most of the traffic. A plausible mechanism is that when a frequently repeated vector with a small p-value falls on the evaluation side of a large host, that host's false-escalation rate rises several-fold, and with only 4–10 evaluation hosts at W = 200 one such host dominates the average. Removing the repeated rows (S4) restored the budgets of most rules, which is consistent with this explanation. The host-conditional reference cannot correct the problem: it adapts each host to its own calibration sample, so it inherits whatever makes that sample unrepresentative. In Phase 10 and in S3, the statistics that weight small p-values most (the likelihood ratio, Higher Criticism) transferred worst and coarse counting best; in S2 and S4 the ordering was not consistent (P10 exceeded the budget less than the host-conditional counter), so no general ranking of the statistics by robustness can be drawn."));
  C.push(P("**Relation to theory.** The guarantees used here are marginal and per flow (Propositions 1 and 2). None of them extends to the windows or streams on which the host-level rules decide, because the p-values of a host share the calibration set and the host reference and because hosts are not exchangeable with one another. The empirical failures of the anytime-valid thresholds and of calibration transfer are what this gap looks like in practice. Theory continues to favour CUSUM-type rules for persistent changes with stable, well-modelled pre-change behaviour [@lorden1971procedures,moustakides1986optimal], and conformal martingales can be made more efficient [@bhattacharyya2026optimal]; neither condition held here."));
  C.push(P("**Contribution and relation to trust management.** No new detector is proposed: the host-conditional p-value is a Mondrian conformal construction combined with the maximum of two p-values, and e-CUSUM and e-SR are e-detectors. The defensible contribution is a pre-specified, multi-seed evaluation with a confirmatory re-test. It shows where the guarantees of a calibrated IoT detector stop holding and that host-level false-escalation budgets — the quantity on which a host trust score must rest — did not transfer between benign samples of the same hosts. For trust management this means that a host's trust threshold is only as good as the host's reference: a deployed system would have to build references from earlier traffic of the same host, refresh them, detect changes in benign behaviour and guard them against poisoning by an attacker present during the reference period."));
}

function secLimitations(C) {
  C.push(H1("8. Limitations and Threats to Validity"));
  secLimitationsCore(C);
  C.push(P("Additional limitations specific to Phases 10 and 10b:"));
  C.push(B("**Simulation, not deployment.** TON_IoT version B has no timestamps. Host streams are random orderings of each host's flows drawn with replacement, which removes temporal dependence, bursts, diurnal patterns and the real timing of attacks. Attack windows are synthetic mixtures of attack flows from attack hosts with benign flows of a benign host. All host-level results are therefore simulations."));
  C.push(B("**No second dataset and no temporal split.** The replications of Phase 10b reuse the same dataset (reversed benign splits, a different detector on two halves of one split, de-duplicated units). They can show that a result does not reproduce, but a positive result in them would not have been independent evidence either. A dataset with timestamps and host identifiers, with calibration on earlier and evaluation on later traffic of the same hosts, is required."));
  C.push(B("**Calibration transfer and few hosts.** Host-level budgets calibrated on one benign sample did not hold on another. Only 4–24 benign hosts had enough flows at a given window size, many hosts shared a fallback reference, and the worst-host statistics depend on a few hosts: large hosts (H1, H2, H4) for the window rules and, for several sequential rules, low-traffic hosts that share the fallback reference."));
  C.push(B("**Non-blind design.** The Phase 10 protocol was written after the validation runs had started, and the per-host benign flag rates of benign_val and benign_test (two seeds), the earlier sparse-attack results and the per-family p-value rates had been inspected beforehand; this motivated the host-conditional reference. The host-conditional counter was identified after the Phase 10 test results had been seen; Phase 10b re-tested it with frozen rules. A test-tuned diagnostic used in an earlier version of the analysis has been withdrawn."));
  C.push(B("**Design choices.** The likelihood ratio was fitted on six known families (in S3 on half of the dev_test vectors), so its shape reflects them. The p-value bins, window sizes, budgets and traffic levels were fixed in advance and not varied beyond the stated grids."));
  C.push(B("**Adaptive attackers and cost.** Attackers who shape their traffic to stay below a host's threshold, or who poison its reference, were not modelled. Timing was measured on a laptop CPU with numba-compiled code, not on a microcontroller."));
}

function secConclusion(C) {
  C.push(H1("9. Conclusion and Future Work"));
  C.push(P(`TrustFed-TinyIDS combines a benign-only autoencoder (${fv("aeParams")} parameters) with a two-threshold conformal rule, federated training and INT8 deployment. On TON_IoT with three held-out families and ten seeds it kept the benign ANOMALY rate at ${fv("normalAnomalyRate")}, flagged ${fv("centralUnseenAnomaly")} of unseen-family flows as ANOMALY and missed ${fv("centralUnseenMissed")}. The large initial gap between federated and central training was mostly an artefact of unequal training, but a gap remained under strongly non-IID splits and federated runs stopped at the epoch cap while still improving. Conformal thresholds did not survive every change of condition: they failed after INT8 conversion of the device model, for small non-IID clients under pooled calibration and under corrupted inputs, and had to be recalibrated.`));
  C.push(P("For sparse attacks, host-conditional calibration of the conformal p-values improved simulated host-level detection on the original split within the mean false-escalation budget, whereas there was no evidence that likelihood-ratio evidence or sequential accumulators improve on simple window counting at equal cost. A confirmatory re-test did not reproduce the advantage, because host-level false-escalation budgets calibrated on one benign sample did not hold on another. The defensible conclusion is therefore a qualified one: per-host calibration may be the right lever for sparse attacks, but only if each host's reference is representative of its later traffic, and that condition could not be established with the available data."));
  C.push(P("**Future work.** The following steps are required before the host-level results can support a positive claim:"));
  C.push(B("evaluate on a dataset with timestamps and host identifiers, calibrating each host on earlier and monitoring it on later traffic, and ideally on a second network;"));
  C.push(B("design and pre-register reference maintenance (refresh, drift detection, resistance to poisoning) and report per-host budgets over time;"));
  C.push(B("model adaptive low-rate attackers;"));
  C.push(B("run the federated models to convergence and test further FedProx settings and client-specific layers for non-IID clients;"));
  C.push(B("measure latency, memory and the effect of post-INT8 recalibration on a real microcontroller."));
}

// ------------------------------------------------------------------ declarations
function secDeclarations(C) {
  C.push(H1("Data and Code Availability"));
  C.push(P("The TON_IoT network dataset is available from its authors [@moustafa2021new]; it is not redistributed. Code, notebooks, run configurations, per-seed scores and results, the Phase 10 protocol with its deviation log, and the verified reference list (with the metadata source used to check each entry) are available in the TrustFed-TinyIDS repository (https://github.com/Mereyani/TrustFed-TinyIDS). Phase 10 can be reproduced from the released scores without the dataset."));
  C.push(H1("Conflict of Interest"));
  C.push(P("The author declares no conflict of interest."));
}

// ------------------------------------------------------------------ references
function loadRefs() {
  const txt = fs.readFileSync(path.join(EN_DIR, "..", "..", "phase10", "references", "references_ieee.txt"), "utf8");
  const m = {};
  for (const line of txt.split(/\r?\n/)) { const r = /^\[([^\]]+)\]\s*(.*)$/.exec(line); if (r) m[r[1]] = r[2]; }
  return m;
}
const CITE_ALIAS = { mcmahan2017: "mcmahan2017communication", li2020fedprox: "li2020federated", hsu2019noniid: "hsu2019measuring",
  kairouz2021: "kairouz2021advances", vovk2005alrw: "vovk2005algorithmic", bates2023outliers: "bates2023testing",
  angelopoulos2023: "angelopoulos2023conformal", moustafa2021toniot: "moustafa2021new", alsaedi2020toniot: "alsaedi2020ton",
  liu2008iforest: "liu2008isolation", jacob2018quant: "jacob2018quantization", banbury2021mlperftiny: "banbury2021mlperf",
  holm1979: "holm1979simple", wilcoxon1945: "wilcoxon1945individual", geifman2017: "geifman2017selective", chow1970: "chow1970optimum",
  sommer2010: "sommer2010outside", arp2022: "arp2022dos", vovk2003exchangeability: "vovk2003testing", page1954: "page1954continuous",
  lorden1971: "lorden1971procedures", moustakides1986: "moustakides1986optimal", shiryaev1963: "shiryaev1963optimum",
  roberts1966: "roberts1966comparison", zaykin2002tpm: "zaykin2002truncated", donoho2004hc: "donoho2004higher",
  reynolds1999bernoulli: "reynolds1999cusum", roberts1959ewma: "roberts1959control", lucas1990ewma: "lucas1990exponentially" };
// IEEE style: journal, proceedings and book titles in italics. Returns [before, italic, after].
const BOOK_TITLES = { vovk2005algorithmic: "Algorithmic Learning in a Random World",
  vovk2022algorithmic: "Algorithmic Learning in a Random World",
  tartakovsky2014sequential: "Sequential Analysis: Hypothesis Testing and Changepoint Detection" };
function splitVenue(key, t) {
  if (BOOK_TITLES[key]) {
    const i = t.indexOf(BOOK_TITLES[key]);
    if (i >= 0) return [t.slice(0, i), BOOK_TITLES[key], t.slice(i + BOOK_TITLES[key].length)];
  }
  const q = t.indexOf(",\" ");                       // end of the quoted article title
  if (q < 0) return [t, "", ""];
  let s = q + 3;
  if (t.startsWith("in ", s)) s += 3;
  if (t.startsWith("arXiv", s)) return [t, "", ""];   // preprints: no italic venue
  const rest = t.slice(s + 1);
  const m = /, (vol\.|no\.|pp\.|p\. |Art\. no\.|early access|PMLR|(19|20)\d\d)|\. \[Online\]/.exec(rest);
  const e = m ? s + 1 + m.index : t.length;
  return [t.slice(0, s), t.slice(s, e), t.slice(e)];
}
function secReferences(C) {
  C.push(H1("References"));
  const refs = loadRefs();
  CITE_ORDER.forEach((k, i) => {
    const t = refs[k];
    if (!t) throw new Error(`reference not found in the verified list: ${k}`);
    const [a, v, b] = splitVenue(k, t);
    C.push(new Paragraph({ spacing: { after: 60, line: 252 }, indent: { left: 560, hanging: 560 },
      children: [new TextRun({ text: `[${i + 1}]\t`, size: 19 }), new TextRun({ text: a, size: 19 }),
        new TextRun({ text: v, size: 19, italics: true }), new TextRun({ text: b, size: 19 })] }));
  });
}
