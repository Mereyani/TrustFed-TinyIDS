// Discussion (7), Limitations (8), Conclusion (9), declarations and the reference list.
function secDiscussion(C) {
  C.push(H1("7. Discussion"));
  C.push(H2("7.1 The original framework"));
  secDiscussionCore(C);
  C.push(H2("7.2 Host-level evidence accumulation"));
  const ch = c10(KEY_HCOUNT, 200), cp = c10(KEY_P10, 200);
  C.push(P("**Did Phase 10 improve sparse-attack detection?** Yes in detection, no at the required cost. The pre-specified configuration raised simulated host-level detection of unseen sparse attacks several-fold over the existing counter. On benign_test hosts, however, it produced more false escalations than the budget allowed, so its gain was not obtained at equal cost and the pre-specified hypothesis was not supported. The exploratory analyses suggest why. Once rules are compared at equal realised cost (a test-tuned diagnostic), evidence weighting and sequential accumulation add little over counting flags in a window for W ≥ 50; they helped only in the smallest windows, where every rule detected little. What changes detection is the reference: evaluating each host's flows against that host's own benign history. This removes the dominant source of false escalations under the pooled reference, namely a few benign hosts that place a much larger share of their benign flows in the low-p region than the nominal level. The pooled threshold can then fall to a level at which a handful of attack flows is enough."));
  C.push(P(`**Why did the more sophisticated statistics not help?** The fitted likelihood ratio gives its largest weight to the region p ≤ 0.02, and Higher Criticism reacts to the smallest p-values in a window. These are exactly where the benign_val reference and benign_test traffic of the same host differ most (Section 6.12.1), so these statistics transfer worst from calibration to test. Counting p ≤ α + β uses a coarser and more stable region, and its discrete threshold is conservative. Sequential rules must also pay for monitoring after every flow instead of once per window, which raises their thresholds. Within a horizon of at most 200 flows this price outweighs the benefit of reacting early, and they win only on delay. These are empirical findings for this dataset and these horizons. Theory still favours CUSUM-type rules for longer, persistent changes with stable pre-change behaviour [@lorden1971procedures,moustakides1986optimal], and recent work shows that standard conformal martingales can be improved [@bhattacharyya2026optimal].`));
  C.push(P(`**Is the improvement operationally meaningful?** For the host-conditional counter, plausibly yes, with caveats. At W = 200 it detected about a third of the windows with a 5% attack share and about two thirds with a 10% share, at an average of ${f2(ch.fe_mean)} false escalations per host-week. It costs one stored threshold per host. However, the worst benign host exceeded the budget in ${ch.seeds_worst_over} of 10 seeds, every number is a simulation on randomly ordered flows, and detection within a single window is not detection within a day. Under the stated independence assumption the daily figure would be higher, but that assumption is not verifiable here. P10 detected more XSS but reached its average by exceeding the budget (${f2(cp.fe_mean)} per host-week at W = 200), which an operator would notice as extra escalations on specific hosts.`));
  C.push(P("**Is there a defensible methodological contribution?** No new detector is proposed. The host-conditional p-value is a Mondrian conformal construction combined with the maximum of two p-values; e-CUSUM and e-SR are e-detectors; the comparison baselines are classical. A defensible contribution lies elsewhere. It is a pre-specified, multi-seed comparison at a common calibration budget, together with exploratory analyses indicating that, for host-level IDS, calibration per host matters more than the choice of accumulator; this indication still needs confirmation on independent data. It also shows that anytime-valid thresholds and pooled conformal guarantees fail when benign hosts are heterogeneous, and that validation-calibrated host budgets transfer imperfectly. These are negative or qualifying results, and they are reported as such."));
  C.push(P("**Relation to trust management.** The host trust score of Section 4.4 is a re-expression of a calibrated statistic. Its value is that the operating point has an operational meaning — false escalations per host per week. Phase 10 shows that this meaning holds only as well as the reference describes the host. A deployed system would therefore need to refresh each host's reference continuously, to detect when a host's benign behaviour changes, and to guard the reference against poisoning: an attacker who is present during the reference period would raise the host's own threshold."));
}

function secLimitations(C) {
  C.push(H1("8. Limitations and Threats to Validity"));
  secLimitationsCore(C);
  C.push(P("Additional limitations specific to Phase 10:"));
  C.push(B("**Simulation, not deployment.** TON_IoT version B has no timestamps. Host streams are random orderings of each host's flows drawn with replacement, which removes temporal dependence, bursts, diurnal patterns and the real timing of attacks. Attack windows are synthetic mixtures of attack flows from attack hosts with benign flows of a benign host. All host-level results are therefore simulations."));
  C.push(B("**Calibration transfer.** Thresholds calibrated on benign_val did not keep every rule within the budget on benign_test. A likely contributor is the de-duplication before splitting, which places all repeated rows of a flow vector in one split. Whether the same transfer problem would occur with temporally split data is unknown."));
  C.push(B("**Few hosts.** Only 4–20 benign_val hosts had enough flows for calibration, depending on W; many hosts had too few reference flows and shared a fallback reference. Per-host results rest on few hosts, and the worst-host statistics are sensitive to a few of them (H2 and H4 for the window rules; low-traffic hosts that share the fallback reference for the sequential rules)."));
  C.push(B("**Non-blind design.** The protocol was written after the validation runs had started, and the per-host benign flag rates of benign_val and benign_test (two seeds), the earlier sparse-attack results and the per-family p-value rates had been inspected beforehand; this inspection motivated the host-conditional reference. The selection itself used validation data only, but the design was not blind to test-split properties."));
  C.push(B("**Exploratory findings.** The host-conditional counter and the matched-cost diagnostic were defined after the test results were seen. They are labelled exploratory, and the matched-cost thresholds use test data. They need confirmation on independent data before they can be claimed as results."));
  C.push(B("**Design choices.** The likelihood ratio was fitted on six known families, so its shape reflects them. The p-value bins, the window sizes, the budget of one false escalation per host-week and the traffic levels of 1,000 and 5,000 flows per day were fixed in advance and not varied beyond the stated grids."));
  C.push(B("**One dataset and a closed testbed.** Families in TON_IoT resemble each other (Section 6.11), and no second dataset was evaluated in Phase 10. Generalisation to other networks, and robustness to adaptive attackers who shape their traffic to stay below a host's threshold or to poison its reference, were not tested."));
  C.push(B("**Cost measurements.** Timing was measured on a laptop CPU with numba-compiled code, not on a microcontroller."));
}

function secConclusion(C) {
  C.push(H1("9. Conclusion and Future Work"));
  secConclusionCore(C);
  C.push(P("Phase 10 examined host-level detection of sparse attacks under a fixed false-escalation budget. Calibrating each host's p-values against its own benign history was the change that mattered. The pre-specified combination with likelihood-ratio e-values raised simulated detection several-fold but exceeded the budget on test hosts. The same host-conditional reference applied to the existing count rule kept the mean budget and retained most of the gain at W = 200 but much less in smaller windows, an exploratory result that needs confirmation. Sequential accumulators and theory-based thresholds did not help at the horizons studied."));
  C.push(P("**Before journal submission, the following work is essential:** (i) confirm the host-conditional counter on data with real timestamps and a temporal split, ideally a second dataset; (ii) design reference maintenance that tolerates drift and resists poisoning, and measure worst-host budgets over time; (iii) evaluate adaptive low-rate attackers; (iv) measure the full pipeline on a microcontroller."));
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
