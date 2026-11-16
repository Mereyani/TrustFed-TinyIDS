// ======================================================================================
// _head_en.js — English helpers for the TrustFed-TinyIDS manuscript (docx 9.x).
// English counterpart of rapor/_head.js. Files are concatenated (head + sections + tail),
// so everything here is a plain top-level global.
//
// Numbers: every value is read from rapor/values.json (written by rapor/make_final_values.py
// from colab_sonuclari/ only). The accessor functions below are identical to the Turkish
// ones; only the *display* formatting (decimal point, thousands comma, "45.6%") and the
// labels are English. Keys into values.json stay in their original form.
//
// Exports used by the section modules / assembler:
//   docx classes ............ Document, Packer, Paragraph, TextRun, ImageRun, Table, ... (as in _head.js)
//   EN_DIR, FIGDIR, VALUES_PATH, OUT_EN
//   colours / sizes ......... NAVY, BLUE, INK, MUTED, LINE, ZEBRA, CALL, FONT, TEXT_W
//   text helpers ............ runs, P, H1, H2, H3, B, EQ, pageBreak, callout
//   numbering ............... TAB, FIG (global counters), XREF, tabNum, figNum, tabRef, figRef
//   floats .................. table(head, rows, widths, caption, {key, note, leftAll}), figure(file, caption, widthIn, {key})
//   citations ............... CITE_ORDER (keys in order of first appearance), citeNum, cite, withCites, KNOWN_CITE_KEYS
//   number formatting ....... nf, pc, pt, pv, th, seedsOf
//   value accessors ......... V, fl, flt, own, ab, i8, rb, f2ok, f5, f5a, cost5, tinyC, minmax, ...
//   labels .................. SCN, PROT, PLAB, PLAB_SHORT, PS, SCN_LAB
//   document config ......... EN_STYLES, EN_NUMBERING (for the assembler's Document)
// ======================================================================================
const fs = require("fs"), path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType, WidthType, BorderStyle,
  ShadingType, PageBreak, Footer, PageNumber, LevelFormat, HeadingLevel, TableLayoutType, VerticalAlign,
} = require("docx");

// ---------- locations ----------
// The concatenated script may run from a temporary location, so the folder is resolved explicitly:
// env TFT_EN_DIR > script folder > cwd > fixed project path.
const EN_DIR = (() => {
  const cands = [process.env.TFT_EN_DIR, typeof __dirname !== "undefined" ? __dirname : null, process.cwd(),
    "E:/University/Master/Güz 2027/IoT/Vize Projesi/Final_Asama/manuscript/en"].filter(Boolean);
  for (const d of cands) if (fs.existsSync(path.join(d, "_head_en.js"))) return d;
  throw new Error("manuscript/en folder not found; set TFT_EN_DIR");
})();
const FIGDIR = path.join(EN_DIR, "figs");
const VALUES_PATH = path.join(EN_DIR, "..", "..", "rapor", "values.json");
const OUT_EN = path.join(EN_DIR, "_core_test.docx");
const NAVY = "1F3A5F", BLUE = "2A78D6", INK = "1F2328", MUTED = "5B6270", LINE = "D9DDE3", ZEBRA = "F5F7FA", CALL = "EEF4FB";
const FONT = "Calibri", TEXT_W = 9638;

// ---------- citations (IEEE numeric, numbered by first appearance) ----------
const KNOWN_CITE_KEYS = ["mcmahan2017", "li2020fedprox", "hsu2019noniid", "kairouz2021", "vovk2005alrw", "bates2023outliers",
  "angelopoulos2023", "moustafa2021toniot", "alsaedi2020toniot", "liu2008iforest", "jacob2018quant", "banbury2021mlperftiny",
  "holm1979", "wilcoxon1945", "geifman2017", "chow1970", "sommer2010", "arp2022"];
const CITE_ORDER = [];                       // keys in order of first appearance (read by the assembler for the reference list)
function citeNum(key) {
  key = key.trim();
  let i = CITE_ORDER.indexOf(key);
  if (i < 0) { CITE_ORDER.push(key); i = CITE_ORDER.length - 1; }
  return i + 1;
}
const cite = (keys) => `[${(Array.isArray(keys) ? keys : String(keys).split(",")).map((k) => citeNum(k)).join(", ")}]`;
// "[@a]" -> "[n]", "[@a,b]" -> "[n, m]" (registry updated in reading order)
const withCites = (text) => String(text).replace(/\[@([^\]]+)\]/g, (_, ks) => cite(ks.split(",").map((s) => s.trim().replace(/^@/, ""))));

// ---------- text helpers ----------
// runs(): citations first, then **bold** spans.
function runs(text, base = {}) {
  text = withCites(text);
  const out = []; const re = /(\*\*[^*]+\*\*)/g; let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    out.push(new TextRun({ text: m[0].slice(2, -2), bold: true, ...base }));
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}
const P = (t, o = {}) => new Paragraph({ children: runs(t, o.run || {}), spacing: { after: o.after ?? 120, before: o.before ?? 0, line: 276 },
  alignment: o.align || AlignmentType.JUSTIFIED, keepNext: o.keepNext });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: runs(t) });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: runs(t) });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: runs(t) });
const B = (t) => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: runs(t), spacing: { after: 70, line: 264 } });
// Display equation: centred, optional label "(n)" appended.
const EQ = (t, o = {}) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 120, line: 276 },
  children: [...runs(t, { italics: o.italics ?? false }), ...(o.label ? [new TextRun({ text: `    (${o.label})` })] : [])] });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

// ---------- table / figure numbering and cross-references ----------
let TAB = 0, FIG = 0;                          // global counters (IEEE: table caption above, figure caption below)
const XREF = { tab: {}, fig: {} };             // key -> number
// tabNum/figNum: return the number of a keyed float; if the float does not exist yet, the next number is
// reserved for it (use only when the referenced float is the next one of its kind to be created).
function tabNum(key) { if (!(key in XREF.tab)) XREF.tab[key] = ++TAB; return XREF.tab[key]; }
function figNum(key) { if (!(key in XREF.fig)) XREF.fig[key] = ++FIG; return XREF.fig[key]; }
const tabRef = (key) => `Table ${tabNum(key)}`;
const figRef = (key) => `Fig. ${figNum(key)}`;

function pngSize(f) { const b = fs.readFileSync(f); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; }
function figure(file, caption, widthIn = 6.5, opts = {}) {
  const f = path.join(FIGDIR, file), s = pngSize(f), w = Math.round(widthIn * 96), h = Math.round(w * s.h / s.w);
  const n = opts.key ? figNum(opts.key) : ++FIG;
  return [new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(f), transformation: { width: w, height: h },
        altText: { title: `Fig. ${n}`, description: withCites(caption).replace(/\*\*/g, ""), name: file } })] }),
    new Paragraph({ spacing: { after: 160 }, alignment: AlignmentType.JUSTIFIED,
      children: [new TextRun({ text: `Fig. ${n}. `, bold: true, size: 19, color: NAVY }), ...runs(caption, { size: 19, color: MUTED })] })];
}
const border = { style: BorderStyle.SINGLE, size: 4, color: LINE };
const borders = { top: border, bottom: border, left: border, right: border };
function table(head, rows, widths, caption, opts = {}) {
  const n = opts.key ? tabNum(opts.key) : ++TAB;
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (txt, i, isHead, r) => new TableCell({ borders, width: { size: widths[i], type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: { fill: isHead ? NAVY : (r % 2 ? ZEBRA : "FFFFFF"), type: ShadingType.CLEAR, color: "auto" },
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    children: [new Paragraph({ alignment: i === 0 || opts.leftAll ? AlignmentType.LEFT : AlignmentType.CENTER, spacing: { after: 0, line: 240 },
      children: runs(String(txt), { size: 18, bold: isHead, color: isHead ? "FFFFFF" : INK }) })] });
  return [new Paragraph({ keepNext: true, spacing: { before: 160, after: 60 },
      children: [new TextRun({ text: `Table ${n}. `, bold: true, size: 19, color: NAVY }), ...runs(caption, { size: 19, color: MUTED })] }),
    new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, layout: TableLayoutType.FIXED,
      rows: [new TableRow({ tableHeader: true, children: head.map((h, i) => cell(h, i, true, 0)) }),
        ...rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, i, false, ri)) }))] }),
    opts.note ? new Paragraph({ spacing: { before: 40, after: 160 }, children: runs(opts.note, { size: 17, color: MUTED }) })
      : new Paragraph({ spacing: { after: 100 }, children: [] })];
}
function callout(title, lines, fill = CALL, accent = BLUE) {
  const kids = [];
  if (title) kids.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: title, bold: true, color: NAVY, size: 22 })] }));
  for (const l of lines) kids.push(new Paragraph({ spacing: { after: 60, line: 264 }, children: runs(l) }));
  const nb = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  return [new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: [TEXT_W], layout: TableLayoutType.FIXED,
    rows: [new TableRow({ cantSplit: true, children: [new TableCell({ width: { size: TEXT_W, type: WidthType.DXA },
      borders: { top: nb, bottom: nb, right: nb, left: { style: BorderStyle.SINGLE, size: 24, color: accent } },
      shading: { fill, type: ShadingType.CLEAR, color: "auto" }, margins: { top: 120, bottom: 80, left: 200, right: 200 }, children: kids })] })] }),
    new Paragraph({ spacing: { after: 120 }, children: [] })];
}

// ---------- document configuration (for the assembler) ----------
const EN_STYLES = { default: { document: { run: { font: FONT, size: 22, color: INK } } },
  paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true, color: NAVY },
      paragraph: { spacing: { before: 360, after: 160 }, keepNext: true, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 25, bold: true, color: NAVY },
      paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 1 } },
    { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 23, bold: true, italics: true, color: NAVY },
      paragraph: { spacing: { before: 200, after: 100 }, keepNext: true, outlineLevel: 2 } },
  ] };
const EN_NUMBERING = { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
  style: { paragraph: { indent: { left: 500, hanging: 260 } } } }] }] };

// ---------- values ----------
const V = JSON.parse(fs.readFileSync(VALUES_PATH, "utf8").replace(/\bNaN\b/g, "null"));
// English number formatting: decimal point, thousands comma, "45.6%".
const nf = (v, d = 1) => Number(v).toFixed(d);                    // same rounding as the Turkish tr(), only the separator differs
const pc = (v, d = 1) => nf(100 * v, d) + "%";
const pt = (v, d = 1) => nf(100 * v, d);                          // percentage points, unsigned
const pv = (p) => (p < 0.001 ? "< 0.001" : nf(p, 3));
const th = (n) => Number(n).toLocaleString("en-US");              // integers with thousands comma
const seedsOf = (n) => `${n} of 10 seeds`;                         // Turkish "10 tohumun n’inde"
// Keys of values.json (kept verbatim; they are data keys, not display text)
const KPOOL = "havuz skor", KCLIENT = "istemci başına";
const KCENTRAL = "Merkezi (yakınsama)", FA = (p) => `FedAvg · ${p}`, KLOCAL = "Yalnız yerel (yakınsama)";
const KUNSEEN_ANO = "görülmemiş_ANOMALY";
const fl = (k, cal, s, m) => V[k].tab[`${cal}|${s}|${m}`];
const flt = (k, s, m, metric = KUNSEEN_ANO) => V[k].tests[`${KCENTRAL} | ${s} | ${KPOOL}||${FA(m)} | ${s} | ${KPOOL}||${metric}`];
const own = (k, key) => V[k].own[key];
const ab = (k, cfg, met) => V[k].abl[`${cfg}|${met}`];
const i8 = (k, m, r) => V[k].int8[`${m}|${r}`];
const rb = (k, b, l, p) => V[k].rob[`${b}|${l}|${p}`];
const SCN = ["IID", "Dirichlet=1.0", "Dirichlet=0.1"];
const SCN_LAB = { "IID": "IID", "Dirichlet=1.0": "Dirichlet 1.0", "Dirichlet=0.1": "Dirichlet 0.1" };
const PROT = ["orijinal", "orijinal_kucuk_yigin", "yakinsama_kalici", "fedprox_kalici"];
// Long labels (text and tables): faithful translations of the Turkish PLAB in rapor/_head.js
const PLAB = { orijinal: "P1 · fixed 40 rounds × 5 local epochs, Adam reset every round",
  orijinal_kucuk_yigin: "P2 · P1 + local batch 512/5 (number of steps ≈ central)",
  yakinsama_kalici: "P3 · until the convergence rule or the cap, Adam state kept",
  fedprox_kalici: "P4 · FedProx (μ = 0.01), until the cap, Adam state kept" };
// Short labels (figures; same as make_figs_en.py)
const PLAB_SHORT = { orijinal: "P1 · 40 rounds × 5 epochs, Adam reset", orijinal_kucuk_yigin: "P2 · equal steps (small batch)",
  yakinsama_kalici: "P3 · until cap, Adam persistent", fedprox_kalici: "P4 · FedProx μ = 0.01" };
const PS = { orijinal: "P1", orijinal_kucuk_yigin: "P2", yakinsama_kalici: "P3", fedprox_kalici: "P4" };
const cellAK = (k, cal, s, m) => { const r = fl(k, cal, s, m); return `${pc(r.ano)} ± ${pt(r.ano_sd)} (${pc(r.kac)})`; };
const F3m = fl("F3", KPOOL, "IID", KCENTRAL), F4m = fl("F4", KPOOL, "IID", KCENTRAL);
const vh = V.valhist, F1 = V.F1;
const t3 = (s, m) => flt("F3", s, m), t4 = (s, m) => flt("F4", s, m);
const f2ok = (W, F) => V.F2.olcut.find((r) => r.W === W && r.F === F);
const f5 = (W, rho, g = "görülmemiş") => V.F5.tespit.find((r) => r.W === W && Math.abs(r["ρ"] - rho) < 1e-9 && r.grup === g);
const f5a = (W, rho, g = "görülmemiş") => V.F5.tespit_anom.find((r) => r.W === W && Math.abs(r["ρ"] - rho) < 1e-9 && r.grup === g);
const cost5 = (W, cnt = "ANOMALY+UNCERTAIN", F = 1000) => V.F5.maliyet.find((r) => r.W === W && r.F === F && r["sayaç"] === cnt);
const tinyC = (k) => V[k].tiny["Merkezi AE"];
const minmax = (arr) => [Math.min(...arr), Math.max(...arr)];
// Phase 1–4 accessors (as in rapor/_body.js)
const P14 = V.P14;
const e1 = (m, d) => P14.E1.find((r) => r.model === m && r.decision === d);
const e3 = (g, f) => P14.E3[`${g}|${f}`];
const b2 = (m, g) => P14.b2[`${m}|${g}`];
const tierU = (rule) => P14.tier[`${rule}|0.01|görülmemiş`];
const e2r = (prev, c) => P14.E2.find((r) => r.prevalence === prev && r.comparison.startsWith(c));
const fst = (cmp, g) => P14.fs_tests.find((r) => r["karşılaştırma"] === cmp && r["saldırılar"] === g);
const epo = (n) => P14.epochs_seed0.find((r) => r.epoch === n);
const sp = P14.data.splits, pt_ = P14.data.per_type, sbt = P14.data.split_by_type, sl = P14.sel;
const ep10 = P14.train.epochs, capN = P14.train.stops.filter((s) => s === "epoch_cap").length;
const SD = (m, sd) => `${pc(m)} ± ${pt(sd)}`;
// Phase 10 value accessors. Every number comes from p10_values.json (written by phase10/make_p10_values.py
// from phase10/results/ only).
const V10 = JSON.parse(fs.readFileSync(path.join(EN_DIR, "p10_values.json"), "utf8").replace(/\bNaN\b/g, "null"));
const near = (a, b) => Math.abs(Number(a) - Number(b)) < 1e-9;
const KEY_EXIST = "pooled|W_COUNT_AU", KEY_HCOUNT = "host|W_COUNT_AU";
const KEY_P10 = `${V10.selection.selected.ref}|${V10.selection.selected.method}`;
const RHO0 = V10.selection.selected.rho0;
function d10(key, W, rho, group = "unseen", F = 1000) {
  const r = V10.detection_group_mean_sd.find((x) => x.key === key && x.W === W && near(x.rho, rho) && x.F === F && x.group === group);
  if (!r) throw new Error(`d10 missing ${key} ${W} ${rho} ${group} ${F}`);
  return r;
}
function c10(key, W, F = 1000) {
  const r = V10.benign_cost_compliance.find((x) => x.key === key && String(x.W) === String(W) && x.F === F);
  if (!r) throw new Error(`c10 missing ${key} ${W} ${F}`);
  return r;
}
const cW = (key, W, F = 1000) => { try { return c10(key, W, F); } catch (e) { return c10(key, "all", F); } };
function fam10(key, W, rho, family, F = 1000) {
  const r = V10.detection_family_mean_sd.find((x) => x.key === key && x.W === W && near(x.rho, rho) && x.family === family && x.F === F);
  if (!r) throw new Error(`fam10 missing ${key} ${W} ${rho} ${family}`);
  return r;
}
function dl10(key, W, rho, group = "unseen", F = 1000) {
  const r = V10.delay_group.find((x) => x.key === key && x.W === W && near(x.rho, rho) && x.group === group && x.F === F);
  if (!r) throw new Error(`dl10 missing ${key} ${W} ${rho}`);
  return r;
}
const prim10 = (W, rho) => V10.primary_comparison.find((x) => x.W === W && near(x.rho, rho));
const ex10 = (A, B, W, rho, oracle) => V10.exploratory_comparisons.find((x) => x.A === A && x.B === B && x.W === W && near(x.rho, rho)
  && x.analysis.startsWith(oracle ? "DIAGNOSTIC" : "EXPLORATORY"));
function mf10(key, W, rho, group = "unseen") {
  const r = V10.matched_fe1_summary.find((x) => x.key === key && x.W === W && near(x.rho, rho) && x.group === group);
  if (!r) throw new Error(`mf10 missing ${key} ${W} ${rho}`);
  return r;
}
const val10 = (ref, method, rho0) => V10.validation.find((x) => x.ref === ref && x.method === method && near(x.rho0, rho0));
const het10 = (label, split) => V10.heterogeneity.find((x) => x.label === label && x.split === split);
const ov10 = (prefix) => V10.overhead.find((x) => x.rule.startsWith(prefix));
const ML10 = {
  W_COUNT_AU: "count, p ≤ α+β", W_COUNT_A: "count, p ≤ α", W_FISHER: "Fisher", W_TPM: "truncated product", W_MINP: "min-p (Tippett)",
  W_HC: "Higher Criticism", W_EVID: "LR e-value window", BCUSUM: "Bernoulli CUSUM", EWMA_FLAG: "EWMA (flag)", EWMA_NLP: "EWMA (−log p)",
  E_CUSUM: "e-CUSUM", E_SR: "e-SR", E_CUSUM_MIX: "e-CUSUM, mixture calibrator", E_CUSUM_LEAKY: "leaky e-CUSUM",
  E_SR_ADAPT: "adaptive e-SR", E_CUSUM_TH: "e-CUSUM, theory threshold", E_SR_TH: "e-SR, theory threshold",
  E_SR_ADAPT_TH: "adaptive e-SR, theory threshold",
};
const RL10 = { pooled: "pooled", host: "host-cond." };
const lab10 = (key) => { const [r, m] = key.split("|"); return `${ML10[m]} [${RL10[r]}]`; };
const pcs = (r) => `${pc(r.mean)} ± ${pt(r.std)}`;
const f2 = (v) => nf(v, 2);
const pvh = (p) => (p < 0.001 ? "< 0.001" : nf(p, 3));
// ======================================================================================
// _core_en.js — English journal-style version of the core content (phases 1–9) of the
// TrustFed-TinyIDS report (rapor/_body.js, sections 3–8). Requires _head_en.js.
// Every number is produced by the same accessors (values.json) as the Turkish source.
//
// Functions (each pushes into the children array C passed by the assembler):
//   secFramework(C)        -> subsections 3.1–3.5   (Turkish §4.1–4.5)
//   secSetup(C)            -> subsections 5.1–5.5   (Turkish §3 and §4.6)
//   secResults(C)          -> subsections 6.1–6.11  (Turkish §5.1–5.11, all tables and figures)
//   secDiscussionCore(C)   -> paragraphs, no heading (Turkish §6)
//   secLimitationsCore(C)  -> bullets, no heading    (Turkish §7)
//   secConclusionCore(C)   -> paragraph + bullets, no heading (Turkish §8)
//   abstractCoreFacts      -> { key: { value, desc } } numbers the abstract may use
// Bullets use numbering reference "bul" (EN_NUMBERING in _head_en.js).
// ======================================================================================

// ---------- table builders (ported from rapor/_body.js, labels translated) ----------
const MLAB = { "Merkezi (yakınsama)": "Central", "FedAvg · orijinal": "FedAvg P1", "FedAvg · orijinal_kucuk_yigin": "FedAvg P2",
  "FedAvg · yakinsama_kalici": "FedAvg P3", "FedAvg · fedprox_kalici": "FedProx P4", "Yalnız yerel (yakınsama)": "Local only¹" };
const PKEY = { "FedAvg · orijinal": "orijinal", "FedAvg · orijinal_kucuk_yigin": "orijinal_kucuk_yigin", "FedAvg · yakinsama_kalici": "yakinsama_kalici", "FedAvg · fedprox_kalici": "fedprox_kalici" };
function flFull(k, cap, key) {
  const rows = [];
  for (const s of SCN) {
    for (const m of [KCENTRAL, ...PROT.map(FA)]) {
      const r = fl(k, KPOOL, s, m), pk = PKEY[m];
      rows.push([SCN_LAB[s], MLAB[m], pc(r.fpr_w, 2), pc(r.fpr_worst, 2), SD(r.ano, r.ano_sd), SD(r.kac, r.kac_sd), nf(r.f1, 3), nf(r.cov, 3), nf(r.sr, 3),
        pk ? nf(V[k].rounds[`${s}|${pk}`], 0) : "—", pk ? nf(V[k].comm[`${s}|${pk}`], 1) : "—"]);
    }
    const lr = V[k].tab[`${KCLIENT}|${s}|${KLOCAL}`];
    if (lr) rows.push([SCN_LAB[s], MLAB[KLOCAL], pc(lr.fpr_w, 2), pc(lr.fpr_worst, 2), SD(lr.ano, lr.ano_sd), SD(lr.kac, lr.kac_sd), nf(lr.f1, 3), nf(lr.cov, 3), nf(lr.sr, 3), "—", "—"]);
  }
  return table(["Split", "Model", "FPR (weighted)", "Worst-client FPR", "Recall (unseen)", "Missed", "F1", "Coverage", "Selective risk", "Rounds", "Communication (MB)"],
    rows, [1150, 1050, 800, 850, 1200, 1100, 650, 750, 750, 550, 788], cap,
    { key, note: "Pooled calibration (¹ local-only models: per-client calibration; run only for IID and Dirichlet 0.1). Recall = ANOMALY on unseen attacks. All metrics in this table are computed for each client (the client’s own normal test set + the shared known and unseen attack sets, α = 1%, β = 4%) and then averaged over the clients; coverage and selective risk therefore differ from the values in the ablation tables, which are computed on a single test set. Rounds and communication are means over 10 seeds; central and local models involve no communication (—)." });
}
const TLAB = { "Merkezi AE": "Central AE", "FedAvg-IID · orijinal": "FedAvg P1 (IID)", "FedAvg-IID · orijinal_kucuk_yigin": "FedAvg P2 (IID)",
  "FedAvg-IID · yakinsama_kalici": "FedAvg P3 (IID)", "FedAvg-IID · fedprox_kalici": "FedProx P4 (IID)" };
function tinyTab() {
  const rows = [];
  for (const [k, n] of [["F3", "53"], ["F4", "21"]]) for (const m of Object.keys(TLAB)) {
    const t = V[k].tiny[m];
    rows.push([`${TLAB[m]} · ${n}`, th(t.parametre), nf(t.tflite_fp32_KB), nf(t.tflite_int8_KB), nf(t.tahmini_RAM_KB_int8),
      `${nf(t["gecikme_fp32_µs_colab"], 2)} / ${nf(t["gecikme_int8_µs_colab"], 2)}`, `${nf(t.Spearman_FP32_INT8, 2)} (${nf(t.sp_min, 2)}–${nf(t.sp_max, 2)})`]);
  }
  return table(["Model · features", "Parameters", "TFLite FP32 (KB)", "TFLite INT8 (KB)", "Rough RAM, INT8 (KB)", "Latency FP32 / INT8 (µs, Colab CPU)", "Spearman FP32–INT8 (normal test)"],
    rows, [2238, 1000, 1100, 1100, 1100, 1600, 1500], "TinyML: model size, rough memory estimate, latency and score rank agreement (mean over 10 seeds)",
    { key: "tiny", note: "Latency was measured on the Colab CPU with a single sample; it is not a microcontroller value. The RAM estimate does not include the TFLite Micro working area. Spearman correlation was computed on the normal test scores only; in parentheses, the minimum–maximum across seeds." });
}
const RCLAB = { "Isolation Forest": "Isolation Forest", "AE gizil skor": "AE latent score (Mahalanobis)", "AE merkezi": "AE central", "AE merkezi INT8": "AE central INT8",
  "Federe AE · orijinal": "FedAvg P1", "Federe AE INT8 · orijinal": "FedAvg P1 INT8", "Federe AE · orijinal_kucuk_yigin": "FedAvg P2", "Federe AE INT8 · orijinal_kucuk_yigin": "FedAvg P2 INT8",
  "Federe AE · yakinsama_kalici": "FedAvg P3", "Federe AE INT8 · yakinsama_kalici": "FedAvg P3 INT8", "Federe AE · fedprox_kalici": "FedProx P4", "Federe AE INT8 · fedprox_kalici": "FedProx P4 INT8" };
function rcTab(k, cap, key) {
  const g = (m, y, c) => { const v = V[k].rc[`${m}|${y}|${c}`]; return v === null || v === undefined || Number.isNaN(Number(v)) ? "—" : nf(v, y === "test kümesi" ? 3 : 4); };
  const rows = Object.keys(RCLAB).filter((m) => V[k].rc[`${m}|test kümesi|0.70`] !== undefined)
    .map((m) => [RCLAB[m], ...["0.50", "0.70", "0.90", "1.00"].map((c) => g(m, "test kümesi", c)), ...["0.70", "0.90"].map((c) => g(m, "π=%1", c))]);
  return table(["Model (FL: IID)", "Coverage 0.5", "0.7", "0.9", "1.0", "π = 1% · 0.7", "π = 1% · 0.9"], rows, [2838, 1150, 1100, 1100, 1100, 1175, 1175], cap,
    { key, note: "Values are selective risk (lower is better); each curve was obtained by sweeping β with α = 1% fixed, read at fixed coverage levels and averaged over 10 seeds. Risk–coverage curves were computed only for the IID federated models; the coverage and selective risk of the non-IID federated models and the local models at α = 1%, β = 4% are given in the all-model tables of Sections 6.5 and 6.10." });
}
function robTab(k, cap, key) {
  const RBx = [["temiz", "0.0", "clean"], ["gürültü", "0.01", "noise σ = 0.01"], ["gürültü", "0.05", "noise σ = 0.05"], ["gürültü", "0.1", "noise σ = 0.10"],
    ["eksik", "0.05", "5% missing"], ["eksik", "0.1", "10% missing"], ["eksik", "0.2", "20% missing"], ["bozuk özellik", "1.0", "1 corrupted feature"], ["bozuk özellik", "3.0", "3 corrupted features"], ["bozuk özellik", "5.0", "5 corrupted features"]];
  const rows = RBx.map(([b, l, lab]) => { const d = rb(k, b, l, "devralınan eşik"), r = rb(k, b, l, "yeniden kalibrasyon");
    return [lab, nf(d.f1, 3), nf(d.cov, 3), nf(d.sr, 3), nf(r.f1, 3), nf(r.cov, 3), nf(r.sr, 3)]; });
  return table(["Corruption", "Inherited: F1", "Coverage", "Selective risk", "Recalibrated: F1", "Coverage", "Selective risk"], rows, [2038, 1300, 1250, 1250, 1300, 1250, 1250], cap,
    { key, note: "F1 for unseen attacks (ANOMALY = positive); coverage and selective risk on the test set. Mean over 10 seeds × 3 repetitions." });
}

// ======================================================================================
// 3.x  The TrustFed-TinyIDS framework (Turkish §4.1–4.5)
// ======================================================================================
function secFramework(C) {
  C.push(H2("3.1 Model and training"));
  C.push(P(`The flow-level detector is an autoencoder (AE) with the architecture 53 → 32 → 16 → 8 → 16 → 32 → 53 (${th(sl.ae_32_16_8.parametre)} parameters, ReLU, mean squared error loss, Adam, learning rate 0.001, batch size 512). The anomaly score s(x) of a flow x is the reconstruction error of the AE. This architecture was selected because, on the development data of the known attack families, it gave a higher PR-AUC than two alternatives (16-8-4, and 32-16-8 with dropout): ${nf(sl.ae_32_16_8.gelistirme_dogrulama_pr_auc, 3)}, versus ${nf(sl.ae_16_8_4.gelistirme_dogrulama_pr_auc, 3)} and ${nf(sl.ae_32_16_8_do.gelistirme_dogrulama_pr_auc, 3)}. Training is stopped by a convergence rule fixed in advance: stop when the best validation loss improves by less than 0.5% over 50 epochs; early stopping with a patience of 40 epochs; at most 1,500 epochs. Over the 10 seeds, training lasted ${Math.min(...ep10)}–${th(Math.max(...ep10))} epochs (${10 - capN} seeds stopped by the convergence rule and ${capN} by the cap).`));

  C.push(H2("3.2 Conformal p-value and three-way decision rule"));
  C.push(P("The score is converted into a p-value with respect to normal calibration data [@vovk2005alrw,bates2023outliers]. With s₁, …, sₙ the scores of the n normal calibration flows,"));
  C.push(EQ("p(x) = (1 + #{i : sᵢ ≥ s(x)}) / (n + 1),     n = 3,348,"));
  C.push(P("that is, one plus the number of calibration scores greater than or equal to s(x), divided by n plus one. If the calibration data and the normal test data come from the same distribution, the rule “alarm if p ≤ α” produces, on average, at most a fraction α of false alarms on normal traffic, and no attack labels are needed for this [@angelopoulos2023]. The three-way decision rule, in which UNCERTAIN defers the decision [@chow1970], is"));
  C.push(EQ("p ≤ 1% → ANOMALY,     1% < p ≤ 5% → UNCERTAIN,     p > 5% → NORMAL     (α = 1%, β = 4%)."));
  C.push(P("For models in which tied scores are frequent (Isolation Forest [@liu2008iforest], the latent score and INT8 models), a randomised p-value is used."));

  C.push(H2("3.3 UNCERTAIN resolution: host trust signal"));
  C.push(P("At the flow level, only ANOMALY produces an immediate alarm; UNCERTAIN decisions are not sent to the analyst but serve as input to a host counter. The counter counts the ANOMALY + UNCERTAIN decisions within a window of W flows of a host and escalates the host to the upper-level system when the count reaches k*. The threshold k* is selected on normal validation hosts such that there is at most 1 false escalation per device per week (with F flows per day, the per-window budget is W / (7F)). The source IP is used as the host identifier, for grouping only. Because the data contain no timestamps, windows are drawn at random from the flows of a host; the host experiments are therefore simulations. In addition, a “gateway” step was evaluated that forwards UNCERTAIN flows to a Random Forest (RF) trained only on the known families."));

  C.push(H2("3.4 Federated learning"));
  C.push(P("The normal data were distributed across 5 clients in three ways: IID, and Dirichlet partitions over the service column with α_D = 1.0 and 0.1 [@hsu2019noniid]. Four training protocols, based on FedAvg [@mcmahan2017] and FedProx [@li2020fedprox], were compared:"));
  for (const p of PROT) C.push(B(`**${PLAB[p]}**`));
  C.push(P("P1 gives the same number of epochs as the central model (200), but because each client sees one fifth of the data, the number of update steps is much smaller (~800 versus ~3,400); P2 equalises the number of steps. P3 and P4 use the convergence rule of the central model (one round = 5 local epochs). In addition, local models trained by each client on its own data only were compared. Calibration was performed in two ways: **pooled calibration** (the clients send their normal calibration scores to the server; scores, not data, are shared) and **per-client calibration**."));

  C.push(H2("3.5 TinyML, robustness and ablation design"));
  C.push(P("The central model and the IID FedAvg models were converted to TFLite FP32 and INT8 [@jacob2018quant] (representative set of 500 normal training vectors). For INT8, three rules were compared: FP32 score and threshold; INT8 score with the inherited FP32 threshold; and recalibration on INT8 scores. For robustness, Gaussian noise (σ = 0.01–0.10), missing features (5–20%, median imputation) and corrupted features (the values of 1, 3 or 5 features shuffled across samples) were applied, with 3 repetitions; for each corruption, the inherited threshold was compared with recalibration on corrupted normal data. The ablation compared A1 Isolation Forest, A2 AE (binary), A3 AE + three-way decision, A3q INT8 AE + three-way decision, A4–A5 federated AE (binary / three-way decision) and A6 INT8 federated AE."));
}

// ======================================================================================
// 5.x  Experimental setup and evaluation protocol (Turkish §3 and §4.6)
// ======================================================================================
function secSetup(C) {
  C.push(H2("5.1 Dataset and preprocessing"));
  C.push(P(`The train_test_network.csv file of the TON_IoT network data [@moustafa2021toniot,alsaedi2020toniot] was used. The version used here consists of ${th(P14.data.rows)} rows and ${P14.data.cols} columns and contains no time column. The IP address and port columns were removed, as were text-valued columns such as the DNS query, HTTP and SSL fields. The data contain many duplicates: after removing identical rows and vectors that are identical after preprocessing, the ${th(P14.data.rows)} flows were reduced first to ${th(P14.data.after1)} and then to ${th(P14.data.after2)} unique vectors (e.g. only ${th(pt_.ransomware.after)} of the ${th(pt_.ransomware.before)} ransomware rows are distinct). Signed log(1 + x) and MinMax scaling were applied to the numerical columns and one-hot encoding to the categorical columns, and features with a mutual correlation above 0.98 were removed, leaving ${P14.data.n_feat} features. The scaler, the encoder and the correlation filter were fitted on the normal training data only.`));
  C.push(P("Some of the 53 features (the DNS, SSL and HTTP fields and the service label) require application-layer parsing, which assumes a Zeek-like flow extractor at the gateway. For constrained edge nodes, a separate **device feature set** was defined, consisting of 10 flow fields that can be counted from header and connection information alone, without parsing the packet payload (protocol, duration, byte and packet counts, connection state); after one-hot encoding it comprises 21 features."));

  C.push(H2("5.2 Data split"));
  C.push(...table(["Split", "Content", "Vectors"], [
    ["Normal training / validation", "normal", `${th(sp.benign_train)} / ${th(sp.benign_val)}`],
    ["Normal calibration / test", "normal", `${th(sp.benign_cal)} / ${th(sp.benign_test)}`],
    ["Known families (development / test)", "backdoor, ddos, dos, injection, password, scanning", `${th(sp.dev_val)} / ${th(sp.dev_test)}`],
    ["Unseen families (test only)", `ransomware (${th(sbt.heldout_test.ransomware)}), xss (${th(sbt.heldout_test.xss)}), mitm (${th(sbt.heldout_test.mitm)})`, th(sp.heldout_test)],
  ], [3000, 4638, 2000], "Data split (split seed 2027, fixed in all experiments)", { key: "split" }));
  C.push(P("The unseen families and the decision budgets were fixed in the project proposal, before the first run. The known families are not used to train the AE; they are used only for model-size selection, for training the Random Forest (RF) used for comparison, and for reporting."));

  C.push(H2("5.3 Leakage check"));
  const lk = fst("sızıntı - tümü", "bilinen"), lku = fst("sızıntı - tümü", "görülmemiş");
  C.push(P(`When the IP and port columns were added back to the model, recall on the known attacks at 1% false alarms increased by ${pt(lk.ortalama_fark)} points (in ${seedsOf(lk.kazanan_tohum)}; p_Holm = ${pv(lk.p_holm)}), whereas on the unseen attacks it did not change significantly (p_Holm = ${pv(lku.p_holm)}). This increase most likely stems from the address information of the machines rather than from attack behaviour [@arp2022]; these columns were therefore removed.`));

  C.push(H2("5.4 Evaluation protocol and statistical analysis"));
  C.push(P("The data split was kept fixed and 10 training seeds (0–9) were used; in each seed, the central model of that seed and the seed-dependent client split are used. Tables report the mean over the 10 seeds; for the main results, the ± standard deviation (in percentage points) is also given. Bootstrap 95% confidence intervals are provided in the summary CSV files of the output folders; paired comparisons use the Wilcoxon signed-rank test [@wilcoxon1945] with Holm correction (p_Holm) [@holm1979]. The intervals reflect training-seed variability only. A few comparisons that were not predefined in the notebooks were additionally computed from the same per-seed results; these are marked as “**additional test**”, and no Holm correction was applied to them. Because attacks form the majority of the test set, precision and selective risk are additionally reported re-weighted to a scenario in which attacks make up 1% of the traffic (π = 1%). Coverage is the fraction of decisions other than UNCERTAIN (automatic decisions); selective risk is the fraction of errors among the automatic decisions (an attack declared NORMAL or a normal flow declared ANOMALY) [@geifman2017]."));

  C.push(H2("5.5 Computing environment"));
  C.push(P("All training and evaluation runs of the framework (Sections 6.1–6.11) were performed on Google Colab with a Tesla T4 GPU, with a fixed data split and 10 training seeds (for LOFO, 10 separate seeds fixed in advance). All reported numbers are read automatically from the output files written by these runs. Environment: Google Colab, Tesla T4 GPU, TensorFlow 2.21.0, Python 3.13.16, NumPy 2.4.6, scikit-learn 1.6.1 (recorded in an environment.json file in each output folder). For one seed, the complete set of experiments of Sections 6.5–6.9 mostly took 21–24 minutes on the T4 (computed from file timestamps)."));
}

// ======================================================================================
// 6.x  Results (Turkish §5.1–5.11)
// ======================================================================================
function secResults(C) {
  // ---------------- 6.1
  C.push(H2("6.1 Baseline models and feature sets"));
  const aeU = b2("ae", "görülmemiş"), aeK = b2("ae", "bilinen"), ifU = b2("iforest", "görülmemiş"), ltU = b2("latent", "görülmemiş");
  C.push(...table(["Model (α = 1%)", "Normal FPR", "Recall unseen", "Recall known", "ROC-AUC unseen", "PR-AUC unseen"], [
    ["Isolation Forest", pc(ifU.fpr, 2), pc(ifU.recall), pc(b2("iforest", "bilinen").recall), nf(ifU.roc_auc, 3), nf(ifU.pr_auc, 3)],
    ["AE latent space (Mahalanobis)", pc(ltU.fpr, 2), pc(ltU.recall), pc(b2("latent", "bilinen").recall), nf(ltU.roc_auc, 3), nf(ltU.pr_auc, 3)],
    ["AE reconstruction error", pc(aeU.fpr, 2), pc(aeU.recall), pc(aeK.recall), nf(aeU.roc_auc, 3), nf(aeU.pr_auc, 3)],
  ], [2838, 1300, 1400, 1300, 1400, 1400], "Baseline models, binary decision p ≤ 1% (10 seeds)", { key: "baseline" }));
  const e200 = epo(200), e100 = epo(100), e1500 = epo(1500);
  // forward reference: the per-family figure is the next figure created (Section 6.2)
  C.push(P(`A high AUC does not imply usable detection: the ROC-AUC of Isolation Forest on the unseen families is ${nf(ifU.roc_auc, 2)}, yet at the 1% budget it flags no attack. At the same budget, the AE detects ${pc(aeU.recall)} of the unseen attacks but only ${pc(aeK.recall)} of the known attacks. Since all attacks are unseen from the point of view of the AE, this difference arises because known families such as injection and password closely resemble normal traffic (${figRef("families")}). Training length is also decisive: for seed 0, unseen recall is ${pc(e100["recall_görülmemiş"])} at 100 epochs, ${pc(e200["recall_görülmemiş"])} at 200 epochs and ${pc(e1500["recall_görülmemiş"])} at 1,500 epochs.`));
  const dK = fst("cihaz - tümü", "bilinen"), dU = fst("cihaz - tümü", "görülmemiş");
  C.push(P(`**Device feature set.** At 1% false alarms, the 21-feature set gave higher recall than the 53-feature set, by ${pt(dK.ortalama_fark)} points on the known families (in ${seedsOf(dK.kazanan_tohum)}; p_Holm = ${pv(dK.p_holm)}) and by ${pt(dU.ortalama_fark)} points on the unseen families (in ${seedsOf(dU.kazanan_tohum)}; p_Holm = ${pv(dU.p_holm)}). Dropping the application-layer fields therefore did not reduce detection. This set was taken through all the FL and INT8 experiments in Section 6.10.`));

  // ---------------- 6.2
  C.push(H2("6.2 Three-way rule: false-alarm guarantee and per-family decisions"));
  C.push(P(`When the normal calibration and test data were randomly re-split 200 times, the mean ANOMALY rate of the AE on normal traffic was ${pc(e1("ae", "ANOMALY").mean, 2)} and the UNCERTAIN rate ${pc(e1("ae", "UNCERTAIN").mean, 3)} (budgets 1% and 4.03%); for Isolation Forest and the latent score the rates also matched the budget (${pc(e1("iforest", "ANOMALY").mean, 2)} and ${pc(e1("latent", "ANOMALY").mean, 2)}). Because the guarantee holds on average, small deviations occur on the fixed test split (AE: ${pc(ab("F3", "A3 · AE + seçici", "normal_FPR").m, 2)}). The widely used μ+3σ threshold (mean of the training errors plus 3 standard deviations) promises 0.135% false alarms under a Gaussian assumption; in practice this rate is ${pc(P14.B3.B3_normal_ANOMALY.mean, 2)}, compared with ${pc(P14.B3.konformal_normal_ANOMALY.mean, 2)} for the conformal threshold (10 seeds).`));
  C.push(...figure("aile_kararlari.png", "Distribution of the three decisions for each family, AE, mean over 10 seeds. * family never used in training or model selection.", 6.5, { key: "families" }));
  const hm = e3("held-out", "macro-average");
  C.push(P(`Averaged over the unseen families (equal weight per family), ${pc(hm.anomaly_rate)} of the flows are ANOMALY, ${pc(hm.uncertain_rate)} UNCERTAIN and ${pc(hm.normal_rate)} NORMAL. The families behave very differently: ${pc(e3("held-out", "ransomware").uncertain_rate)} of ransomware flows are UNCERTAIN (the model is not certain about a single flow but is suspicious), ${pc(e3("held-out", "xss").anomaly_rate)} of xss flows are ANOMALY, and mitm is the hardest family (${pc(e3("held-out", "mitm").normal_rate)} NORMAL). Among the known families, injection (${pc(e3("known", "injection").normal_rate)}) and password (${pc(e3("known", "password").normal_rate)}) mostly receive a NORMAL decision. Vector-level (micro-averaged) rates differ because of the weight of xss: ${pc(F3m.ano)} of the unseen flows are ANOMALY and ${pc(F3m.kac)} NORMAL.`));

  // ---------------- 6.3
  C.push(H2("6.3 Selective detection: alarm and review load"));
  const tb = tierU("binary α=0.01"), t5_ = tierU("binary α+β=0.05"), t3w = tierU("three-way α=0.01, β=0.04");
  C.push(...table(["Rule (unseen families, attack share 1%)", "Immediate alarms / 10,000 flows", "Alarm precision", "Reviews / 10,000 flows", "Review precision", "Missed attacks"], [
    ["Binary, p ≤ 1%", nf(tb.alarms_per_flows, 0), nf(tb.precision_alarm_tier, 3), "—", "—", pc(tb.attack_missed)],
    ["Binary, p ≤ 5%", nf(t5_.alarms_per_flows, 0), nf(t5_.precision_alarm_tier, 3), "—", "—", pc(t5_.attack_missed)],
    ["Three-way (α = 1%, β = 4%)", nf(t3w.alarms_per_flows, 0), nf(t3w.precision_alarm_tier, 3), nf(t3w.reviews_per_flows, 0), nf(t3w.precision_review_tier, 3), pc(t3w.attack_missed)],
  ], [3038, 1400, 1200, 1400, 1200, 1400], "Alarm and review load (10 seeds)", { key: "tiering" }));
  C.push(P(`The immediate alarms of the three-way rule are identical to those of the binary p ≤ 1% rule, and ANOMALY and UNCERTAIN together flag the same flows as the binary p ≤ 5% rule. The three-way decision therefore adds no new detection power; it splits the flagged flows into two tiers: instead of the ${nf(t5_.alarms_per_flows, 0)} alarms of the binary p ≤ 5% rule, which achieves the same total detection, there are ${nf(t3w.alarms_per_flows, 0)} immediate alarms (precision ${nf(t3w.precision_alarm_tier, 3)}) and a review queue of ${nf(t3w.reviews_per_flows, 0)} flows (precision ${nf(t3w.precision_review_tier, 3)}). Because the precision of the queue is low, sending it directly to an analyst is not practical; the queue is therefore used as input to the host counter (Section 6.4).`));
  const eIF = e2r("test kümesi", "B1"), eLt = e2r("test kümesi", "B5"), eB3 = e2r("test kümesi", "B3"), eRnd = e2r("test kümesi", "rastgele");
  const eIF1 = e2r("0.01", "B1"), eLt1 = e2r("0.01", "B5");
  C.push(P(`**Does deferral carry information?** Compared with alternatives that defer the same number of flows (pre-specified primary analysis, test set), the selective risk of the conformal AE band is lower by ${nf(eIF.mean_delta_sr, 2)} than that of the Isolation Forest band, by ${nf(eLt.mean_delta_sr, 2)} than that of the latent-score band and by ${nf(eRnd.mean_delta_sr, 2)} than that of random deferral; it is higher by ${nf(-eB3.mean_delta_sr, 2)} than that of the μ+3σ band, because μ+3σ detects more attacks by exceeding the false-alarm budget. In the 1% scenario, in which attacks are rare (exploratory), the conformal AE gave a lower risk than all three alternatives (${nf(eLt1.mean_delta_sr, 3)} … ${nf(eIF1.mean_delta_sr, 3)}). In all comparisons the direction was the same in 10 of 10 seeds, p_Holm ≤ ${pv(Math.max(...P14.E2.map((r) => r.p_holm)))}.`));

  // ---------------- 6.4
  C.push(H2("6.4 Host trust signal and sparse attacks"));
  const rhos = [0.05, 0.1, 0.25, 0.5, 1.0], Ws = [20, 50, 100, 200];
  C.push(...table(["ρ", ...Ws.map((W) => `W = ${W}`)], rhos.map((r) => [r === 0.05 ? "≤ 0.05" : nf(r, 2),
    ...Ws.map((W) => { const a = f5(W, r); if (!a) return "—"; if (r === 0.05) { const vs = [0.01, 0.02, 0.05].map((x) => f5(W, x)).filter(Boolean); return pc(Math.max(...vs.map((q) => q.pencere_tespit_mean))); } return pc(a.pencere_tespit_mean); })]),
    [1638, 2000, 2000, 2000, 2000], "Host-window detection on the unseen families; ρ = share of attack flows in the window, ANOMALY + UNCERTAIN counter, F = 1,000 flows/day (10 seeds, simulation)",
    { key: "sparse", note: "The “≤ 0.05” row gives the highest value over the ρ values for which the window contains at least one attack flow. W = 500 was not used: only two normal hosts had enough flows for calibration, and 28.2% of the normal windows were escalated (target 7.1%); the high detection in this setting stems from false alarms." }));
  C.push(...figure("seyrek.png", "Detection by the host counter as a function of the attack share (unseen families, F = 1,000 flows/day, 10 seeds, simulation).", 5.8, { key: "sparse" }));
  const cw = (W) => V.F5.en_kotu_host[W] ? Object.values(V.F5.en_kotu_host[W]) : [];
  const okSeeds = (W) => cw(W).filter((v) => v <= 1).length;
  C.push(B(`**The counter is effective against dense attacks.** The immediate-alarm rate of ${pc(F3m.ano)} for a single flow becomes 100% escalation for hosts whose traffic is entirely malicious at W ≥ 50. When only ANOMALY is counted, this rate remains at ${pc(f5a(50, 1).pencere_tespit_mean)} at W = 50; UNCERTAIN decisions are therefore evidence that can accumulate.`));
  C.push(B(`**The counter is ineffective against sparse attacks.** When attack flows make up ≤ 5% of the traffic in the window, detection is 0%; at ρ = 10% it is at most ${pc(f5(200, 0.1).pencere_tespit_mean)}. The mechanism works only at ρ ≈ 25% and W ≥ 50 (${pc(f5(50, 0.25).pencere_tespit_mean)}–${pc(f5(200, 0.25).pencere_tespit_mean)}). This analysis was not pre-registered; it is exploratory.`));
  C.push(B(`**Cost on normal hosts.** Number of seeds in which the worst normal host stayed within the weekly budget: ${okSeeds(20)}/10 at W = 20, ${okSeeds(50)}/10 at W = 50, ${okSeeds(100)}/10 at W = 100 and ${okSeeds(200)}/10 at W = 200. Where the budget is exceeded, a single normal host appears persistently suspicious (350 false escalations per week at W = 20).`));
  const g = P14.gw;
  C.push(P(`**Gateway step (UNCERTAIN → RF).** Within the UNCERTAIN band, the RF separates attacks from normal flows well (AUC ${nf(g.mitm.auc, 3)}–${nf(g.ransomware.auc, 3)}). When the UNCERTAIN flows confirmed by the RF are added to the ANOMALY decisions of the AE, flow-level detection changed from ${pc(g.ransomware.ae)} to ${pc(g.ransomware.ae_gw)} for ransomware, from ${pc(g.xss.ae)} to ${pc(g.xss.ae_gw)} for xss and from ${pc(g.mitm.ae)} to ${pc(g.mitm.ae_gw)} for mitm, with a false-alarm rate of ${pc(g["normal (yanlış alarm)"].ae_gw)} on normal traffic. However, the RF alone detects these families at rates of ${pc(g.xss.rf)}–${pc(g.ransomware.rf)}; this was the first indication of the dataset limitation discussed in Section 6.11.`));

  // ---------------- 6.5
  C.push(H2("6.5 Federated learning: why can the federated model fall behind?"));
  C.push(P("A single-seed (seed 0) diagnostic experiment (31 training runs) was carried out first to test three hypotheses: **H1** the clients perform fewer update steps than the central model; **H2** the Adam state is reset in every round; **H3** non-IID clients drift apart from each other [@kairouz2021]."));
  C.push(...table(["Model (seed 0, IID, pooled calibration)", "Steps per client", "Unseen ANOMALY", "Missed"], [
    ["Central, until the convergence rule", "21,658", pc(F1.M_yak.ano), pc(F1.M_yak.kac)],
    ["Central, 200 epochs", "3,400", pc(F1.M_200.ano), pc(F1.M_200.kac)],
    ["Central, same number of steps as P1 (47 epochs)", "799", pc(F1.M_esit.ano), pc(F1.M_esit.kac)],
    ["FedAvg P1", "800", pc(F1.FL_orj.ano), pc(F1.FL_orj.kac)],
    ["FedAvg P2 (H1)", "3,400", pc(F1.FL_kucuk.ano), pc(F1.FL_kucuk.kac)],
    ["FedAvg, until the cap, Adam reset every round", "6,000", pc(F1.FL_reset.ano), pc(F1.FL_reset.kac)],
    ["FedAvg P3 (H1 + H2)", "6,000", pc(F1.FL_kalici.ano), pc(F1.FL_kalici.kac)],
    ["FedProx P4", "6,000", pc(F1.FL_prox.ano), pc(F1.FL_prox.kac)],
  ], [4400, 1600, 1838, 1800], "Diagnostic experiment (single seed)", { key: "fldiag" }));
  C.push(P(`The diagnosis supported H1 and H2 but also gave an important warning: when the same central training (200 epochs, same initial weights) was run with Keras and with the FL code using a single client, with only the batch order differing, the results were ${pc(F1.M_200.ano)} and ${pc(F1.K1_kalici.ano)}. This metric is highly volatile for under-trained models; the four protocols were therefore repeated with 10 seeds.`));
  C.push(...table(["Model", ...SCN.map((s) => SCN_LAB[s])], [
    ["Central (convergence rule)", ...SCN.map((s) => cellAK("F3", KPOOL, s, KCENTRAL))],
    ...PROT.map((p) => [PLAB[p], ...SCN.map((s) => cellAK("F3", KPOOL, s, FA(p)))]),
  ], [3838, 1933, 1933, 1934], "ANOMALY on unseen attacks (missed in parentheses), 53 features, 10 seeds, pooled calibration", { key: "flmain", note: "The central model is not affected by the client split; the same value is therefore repeated in every column." }));
  C.push(...figure("fl_merkezi.png", "ANOMALY rate on unseen attacks; bar = mean over 10 seeds, dot = single seed. Left: 53 features; right: 21-feature device model. Pooled calibration.", 6.5, { key: "flcentral" }));
  const tO = t3("IID", "orijinal"), tK = t3("IID", "orijinal_kucuk_yigin"), tY = t3("IID", "yakinsama_kalici");
  const kY = own("F3", "kac|IID|yakinsama_kalici"), h1 = own("F3", "H1|IID"), h1d = own("F3", "H1|Dirichlet=0.1");
  const px = (s) => own("F3", `prox|${s}`);
  C.push(B(`**The gap with P1 is large and consistent:** in IID, ${pc(fl("F3", KPOOL, "IID", FA("orijinal")).ano)} (P1) versus ${pc(F3m.ano)} (central); the central model is higher in ${seedsOf(tO.a_buyuk)} (p_Holm = ${pv(tO.p_holm)}).`));
  C.push(B(`**H1 explains most of the gap, but not all of it.** When the number of steps is equalised (P2), ANOMALY increases by ${pt(h1.fark)} points (in ${seedsOf(h1.a_buyuk)}; additional test p = ${pv(h1.p)}) but remains ${pt(tK.fark)} points below the central model (p_Holm = ${pv(tK.p_holm)}). The single-seed result (${pc(F1.FL_kucuk.ano)}) was optimistic.`));
  C.push(B(`**With equivalent training, the IID gap largely closes.** P3 reaches ${pc(fl("F3", KPOOL, "IID", FA("yakinsama_kalici")).ano)} and the central model ${pc(F3m.ano)}: the difference is ${pt(tY.fark)} points, the central model is higher in ${seedsOf(tY.a_buyuk)}, and the difference is not significant (p_Holm = ${pv(tY.p_holm)}). The missed rate, however, remains ${pt(kY.fark)} points higher in FL (in ${seedsOf(kY.a_buyuk)}; additional test p = ${pv(kY.p)}).`));
  C.push(B(`**Under non-IID partitions the gap persists (H3).** P3 reaches ${pc(fl("F3", KPOOL, "Dirichlet=1.0", FA("yakinsama_kalici")).ano)} at Dirichlet 1.0 (p_Holm = ${pv(t3("Dirichlet=1.0", "yakinsama_kalici").p_holm)}) and ${pc(fl("F3", KPOOL, "Dirichlet=0.1", FA("yakinsama_kalici")).ano)} at Dirichlet 0.1 (p_Holm = ${pv(t3("Dirichlet=0.1", "yakinsama_kalici").p_holm)}). Equalising the number of steps gave no consistent improvement at Dirichlet 0.1 (+${pt(h1d.fark)} points, in ${seedsOf(h1d.a_buyuk)}; additional test p = ${pv(h1d.p)}).`));
  C.push(B(`**FedProx (μ = 0.01) gave no consistent improvement:** relative to P3, the difference is ${nf(100 * px("IID").fark)} points in IID, ${nf(100 * px("Dirichlet=1.0").fark)} at Dirichlet 1.0 and +${nf(100 * px("Dirichlet=0.1").fark)} at Dirichlet 0.1 (in the last case better in only ${seedsOf(px("Dirichlet=0.1").a_buyuk)}; additional test p = ${pv(px("Dirichlet=0.1").p)}). Only μ = 0.01 was tested.`));
  C.push(...flFull("F3", "All federated, central and local models, 53 features (mean over 10 seeds; ± standard deviation)", "flfull53"));
  const v3 = vh["F3|IID|yakinsama_kalici"], v4 = vh["F4|IID|yakinsama_kalici"];
  C.push(P(`**Convergence.** In IID, the P3 and P4 runs stopped at the cap of 300 rounds (1,500 epochs) in all 10 seeds. According to the validation losses recorded in every round, none of the ${V.valhist_all_cap.n} federated runs that reached the cap had fallen below the convergence threshold: the improvement over the last 50 epochs was ${pc(v3.r10_min, 2)}–${pc(v3.r10_max, 2)} for 53 features and ${pc(v4.r10_min, 2)}–${pc(v4.r10_max, 2)} for 21 features (threshold 0.5%). These models are therefore referred to as “trained until the cap”; whether the small remaining IID gap would close with longer training cannot be determined from these experiments.`));
  C.push(...figure("val_hist.png", "Best validation loss of the P3 and P4 runs on the IID split (each line is one seed). The curves are still decreasing at the 1,500-epoch cap.", 6.5, { key: "valhist" }));
  C.push(P(`**Summary for federated learning.** The main reason why the federated model appears weaker is insufficient training: an equal number of epochs means ~4 times fewer update steps for the clients, and an Adam state reset in every round slows training down. Under equivalent conditions in IID, the ANOMALY gap is no longer significant (${pc(fl("F3", KPOOL, "IID", FA("yakinsama_kalici")).ano)} / ${pc(F3m.ano)}), while a small gap of ${pt(kY.fark)} points remains in missed attacks. Under strong non-IID partitions there is a real gap, and FedProx (μ = 0.01) does not close it. In the 21-feature model, no gap arises at all (Section 6.10).`));

  // ---------------- 6.6
  C.push(H2("6.6 Calibration in federated learning and local-only models"));
  const w01 = PROT.map((p) => fl("F3", KPOOL, "Dirichlet=0.1", FA(p)));
  const y01a = own("F3", "yerel|Dirichlet=0.1|görülmemiş_ANOMALY");
  C.push(P(`Pooled calibration keeps the weighted FPR around α (0.6–1.1%), but at Dirichlet 0.1 the FPR of the worst client of the federated models is ${pc(Math.min(...w01.map((r) => r.fpr_worst)))}–${pc(Math.max(...w01.map((r) => r.fpr_worst)))} on average and ${pc(Math.max(...w01.map((r) => r.fpr_worst_max)))} in the worst seed. These clients are very small (only 4 normal test vectors in one seed). Per-client calibration keeps the worst client at ≤ 2.2% for the federated models but reduces detection. With this calibration, under strong non-IID partitions, the per-client local-only models outperform FedAvg: unseen ANOMALY ${pc(fl("F3", KCLIENT, "Dirichlet=0.1", KLOCAL).ano)} (local only) versus ${pc(fl("F3", KCLIENT, "Dirichlet=0.1", FA("yakinsama_kalici")).ano)} (FedAvg P3) (in ${seedsOf(y01a.a_buyuk)}; additional test p = ${pv(y01a.p)}), missed ${pc(fl("F3", KCLIENT, "Dirichlet=0.1", KLOCAL).kac)} versus ${pc(fl("F3", KCLIENT, "Dirichlet=0.1", FA("yakinsama_kalici")).kac)}. In IID, by contrast, FedAvg misses fewer attacks. Detailed results for every seed, model, split, calibration and client are available in the per-client result files of the output folders (53- and 21-feature models); the worst client is summarised here.`));

  // ---------------- 6.7
  C.push(H2("6.7 TinyML and threshold validity in INT8"));
  const i4d = i8("F4", "Merkezi AE", "INT8 skor + devralınan FP32 eşik"), i4r = i8("F4", "Merkezi AE", "INT8 skor + INT8 yeniden kalibrasyon"), i4f = i8("F4", "Merkezi AE", "FP32 skor + FP32 eşik");
  const i3d = i8("F3", "Merkezi AE", "INT8 skor + devralınan FP32 eşik"), i3r = i8("F3", "Merkezi AE", "INT8 skor + INT8 yeniden kalibrasyon"), i3f = i8("F3", "Merkezi AE", "FP32 skor + FP32 eşik");
  C.push(P(`The INT8 model occupies ${nf(tinyC("F3").tflite_int8_KB)} KB for 53 features (FP32 TFLite: ${nf(tinyC("F3").tflite_fp32_KB)} KB) and ${nf(tinyC("F4").tflite_int8_KB)} KB for 21 features; the rough RAM estimates are ${nf(tinyC("F3").tahmini_RAM_KB_int8)} and ${nf(tinyC("F4").tahmini_RAM_KB_int8)} KB. These values are below the RAM of typical TinyML microcontrollers, which ranges from tens to a few hundred KB [@banbury2021mlperftiny]; however, the estimate does not include the TFLite Micro working area. Latency was measured on the Colab CPU (INT8 ≈ ${nf(tinyC("F3").gecikme_int8_µs_colab, 2)} µs); it is not a microcontroller value.`));
  C.push(...tinyTab());
  C.push(...table(["Central AE", "53 feat.: FPR", "53 feat.: normal UNCERTAIN", "21 feat.: FPR", "21 feat.: normal UNCERTAIN"], [
    ["FP32 score + FP32 threshold", pc(i3f.fpr, 2), pc(i3f.unc), pc(i4f.fpr, 2), pc(i4f.unc)],
    ["INT8 score + inherited FP32 threshold", `${pc(i3d.fpr, 2)} (max ${pc(i3d.fpr_max, 2)})`, `${pc(i3d.unc)} (${pc(i3d.unc_min)}–${pc(i3d.unc_max)})`, `**${pc(i4d.fpr, 2)}** (max ${pc(i4d.fpr_max, 2)})`, `**${pc(i4d.unc)}** (${pc(i4d.unc_min)}–${pc(i4d.unc_max)})`],
    ["INT8 score + recalibration with INT8", pc(i3r.fpr, 2), pc(i3r.unc), pc(i4r.fpr, 2), pc(i4r.unc)],
  ], [2838, 1500, 1900, 1500, 1900], "Validity of FP32-computed thresholds in the INT8 model (10 seeds; target FPR ≤ 1%, UNCERTAIN ≈ 4%)", { key: "int8" }));
  C.push(...figure("int8_esik.png", "UNCERTAIN rate on normal traffic, each dot is one seed (central model). Dashed line: β = 4%.", 5.8, { key: "int8" }));
  const kq = V.own_device.kac_int8_eksi_fp32_cihaz;
  C.push(P(`The FP32 thresholds remained valid for ANOMALY in the 53-feature model, but the UNCERTAIN band shifted (${pc(i3f.unc)} → ${pc(i3d.unc)}). In the 21-feature model both thresholds broke: the false-alarm rate exceeded α and most of the normal traffic fell into UNCERTAIN. Recalibration with INT8 scores restored the budget in both models; the cost is an increase of ${pt(kq.fark)} points in the missed-attack rate of the device model (in ${seedsOf(kq.a_buyuk)}; additional test p = ${pv(kq.p)}). The FedAvg-IID models were less affected by INT8. For the central model, the rank correlation (Spearman) between FP32 and INT8 scores on normal traffic is ${nf(tinyC("F3").Spearman_FP32_INT8, 2)} for 53 features and ${nf(tinyC("F4").Spearman_FP32_INT8, 2)} for 21 features.`));

  // ---------------- 6.8
  C.push(H2("6.8 Corrupted input"));
  const RB = [["temiz", 0, "clean"], ["gürültü", 0.01, "noise σ = 0.01"], ["gürültü", 0.05, "noise σ = 0.05"], ["gürültü", 0.1, "noise σ = 0.10"],
    ["eksik", 0.05, "5% missing features"], ["eksik", 0.2, "20% missing features"], ["bozuk özellik", 1, "1 corrupted feature"], ["bozuk özellik", 5, "5 corrupted features"]];
  const rbRow = (b, l, lab) => { const lv = b === "bozuk özellik" ? `${l}.0` : (l === 0 ? "0.0" : String(l));
    const d3 = rb("F3", b, lv, "devralınan eşik"), r3 = rb("F3", b, lv, "yeniden kalibrasyon"), d4 = rb("F4", b, lv, "devralınan eşik"), r4 = rb("F4", b, lv, "yeniden kalibrasyon");
    return [lab, pc(d3.fpr), `${pc(r3.fpr)} / ${pc(r3.kac)}`, pc(d4.fpr), `${pc(r4.fpr)} / ${pc(r4.kac)}`]; };
  C.push(...table(["Corruption", "53 feat.: inherited threshold FPR", "53 feat.: recalibrated FPR / missed", "21 feat.: inherited threshold FPR", "21 feat.: recalibrated FPR / missed"],
    RB.map(([b, l, lab]) => rbRow(b, l, lab)), [2038, 1700, 2000, 1900, 2000], "Central AE under corrupted input (10 seeds × 3 repetitions)", { key: "robfpr" }));
  C.push(...robTab("F3", "F1, coverage and selective risk under corrupted input, 53-feature central AE", "rob53"));
  C.push(...robTab("F4", "F1, coverage and selective risk under corrupted input, 21-feature central AE", "rob21"));
  C.push(P("The inherited threshold breaks down even under small corruptions; the device model is more sensitive to noise. Recalibration with normal data subjected to the same corruption brings the false-alarm rate back to around 1%, but in that case most attacks are missed. Recalibration restores the guarantee, not the detection; moreover, normal data subjected to the same corruption may not always be available in the field."));

  // ---------------- 6.9
  C.push(H2("6.9 Ablation and risk–coverage for all models"));
  const AB = [["A1 · Isolation Forest", "A1 · Isolation Forest"], ["A2 · AE (ikili)", "A2 · AE (binary)"], ["A3 · AE + seçici", "A3 · AE + three-way"],
    ["A3q · INT8 AE + seçici (merkezi)", "A3q · INT8 AE + three-way"], ["A5 · Federe AE + seçici · orijinal", "A5 · FedAvg P1 + three-way"],
    ["A5 · Federe AE + seçici · orijinal_kucuk_yigin", "A5 · FedAvg P2 + three-way"], ["A4 · Federe AE (ikili) · yakinsama_kalici", "A4 · FedAvg P3, binary"],
    ["A5 · Federe AE + seçici · yakinsama_kalici", "A5 · FedAvg P3 + three-way"], ["A6 · INT8 Federe AE + seçici · yakinsama_kalici", "A6 · INT8 FedAvg P3 + three-way"],
    ["A5 · Federe AE + seçici · fedprox_kalici", "A5 · FedProx P4 + three-way"]];
  const abRow = (k, key, lab) => { const g2 = (m) => ab(k, key, m); if (!g2("normal_FPR")) return null;
    return [lab, pc(g2("normal_FPR").m, 2), SD(g2("recall_görülmemiş").m, g2("recall_görülmemiş").sd), SD(g2("görülmemiş_kaçan").m, g2("görülmemiş_kaçan").sd), g2("f1_görülmemiş") && g2("f1_görülmemiş").m !== null ? nf(g2("f1_görülmemiş").m, 3) : "—",
      nf(g2("coverage").m, 3), nf(g2("selective_risk").m, 3), nf(g2("selective_risk_π=%1").m, 4)]; };
  const hdr = ["Configuration (FL: IID)", "FPR", "Recall (unseen)", "Missed", "F1", "Coverage", "Selective risk", "Selective risk π = 1%"], wd = [3238, 800, 1000, 800, 700, 900, 1000, 1200];
  C.push(...table(hdr, AB.map(([k, l]) => abRow("F3", k, l)).filter(Boolean), wd, "Ablation, 53-feature models, mean over 10 seeds (± standard deviation)", { key: "abl53", note: "Recall = ANOMALY rate on unseen attacks. Selective risk is given on the test set and re-weighted to an attack share of 1%." }));
  C.push(...table(hdr, AB.map(([k, l]) => abRow("F4", k, l)).filter(Boolean), wd, "Ablation, 21-feature models, mean over 10 seeds (± standard deviation; Isolation Forest was not run for the 21-feature set)", { key: "abl21" }));
  const a23 = V.F3.abl_tests["A3 · AE + seçici||A2 · AE (ikili)||selective_risk"];
  C.push(P(`The three-way rule (deferral through UNCERTAIN) reduced the selective risk in 10 of 10 seeds for all AE-based models with 53 and 21 features (e.g. for the central AE, ${nf(ab("F3", "A2 · AE (ikili)", "selective_risk").m, 3)} → ${nf(ab("F3", "A3 · AE + seçici", "selective_risk").m, 3)}; p_Holm = ${pv(a23.p_holm)}). For the 53-feature models, INT8 conversion (A3 → A3q, A5 → A6) did not change the results significantly; the effect on the 21-feature device model is reported in Section 6.7. Isolation Forest flagged no attack at the 1% budget and produced ${pc(V.F3.iforest_fpr.min, 2)}–${pc(V.F3.iforest_fpr.max, 2)} false alarms on normal traffic. The selective risk is high on the test set because attacks are the majority and attacks that look normal receive a “confident” NORMAL decision; when re-weighted to an attack share of 1%, the selective risks of the AE-based models converge to approximately the range 0.010–0.019.`));
  C.push(...rcTab("F3", "Risk–coverage: selective risk at fixed coverage levels for all 53-feature models (10 seeds)", "rc53"));
  C.push(...rcTab("F4", "Risk–coverage: selective risk at fixed coverage levels for all 21-feature models (10 seeds)", "rc21"));
  C.push(...figure("risk_kapsama.png", "Risk–coverage curves (α fixed, β swept; test set; mean over 10 seeds). The federated models are from the IID split.", 6.5, { key: "rc" }));

  // ---------------- 6.10
  C.push(H2("6.10 The 21-feature device model: federated learning and INT8"));
  const cDev = V.F4.cihaz_tumu;
  const dAno = cDev["A3 · AE + seçici | cihaz||görülmemiş_ANOMALY"], dBil = cDev["A3 · AE + seçici | cihaz||bilinen_ANOMALY"], dSr = cDev["A3 · AE + seçici | cihaz||selective_risk"];
  const dKac = V.own_device.kac_cihaz_eksi_tumu;
  C.push(P("All experiments of Sections 6.5–6.9 were also run for the 21-feature device model, with the same rows, the same code and the same protocols."));
  C.push(...table(["Measure (central AE + three-way)", "53 features", "21 features", "Difference"], [
    ["Parameters", th(V.F3.tiny["Merkezi AE"].parametre), th(V.F4.tiny["Merkezi AE"].parametre), ""],
    ["TFLite INT8 / FP32 (KB)", `${nf(tinyC("F3").tflite_int8_KB)} / ${nf(tinyC("F3").tflite_fp32_KB)}`, `${nf(tinyC("F4").tflite_int8_KB)} / ${nf(tinyC("F4").tflite_fp32_KB)}`, ""],
    ["Unseen ANOMALY", pc(ab("F3", "A3 · AE + seçici", "görülmemiş_ANOMALY").m), pc(ab("F4", "A3 · AE + seçici", "görülmemiş_ANOMALY").m), `+${pt(dAno.fark)} points, ${dAno.a_buyuk}/10, p_Holm = ${pv(dAno.p_holm)}`],
    ["Unseen missed", pc(ab("F3", "A3 · AE + seçici", "görülmemiş_kaçan").m), pc(ab("F4", "A3 · AE + seçici", "görülmemiş_kaçan").m), `+${pt(dKac.fark)} points, ${dKac.a_buyuk}/10, additional test p = ${pv(dKac.p)}`],
    ["Known ANOMALY", pc(ab("F3", "A3 · AE + seçici", "bilinen_ANOMALY").m), pc(ab("F4", "A3 · AE + seçici", "bilinen_ANOMALY").m), `+${pt(dBil.fark)} points, ${dBil.a_buyuk}/10, p_Holm = ${pv(dBil.p_holm)}`],
    ["Normal FPR", pc(ab("F3", "A3 · AE + seçici", "normal_FPR").m, 2), pc(ab("F4", "A3 · AE + seçici", "normal_FPR").m, 2), "not significant"],
    ["Selective risk (test set)", nf(ab("F3", "A3 · AE + seçici", "selective_risk").m, 3), nf(ab("F4", "A3 · AE + seçici", "selective_risk").m, 3), `${nf(dSr.fark, 3)}, ${10 - dSr.a_buyuk}/10 lower, p_Holm = ${pv(dSr.p_holm)}`],
  ], [3000, 1700, 1700, 3238], "Central models with 53 and 21 features (10 seeds)", { key: "device" }));
  const t4max = Math.max(...SCN.flatMap((s) => PROT.map((p) => t4(s, p).p_holm)));
  const t4min = Math.min(...SCN.flatMap((s) => PROT.map((p) => t4(s, p).p_holm)));
  C.push(P(`Despite being smaller, the device model is not worse on unseen attacks: it flags more attacks as ANOMALY and defers fewer, and the missed rates are close. **In federated learning, there is no significant difference in unseen ANOMALY between the central and federated models under any condition** (12 comparisons, p_Holm ${nf(t4min, 2)}–${nf(t4max, 2)}; ${figRef("flcentral")}, right): even P1 gives the same result as the central model (IID: ${pc(fl("F4", KPOOL, "IID", FA("orijinal")).ano)} / ${pc(F4m.ano)}), and at Dirichlet 0.1 the federated models reach ${pc(Math.min(...PROT.map((p) => fl("F4", KPOOL, "Dirichlet=0.1", FA(p)).ano)))}–${pc(Math.max(...PROT.map((p) => fl("F4", KPOOL, "Dirichlet=0.1", FA(p)).ano)))}. A gap appears only on the known families. The validation loss of the device model is very low under all protocols, which suggests that the learning problem is easier and that few steps suffice (not tested separately). In INT8, by contrast, recalibration of the thresholds is mandatory (Section 6.7). Note: with these 21 features, ${pc(V.F4.seen.benign_test)} of the normal test vectors are identical to a vector in the training data; the effect of this on the FPR was not measured.`));
  C.push(...flFull("F4", "All federated, central and local models, 21 features (mean over 10 seeds; ± standard deviation)", "flfull21"));

  // ---------------- 6.11
  C.push(H2("6.11 Leaving out each attack family in turn (LOFO)"));
  C.push(P(`To ensure that the “unseen attack” claim does not depend on the three chosen families, each family was left out in turn following a pre-registered design: 9 folds, in each of which one family is unseen and the other eight are known; 10 separate seeds (10–19). Since the AE is trained on normal traffic only, its result does not change across folds; what changes is the RF trained on the other eight families. All 10 AEs stopped by the convergence rule (${V.F2.ae_epoch[0]}–${th(V.F2.ae_epoch[1])} epochs).`));
  C.push(P("**Success criterion (pre-registered):** AE + host counter must reduce the “missed + deferred” rate at ρ = 1 by at least 30 points while the worst normal host stays within the weekly budget, and this must hold in at least 6 of the 9 folds. **Failure criterion:** if, for families that are dissimilar to the known ones (RF recall < 0.50), the RF alone matches AE + counter (difference ≤ 0.05), the “normal traffic only” claim is withdrawn."));
  C.push(...table(["W (flows)", "F = 1,000 flows/day", "F = 5,000 flows/day", "Criterion"],
    [20, 50, 100].map((W) => [String(W), `${f2ok(W, 1000).başarılı_katman} / 9`, `${f2ok(W, 5000).başarılı_katman} / 9`,
      f2ok(W, 1000).başarı_ölçütü_sağlandı && f2ok(W, 5000).başarı_ölçütü_sağlandı ? "met" : "**not met**"]),
    [1800, 2600, 2600, 2638], "Number of folds meeting the LOFO success criterion (10 seeds)", { key: "lofo" }));
  C.push(...figure("lofo.png", "W = 50, F = 1,000 flows/day: single-flow ANOMALY rate of the AE on the left-out family, single-flow recall of the RF trained on the other eight families, and host detection by AE + host counter at ρ = 1 (10 seeds).", 6.5, { key: "lofo" }));
  const fam = V.F2.aile_W50_F1000, rfr = minmax(fam.map((r) => r["RF_tek_recall_α"]));
  const inj = fam.find((r) => r.aile === "injection"), ddos = fam.find((r) => r.aile === "ddos");
  C.push(B("**At W = 20 the criterion was not met:** in every seed, a single normal host was escalated in every window (350 false escalations per week, budget 1)."));
  C.push(B(`**ddos was not counted as a success in any setting;** the reason is a ceiling effect: since the AE already gives ${pc(ddos.AE_ANOMALY)} ANOMALY on single flows, an improvement of 30 points is not possible. The weakest family is injection (host detection ${pc(inj["karisik_ρ=1.00"])} at W = 50, F = 1,000, ρ = 1).`));
  C.push(B(`**The failure criterion could not be tested:** the RF detected each left-out family at rates of ${pc(rfr[0])}–${pc(rfr[1])}; by this definition, no family “dissimilar” to the known ones exists in TON_IoT. In addition, the RF reaches the level of AE + counter for backdoor, ransomware, scanning and injection.`));
  C.push(P("**Summary for LOFO.** The pre-registered success criterion was met at W = 50 and 100 and not met at W = 20. In TON_IoT, every family is sufficiently similar to the other eight; here, “unseen” means only “a family not used in training”, not “an attack dissimilar to the known ones”. This is a finding about the dataset, not a success or failure of the method; another dataset is required to demonstrate the value of learning from normal traffic alone for genuinely new attacks."));
}

// ======================================================================================
// Discussion / limitations / conclusion bodies (no headings; Turkish §6, §7, §8)
// ======================================================================================
function secDiscussionCore(C) {
  C.push(P("The main lesson drawn from the results is that the conformal threshold keeps the promised false-alarm rate under the condition in which it was computed and, instead of silently missing most new attacks, separates them into a distinct queue. This guarantee, however, does not transfer automatically to another condition: it broke under INT8 for the device model, for small clients under non-IID partitions, and under corrupted input. For IoT, this means that each device or client must validate its threshold under its own condition and recalibrate it if necessary."));
  C.push(P("Operationally, the hierarchical filter between the flow and host levels turns UNCERTAIN decisions from a burden on the analyst into evidence about the trustworthiness of hosts that can accumulate; this, however, works only when the attack makes up a substantial part of the traffic of the host. From the perspective of the edge node, the 21-feature device model provides at least the same detection without application-layer parsing, is unaffected by federated training, and its INT8 size is below the typical capacity of microcontrollers. In federated learning, a fair comparison requires equalising the number of update steps and the optimiser state rather than the number of epochs; under strong non-IID partitions, local models can outperform the federated model."));
}
function secLimitationsCore(C) {
  C.push(B("In TON_IoT, the “unseen” families resemble the known ones (Section 6.11). The value of learning from normal traffic alone for genuinely new attacks cannot be demonstrated with these data [@sommer2010]."));
  C.push(B("Most federated runs stopped at the 1,500-epoch cap while the validation loss was still decreasing; for FedProx, only μ = 0.01 was tested."));
  C.push(B("The FL clients are not real devices; the normal data were split across five clients according to the service column. At Dirichlet 0.1 some clients are very small, so the client FPRs are coarse."));
  C.push(B("The host-counter and sparse-attack experiments are simulations (the data contain no timestamps); the sparse-attack analysis was not pre-registered. The original counter only counts evidence within a window, with no update that discounts old evidence; Phase 10 evaluates such updates (Section 6.12.5)."));
  C.push(B("Latency was measured on the Colab CPU, and RAM is only a rough estimate; no measurement was made on a real microcontroller. The flow-extraction cost of the device feature set was not measured either."));
  C.push(B("Confidence intervals reflect training-seed variability only; the data split was kept fixed. No Holm correction was applied to the comparisons marked as “additional test”."));
}
function secConclusionCore(C) {
  C.push(P(`A three-way detector built from an AE with ${th(sl.ae_32_16_8.parametre)} parameters, trained on normal traffic only, and two conformal thresholds keeps the 1% false-alarm budget on normal traffic while flagging ${pc(F3m.ano)} of the unseen attack flows as immediate alarms, missing ${pc(F3m.kac)} and deferring the remainder; when the deferred flows are accumulated at the host level, hosts carrying dense attacks are detected. The system also operates in federated and INT8 form; however, the thresholds must be validated under every new condition.`));
  C.push(P("Future work:", { after: 60 }));
  C.push(B("Testing the unseen-attack claim on a second dataset (e.g. Edge-IIoTset)."));
  C.push(B("Continuing federated training without a cap until actual convergence; trying other μ values and client-specific layers for non-IID partitions."));
  C.push(B("Making post-INT8 recalibration a default step for the device model; measuring latency and memory on a real microcontroller."));
  C.push(B("Per-host (Mondrian) calibration, evidence decay and sequential accumulation for sparse attacks; these are evaluated in Phase 10 (Section 6.12)."));
}

// ======================================================================================
// Key numbers for the abstract (all from the same accessors; English formatting)
// ======================================================================================
const abstractCoreFacts = (() => {
  const P3 = (s) => fl("F3", KPOOL, s, FA("yakinsama_kalici"));
  const tY = t3("IID", "yakinsama_kalici"), tO = t3("IID", "orijinal"), kY = own("F3", "kac|IID|yakinsama_kalici");
  const i4d = i8("F4", "Merkezi AE", "INT8 skor + devralınan FP32 eşik"), i4r = i8("F4", "Merkezi AE", "INT8 skor + INT8 yeniden kalibrasyon");
  const kq = V.own_device.kac_int8_eksi_fp32_cihaz;
  const t4p = SCN.flatMap((s) => PROT.map((p) => t4(s, p).p_holm));
  const fam = V.F2.aile_W50_F1000, rfr = minmax(fam.map((r) => r["RF_tek_recall_α"]));
  const f = (value, desc) => ({ value, desc });
  return {
    aeParams: f(th(sl.ae_32_16_8.parametre), "Parameters of the 53-feature AE (53-32-16-8-16-32-53)."),
    normalAnomalyRate: f(pc(e1("ae", "ANOMALY").mean, 2), "AE ANOMALY rate on normal traffic over 200 calibration/test re-splits (budget 1%)."),
    normalUncertainRate: f(pc(e1("ae", "UNCERTAIN").mean, 2), "AE UNCERTAIN rate on normal traffic over 200 re-splits (budget 4.03%)."),
    centralUnseenAnomaly: f(pc(F3m.ano), "Central 53-feature AE: share of unseen-family flows (ransomware, xss, mitm) declared ANOMALY (vector level, pooled calibration, mean of 10 seeds)."),
    centralUnseenUncertain: f(pc(ab("F3", "A3 · AE + seçici", "görülmemiş_UNCERTAIN").m), "Central 53-feature AE: share of unseen-family flows declared UNCERTAIN (ablation A3, 10 seeds)."),
    centralUnseenMissed: f(pc(F3m.kac), "Central 53-feature AE: share of unseen-family flows declared NORMAL (missed)."),
    alarmPrecision1pct: f(pc(tierU("three-way α=0.01, β=0.04").precision_alarm_tier), "Precision of immediate alarms (three-way rule, unseen families) re-weighted to a 1% attack share."),
    hostDenseW50: f("100%", "Escalation of hosts whose traffic is entirely malicious at W ≥ 50 (stated in the text of Section 6.4, simulation)."),
    hostSparseMax: f(pc(f5(200, 0.1).pencere_tespit_mean), "Maximum host-window detection when attack flows are 10% of the window (W = 200, simulation); 0% at ρ ≤ 5%."),
    flP1IID: f(pc(fl("F3", KPOOL, "IID", FA("orijinal")).ano), `FedAvg P1 (40 rounds × 5 epochs, Adam reset), IID, unseen ANOMALY; central higher in ${tO.a_buyuk}/10 seeds, p_Holm = ${pv(tO.p_holm)}.`),
    flP3IID: f(pc(P3("IID").ano), `FedAvg P3 (until the 1,500-epoch cap, Adam kept), IID, unseen ANOMALY vs central ${pc(F3m.ano)}; gap ${pt(tY.fark)} points, p_Holm = ${pv(tY.p_holm)} (not significant).`),
    flP3IIDMissedGap: f(`${pt(kY.fark)} points`, `Higher missed rate of FedAvg P3 vs central in IID (${kY.a_buyuk}/10 seeds; additional test p = ${pv(kY.p)}, no Holm correction).`),
    flP3Dir1: f(pc(P3("Dirichlet=1.0").ano), `FedAvg P3 at Dirichlet 1.0, unseen ANOMALY (p_Holm = ${pv(t3("Dirichlet=1.0", "yakinsama_kalici").p_holm)}).`),
    flP3Dir01: f(pc(P3("Dirichlet=0.1").ano), `FedAvg P3 at Dirichlet 0.1, unseen ANOMALY (p_Holm = ${pv(t3("Dirichlet=0.1", "yakinsama_kalici").p_holm)}).`),
    flCapCaveat: f(`${V.valhist_all_cap.n} runs`, "Federated runs that reached the 1,500-epoch cap; none had fallen below the convergence threshold (still improving). FedProx tested only with μ = 0.01."),
    int8SizeKB53: f(`${nf(tinyC("F3").tflite_int8_KB)} KB`, "TFLite INT8 size of the central 53-feature AE (rough RAM estimate " + nf(tinyC("F3").tahmini_RAM_KB_int8) + " KB, excluding the TFLite Micro working area)."),
    int8SizeKB21: f(`${nf(tinyC("F4").tflite_int8_KB)} KB`, "TFLite INT8 size of the central 21-feature device AE (rough RAM estimate " + nf(tinyC("F4").tahmini_RAM_KB_int8) + " KB)."),
    int8DeviceInheritedFPR: f(pc(i4d.fpr, 2), `21-feature AE, INT8 score with inherited FP32 threshold: normal FPR (normal UNCERTAIN ${pc(i4d.unc)}); thresholds break.`),
    int8DeviceRecalFPR: f(pc(i4r.fpr, 2), `21-feature AE after INT8 recalibration: normal FPR (normal UNCERTAIN ${pc(i4r.unc)}).`),
    int8DeviceRecalMissedCost: f(`${pt(kq.fark)} points`, `Increase in missed rate of the device model after INT8 recalibration (${kq.a_buyuk}/10 seeds; additional test p = ${pv(kq.p)}).`),
    int8LatencyNote: f(`${nf(tinyC("F3").gecikme_int8_µs_colab, 2)} µs`, "INT8 latency of the central 53-feature AE measured on the Colab CPU (not a microcontroller value)."),
    deviceUnseenAnomaly: f(pc(F4m.ano), "Central 21-feature device AE: unseen ANOMALY (pooled calibration, 10 seeds)."),
    deviceUnseenMissed: f(pc(F4m.kac), "Central 21-feature device AE: unseen missed."),
    deviceFLpHolmRange: f(`${nf(Math.min(...t4p), 2)}–${nf(Math.max(...t4p), 2)}`, "p_Holm range of the 12 central-vs-federated comparisons for the device model (no significant difference)."),
    lofoFoldsW20: f(`${f2ok(20, 1000).başarılı_katman} / 9`, "LOFO folds meeting the pre-registered success criterion at W = 20, F = 1,000 (criterion not met)."),
    lofoFoldsW50: f(`${f2ok(50, 1000).başarılı_katman} / 9`, "LOFO folds meeting the success criterion at W = 50, F = 1,000."),
    lofoFoldsW100: f(`${f2ok(100, 1000).başarılı_katman} / 9`, "LOFO folds meeting the success criterion at W = 100, F = 1,000."),
    lofoRFRecallRange: f(`${pc(rfr[0])}–${pc(rfr[1])}`, "Single-flow recall of an RF trained on the other eight families, on each left-out family (failure criterion untestable; 'unseen' families resemble known ones)."),
  };
})();
// ======================================================================================
// Phase 10 — method section (English). Uses helpers from _head_en.js (P, H1, H2, B, EQ, table, figure).
// No result numbers here; results come from p10_values.json in _p10_results_en.js.
// ======================================================================================
function secPhase10Method(C) {
  C.push(H1("4. Phase 10: Host-Level Evidence Accumulation and Mathematical Formulation"));
  C.push(P("The framework of Section 3 escalates a host when the number of its flows with p ≤ α + β inside a window of W flows reaches a calibrated count k*. This rule is reported in Section 6.4: it does not detect sparse attacks, in which only a small share ρ of a host's flows are malicious. Phase 10 asks whether a different host-level rule can do better **without** changing the autoencoder, its conformal calibration, the federated training or the TinyML deployment, and **at the same false-escalation budget**. Every rule below is a function of the per-flow conformal p-values that the framework already produces. Most of the ingredients are established techniques; Sections 2.7 and 7 discuss which parts, if any, are new."));

  C.push(H2("4.1 Setting and operational constraint"));
  C.push(P("A host h emits flows x₁, x₂, …. For each flow the detector computes the conformal p-value pₜ = (1 + #{i ≤ n : sᵢ ≥ s(xₜ)}) / (n + 1) against the n benign calibration scores [@vovk2005alrw,bates2023outliers]. If the flow is benign and exchangeable with the calibration flows, pₜ is super-uniform: P(pₜ ≤ u) ≤ u for all u ∈ [0, 1]. A host-level rule maps the sequence (pₜ) of one host to escalation decisions. Its cost is the number of **false escalations per host per week** on benign hosts, and the operational budget is B = 1 false escalation per host per week at a traffic level of F flows per day. For a window rule that decides once every W flows, this budget is a per-window false-escalation probability α_W = B·W / (7F); for a sequential rule that decides after every flow, it is a false-alarm rate of B / (7F) per benign flow, i.e. an average run length to false alarm of at least 7F/B flows. Both forms describe the same weekly budget, which makes the rules comparable."));

  C.push(H2("4.2 Host-conditional p-values"));
  C.push(P("The conformal guarantee is marginal over the benign population that generated the calibration set. Individual hosts need not be exchangeable with that population: Section 6.12 shows benign hosts whose flows fall at p ≤ 0.05 far more often than the nominal 5% (more than twice as often on average for one host), while most hosts fall there far less often. A rule calibrated on pooled benign traffic must then accommodate the noisiest host, which wastes power on all quiet hosts and still violates the budget on the noisy one. Following the Mondrian (category-conditional) construction of conformal prediction [@vovk2005alrw], Phase 10 adds a second p-value against the host's own benign reference flows R_h:"));
  C.push(EQ("p_host(x) = (1 + #{j ∈ R_h : p_j ≤ p(x)}) / (|R_h| + 1),     p′(x) = max{ p(x), p_host(x) }."));
  C.push(P("**Proposition 1 (validity of the maximum).** If either p(x) or p_host(x) is super-uniform for benign flows of host h, then p′(x) is super-uniform, because P(max{p, p_host} ≤ u) ≤ min{P(p ≤ u), P(p_host ≤ u)} ≤ u. The argument is elementary; merging p-values through order statistics is studied in general by Vovk and Wang [@vovk2020combining]. p′ is therefore valid if the host's benign traffic is exchangeable with the pooled calibration set **or** with its own reference, a weaker requirement than either alone. Its price is conservativeness: p′ can never be smaller than the pooled p-value."));
  C.push(P("R_h consists of the host's benign_val flows. To avoid in-sample optimism, the benign_val flows of each host are split into two folds; a benign_val flow is referenced against the other fold, and every other flow against fold 0. A host with fewer than 20 reference flows per fold cannot be given a meaningful own reference; all such low-traffic hosts share one reference category built from their pooled benign_val flows, which is again a Mondrian taxonomy. Only benign_val data enter R_h."));

  C.push(H2("4.3 Per-flow e-values for a sparse-mixture alternative"));
  C.push(P("Counting p ≤ α + β gives the same weight to every flagged flow, and Fisher-type statistics weigh every flow on the same scale. Phase 10 instead converts each p-value into an e-value [@vovk2021evalues], a non-negative statistic e with E[e] ≤ 1 under the null, tuned to the alternative of interest. Under a sparse attack, a share ρ of a host's flows are attack flows whose p-values have a density q, and the rest are benign with a (super-)uniform density f₀. The likelihood ratio of one flow is then"));
  C.push(EQ("e_ρ₀(p) = (1 − ρ₀) + ρ₀ · r(p),     r(p) = q(p) / f₀(p),"));
  C.push(P("evaluated at a design share ρ₀. For a known q this is the Neyman–Pearson optimal per-flow evidence for the mixture. Because attacks of the target families are by definition unavailable, q is estimated from the p-values of the six **known** families on the dev_val split (equal weight per family; the held-out families are never used). The estimate is binned on twelve fixed p-value bins with upper edges 1/(n + 1), 0.001, 0.002, 0.005, 0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.5 and 1. f₀,b is the exact null probability of bin b for a conformal p-value with n calibration points, ⌊e_b(n + 1)⌋/(n + 1) − ⌊e_{b−1}(n + 1)⌋/(n + 1). The ratio r_b = q_b / f₀,b is made non-increasing by weighted isotonic regression, which preserves Σ_b f₀,b r_b = 1, and q is mixed with 1% of f₀ so that r_b > 0. In the fitted ratios, the isotonic step made r constant for all p ≤ 0.02 in every seed (up to 0.03 or 0.05 in three seeds), so in practice the e-value distinguishes three or four p-value regions rather than the smallest p-values individually."));
  C.push(P("**Proposition 2 (e-validity).** If r is non-increasing in p and Σ_b f₀,b r_b = 1, then E[e_ρ₀(p)] ≤ 1 for every super-uniform conformal p-value: a non-increasing function has its largest expectation under the stochastically smallest admissible distribution, the discrete uniform, under which E[r(p)] = 1. For the host-conditional p′, which lives on a different grid, the argument holds against the continuous uniform distribution, for which E[r(U)] = Σ_b r_b·(e_b − e_{b−1}); with the fitted ratios this exceeds 1 by at most 0.0074 over the ten seeds, so e is valid up to that discretisation term. A benign-only alternative, which uses no attack data at all, replaces r by the mixture calibrator f(p) = (1 − p + p ln p) / (p ln² p) of Vovk and Wang [@vovk2021evalues]."));

  C.push(H2("4.4 Accumulators and the host trust score"));
  C.push(P("Let ℓₜ = log e_ρ₀(pₜ) (or log e_ρ₀(p′ₜ) with the host-conditional reference). Phase 10 evaluates two families of accumulators:"));
  C.push(B("**Window evidence** (W_EVID): Λ_W = Σ ℓₜ over the W flows of a window; escalate if Λ_W ≥ c_W. This is the log of a product of e-values over the window; it is analogous to a conformal test martingale [@vovk2003exchangeability,fedorova2012plugin], but the p-values are computed against a fixed calibration set rather than online."));
  C.push(B("**e-CUSUM**: Sₜ = max{0, Sₜ₋₁ + ℓₜ}; escalate if Sₜ ≥ h and restart at 0. With likelihood-ratio increments this is Page's CUSUM [@page1954], which is minimax-optimal for detecting a change between known distributions [@lorden1971,moustakides1986]; with e-value increments it is the CUSUM e-detector of Shin, Ramdas and Rinaldo [@shin2024edetectors]."));
  C.push(B("**e-Shiryaev–Roberts** (e-SR): Rₜ = (1 + Rₜ₋₁)·e_ρ₀(pₜ); escalate if Rₜ ≥ A [@shiryaev1963,roberts1966]. Under independent super-uniform p-values its average run length to false alarm is at least A [@shin2024edetectors]."));
  C.push(B("**Evidence decay** (leaky e-CUSUM): Sₜ = max{0, γSₜ₋₁ + ℓₜ} with γ = 1 − 2/(W + 1), so that evidence older than about W flows fades, the exponential counterpart of a window."));
  C.push(B("**Adaptive accumulation** (adaptive e-SR): the average of e-SR procedures over ρ₀ ∈ {0.01, 0.02, 0.05, 0.10, 0.25, 0.50}. An average of e-detectors is an e-detector, so no single design share has to be chosen."));
  C.push(P("A host trust score in (0, 1] follows directly as τₜ = exp(−Sₜ) for CUSUM-type rules (τₜ = 1 / (1 + Rₜ) for SR-type rules, and exp(−max{0, Λ_W}) for the window rule): it falls as evidence against the host accumulates, and escalation happens when it crosses a calibrated level. The score is a monotone re-expression of the statistic, not an additional mechanism."));

  C.push(H2("4.5 Baselines"));
  C.push(P("All baselines use the same p-values (pooled or host-conditional) and the same budget:"));
  C.push(B("the existing counter of Section 3.3 (count of p ≤ α + β) and a count of p ≤ α;"));
  C.push(B("classical p-value combinations over the window: Fisher's −Σ log p, the truncated product with τ = α + β [@zaykin2002tpm], the minimum p-value (Tippett) and Higher Criticism HC⁺, which was designed for sparse heterogeneous mixtures [@donoho2004hc];"));
  C.push(B("sequential control charts: a Bernoulli CUSUM on the flag p ≤ α + β [@reynolds1999bernoulli], whose increments are the same likelihood ratio built on two bins instead of twelve (so it isolates the value of using the full p-value instead of a count); an EWMA chart on the flag [@roberts1959ewma,lucas1990ewma]; and an EWMA of −log p. Both EWMA charts use λ = 2/(W + 1)."));

  C.push(H2("4.6 Calibration to the operational budget"));
  C.push(P("Window rules are calibrated exactly as the existing counter: a split-conformal quantile of the statistic over 5,000 benign_val windows at level α_W, i.e. the smallest c with (1 + #{Λ_cal ≥ c}) / (n + 1) ≤ α_W. Sequential rules are calibrated by counting alarms with restart on 200 simulated benign_val host streams of 14 days each, choosing by bisection the smallest threshold with (alarms + 1) / flows × 7F ≤ B. Benign_test data are never used for calibration."));
  C.push(P("The e-detector bound offers a calibration-free alternative, A = 7F/B. Phase 10 reports it (the \"theory threshold\" rows) but does not rely on it. The bound needs the p-values of a benign host to be independent and super-uniform. Conformal p-values computed against one fixed calibration set are only conditionally independent, and their conditional validity holds approximately for large n [@bates2023outliers]. Real benign hosts are moreover not exchangeable with the calibration population (Section 6.12). The empirical calibration targets the operational quantity directly, and the theory threshold shows how far the assumptions are from holding."));

  C.push(H2("4.7 Computational cost"));
  C.push(P("Every Phase 10 rule needs O(1) work per flow. The p-value is mapped to one of twelve bins by a binary search over the bin edges, and the bin indexes a twelve-entry table of log e-values. CUSUM and SR keep one number per host; the window rule keeps a ring buffer of W bin indices (one byte each) and a running sum. The host-conditional reference does not require storing the reference flows on the device: for the binned rules only the bin of p′ matters, and it is fixed by eleven thresholds per host (one per inner bin edge) on the pooled p-value. Higher Criticism, Fisher and the minimum p-value need the W p-values themselves, and Higher Criticism sorts them once per window. Section 6.12 reports measured times and memory."));
}
// Phase 10 simulation protocol (subsection of Section 5). Numbers here are design constants, not results.
function secPhase10Setup(C, num) {
  C.push(H2(`${num} Phase 10 simulation protocol`));
  C.push(P("**Inputs.** Phase 10 reuses the saved per-seed autoencoder scores of the central model (seeds 0–9) and the map from raw TON_IoT rows to model vectors and source hosts. Nothing is retrained. The pooled conformal p-values are computed exactly as in Section 3.2. As a check, the stored sparse-attack evaluation of the existing counter (Section 6.4) was recomputed locally from the saved scores for all ten seeds; the largest absolute difference in any numeric column was 5.7 × 10⁻¹⁴."));
  C.push(P("**Simulated host streams.** Version B of TON_IoT has no timestamps, so a host stream is a random ordering of that host's flows, drawn with replacement (the windows used to calibrate and evaluate the window rules contain W distinct flows of one host, as in Section 6.4). This removes temporal dependence; every Phase 10 result is therefore a **simulation** of host-level monitoring, not a deployment measurement. An attacked stream consists of 1,000 benign warm-up flows of a benign_test host with at least W benign_test flows, chosen with probability proportional to its traffic, followed by an attack window of W ∈ {20, 50, 100, 200} flows. The window contains round(ρW) attack flows at random positions, with ρ ∈ {0.01, 0.05, 0.10, 0.25, 0.50}. Combinations with no attack flow (ρ = 0.01 with W < 100) are skipped, as in Section 6.4. Attack flows are drawn from the dev_test flows of each known family and the heldout_test flows of ransomware, xss and mitm, with 300 streams per family, ρ and W. The same streams are used for every method (common random numbers), so comparisons are paired."));
  C.push(P("**Outcomes.** A host is detected if the rule escalates it within the W flows of the attack window. Window rules see a window aligned with the attack onset and decide at its end, as in the original evaluation, which favours them; sequential rules start from the state reached after the warm-up and may escalate after any flow. The detection delay is the number of flows from onset to escalation among detected streams. Benign cost is the number of false escalations per host per week on benign_test hosts at F = 1000 and F = 5000 flows per day. For window rules it is estimated from 5,000 windows; for sequential rules from 12 streams of 14 days per host, with restart after each alarm. Three summaries are reported: the traffic-weighted mean over hosts, the worst host, and the number of hosts above the budget."));
  C.push(P("**Selection and freezing.** The configuration called P10 below was selected before any test-stage run of Phase 10. The selection rule was written down after the validation runs had started but before any test-stage run. Its design was not blind: before writing it, the per-family flow-level p-value rates (already reported in Sections 6.2–6.4), the earlier sparse-attack results and the per-host benign flag rates in benign_val and benign_test for two seeds had been inspected, and the latter motivated the host-conditional reference. A first smoke run also changed the calibration of the sequential rules; these deviations are logged with the protocol. The rule uses only benign_val streams and known-family attacks from one half of dev_val, with the likelihood ratio fitted on the other half. Its criterion is the mean known-family detection at ρ ∈ {0.05, 0.10}, averaged over W and seeds at F = 1000, subject to a validation false-escalation rate within the budget. The candidates were the window e-value rule, e-CUSUM, e-SR, leaky e-CUSUM and adaptive e-SR, each with both references and ρ₀ ∈ {0.01, 0.02, 0.05, 0.10, 0.25}. On the test stage the likelihood ratio is refitted on all of dev_val. The protocol, the selection output and every deviation are archived with the code."));
  C.push(P("**Computing environment.** Phase 10 ran on a local Windows laptop CPU (Python 3.12.1, NumPy 1.26.2, pandas 2.1.4, SciPy 1.11.4, numba-compiled kernels), one process per seed; no GPU and no retraining were involved."));
  C.push(P("**Statistics.** The primary comparison is P10 against the existing counter on unseen-family detection at F = 1000, for ρ ∈ {0.05, 0.10} and the four window sizes (eight paired comparisons over the ten seeds). It uses two-sided Wilcoxon signed-rank tests [@wilcoxon1945] with Holm correction [@holm1979], and reports mean differences with 95% percentile-bootstrap intervals over seeds. Comparisons against the other methods are secondary, Holm-corrected within each comparison. A method whose benign_test false escalations exceed the budget is reported as such, and its detection is not counted as an improvement."));
}
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
// Front matter, Introduction (Section 1) and Related Work (Section 2).
const ACF = abstractCoreFacts;
const fv = (k) => ACF[k].value;

function secTitle(C) {
  C.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600, after: 240 },
    children: [new TextRun({ text: "TrustFed-TinyIDS: Conformal Three-Way Decisions, Federated Training and Host-Level Evidence Accumulation for Unseen and Sparse Attacks in IoT Networks", bold: true, size: 34, color: NAVY })] }));
  C.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [new TextRun({ text: "Mohamed Mereyani", size: 24 })] }));
  C.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 }, children: [new TextRun({ text: "Department of Computer Engineering, Siirt University, Siirt, Türkiye", size: 20, color: MUTED })] }));
}

function secAbstract(C) {
  const p200a = prim10(200, 0.05), p200b = prim10(200, 0.10);
  const e200a = ex10(KEY_HCOUNT, KEY_EXIST, 200, 0.05, false), e200b = ex10(KEY_HCOUNT, KEY_EXIST, 200, 0.10, false);
  C.push(H1("Abstract"));
  C.push(P(`Intrusion detectors for IoT networks must flag attacks they were not trained on, keep false alarms within an operational budget, learn across heterogeneous sites and run on constrained devices. This paper studies these requirements jointly in TrustFed-TinyIDS, a framework built around an autoencoder trained only on benign traffic (${fv("aeParams")} parameters). Conformal p-values against held-out benign scores yield a three-way decision (NORMAL, UNCERTAIN, ANOMALY) with a finite-sample false-alarm guarantee for exchangeable benign traffic, and UNCERTAIN flows are resolved per host rather than discarded. On the TON_IoT network dataset with three attack families held out and ten seeds, the central model flags ${fv("centralUnseenAnomaly")} of unseen-family flows as ANOMALY and misses ${fv("centralUnseenMissed")}, at a benign ANOMALY rate of ${fv("normalAnomalyRate")}. A leave-one-family-out analysis shows that supervised models also recognise most held-out families (recall ${fv("lofoRFRecallRange")}), a limitation of the benchmark. Federated averaging initially appeared far weaker than central training (${fv("flP1IID")} versus ${fv("centralUnseenAnomaly")} under IID splits); with matched local training it reached ${fv("flP3IID")} (not significantly different), and a clear gap remained only under a strongly non-IID split (${fv("flP3Dir01")} at Dirichlet 0.1). INT8 quantisation preserved the ANOMALY level of the 53-feature model (its UNCERTAIN band drifted) but broke the inherited thresholds of a 21-feature device model (benign ANOMALY rate ${fv("int8DeviceInheritedFPR")}); recalibration restored it at a cost of ${fv("int8DeviceRecalMissedCost").replace(" points", "")} percentage points of missed attacks. A pre-specified extension (Phase 10) addressed sparse attacks, where the original host counter detected almost nothing below a 25% attack share. Host-conditional (Mondrian) conformal p-values combined with likelihood-ratio e-values raised simulated host-level detection at W = 200 flows from ${pc(p200a.existing_mean)} to ${pc(p200a.P10_mean)} at a 5% attack share and from ${pc(p200b.existing_mean)} to ${pc(p200b.P10_mean)} at 10%, but exceeded the false-escalation budget on test hosts, so the pre-specified hypothesis was not supported. Exploratory analyses traced the gain to the host-conditional reference rather than to evidence weighting or sequential accumulation (CUSUM, Shiryaev–Roberts, EWMA): applied to the existing count rule, it reached ${pc(e200a.A_mean)} and ${pc(e200b.A_mean)} within the mean budget. Host-level results are simulations on a dataset without timestamps. The contribution is a reproducible empirical assessment rather than a new detector.`));
  C.push(P("**Keywords:** IoT intrusion detection; conformal prediction; unseen attacks; federated learning; TinyML; sequential change detection; e-values; host trust."));
}

function secIntro(C) {
  C.push(H1("1. Introduction"));
  C.push(P("Networks of Internet of Things (IoT) devices combine large numbers of heterogeneous, weakly protected endpoints with limited computing resources, which makes them both attractive targets and difficult places to run intrusion detection. Machine-learning intrusion detection systems (IDS) for IoT have been surveyed extensively, from centralised deep models to federated and explainable designs [@arisdakessian2023survey,khraisat2025survey,hernandezramos2025intrusion]. Three properties separate a laboratory detector from one that can be relied upon in operation: it must react to attacks it has not seen, its false alarms must stay within what operators can process, and it must run where the data are — often on devices that cannot ship raw traffic to a central server."));
  C.push(P("**Unseen attacks.** Supervised classifiers learn the attack families present in their training data; their behaviour on new families is not controlled, a long-standing concern for machine learning in intrusion detection [@sommer2010outside,arp2022dos]. Open-set and zero-day detectors address this with reconstruction errors, energy scores or uncertainty estimates [@yang2025lightweight,yu2024deep,fawaz2026detecting], but their alarm thresholds are usually set heuristically. One-class detectors trained only on benign traffic, such as autoencoders [@mirsky2018kitsune,yao2023lightweight], do not depend on attack labels, yet they share the same thresholding problem."));
  C.push(P("**False alarms.** Conformal prediction converts any anomaly score into a p-value against held-out benign scores and gives a finite-sample bound on the false-alarm rate when benign traffic is exchangeable with the calibration data [@vovk2005algorithmic,bates2023testing,angelopoulos2023conformal]. Recent IDS work uses conformal calibration for per-flow alarms and reject options [@farsimadan2026confid,datta2026cassidy,massaad2026beyond,younas2026operationally]. Per-flow control has a cost: at a strict false-alarm level, a single flow rarely carries enough evidence. A recent open-world evaluation reports a mean unknown-alert detection of only about 30.6% for a benign-calibrated gate at 1% FPR [@younas2026operationally]. Evidence must therefore be aggregated, and the natural unit in an IoT network is the host. Aggregation brings its own risk. Low-rate and sparse attacks send only a few malicious flows among many benign ones [@kuzmanovic2003lowrate,rios2022detection], and a host-level rule must catch them without escalating benign hosts that merely look unusual."));
  C.push(P("**Federated heterogeneity.** Federated learning (FL) trains a shared model without moving raw traffic [@mcmahan2017communication]. IoT clients hold very different traffic, and non-IID data slow convergence and can bias the global model [@kairouz2021advances,li2020federated,hsu2019measuring]. Surveys note that federated IDS lack common evaluation criteria [@lavaur2022evolution], and evaluations report that class imbalance and non-IID splits degrade federated IDS [@singh2024evaluating]. Federated and central models are also often compared under different amounts of local training, a confound examined in Section 6.5. When a federated detector is calibrated conformally, it is also unclear whether one global threshold can serve clients whose benign traffic differs."));
  C.push(P("**Constrained devices.** TinyML deploys compressed, usually INT8-quantised, models on microcontrollers [@jacob2018quantization,banbury2021mlperf], and several IoT IDS have been deployed this way [@ortizgarces2026nasoptimized,debernardis2026lightweight,panopio2026from]. Quantisation changes the score distribution. A threshold calibrated on the floating-point model is therefore not automatically valid for its INT8 version, and this question is rarely examined."));
  C.push(P("**Research gap.** Each of these problems has been studied, mostly in isolation. What remains less examined is what happens to a calibrated detector's guarantees and detection when the pieces are combined: a benign-only detector with conformal thresholds, trained federatedly on heterogeneous clients, quantised for devices, and turned into host-level escalation decisions for attacks that may be sparse. Section 2 shows that the closest prior studies cover at most two of these aspects at a time, and that host-level accumulation of conformal evidence has not been evaluated for intrusion detection. The gap addressed here is therefore primarily empirical: a controlled, multi-seed assessment of which guarantees survive each step and which design choices actually change host-level detection."));
  C.push(P("**Objectives and research questions.** The study asks:"));
  C.push(B("**RQ1.** How well does a benign-only autoencoder with a conformal three-way rule detect attack families excluded from training, and how faithful is its false-alarm guarantee?"));
  C.push(B("**RQ2.** Why can a federated version of the detector perform much worse than the central one, and does the gap persist under equal training and under non-IID splits?"));
  C.push(B("**RQ3.** Do conformal thresholds remain valid after INT8 quantisation, input corruption and the reduction to a 21-feature device model?"));
  C.push(B("**RQ4 (Phase 10).** Can host-level evidence accumulation — continuous conformal evidence, sequential updates, decay and adaptive accumulation — detect sparse attacks better than the existing host counter at the same false-escalation budget, and at what computational cost?"));
  C.push(P("**Contributions.** The contributions are empirical and methodological rather than a new detection algorithm:"));
  C.push(B(`**C1. Calibrated unseen-attack detection.** A benign-only autoencoder with a two-threshold conformal rule, evaluated with ten seeds and three held-out families. The benign ANOMALY rate is ${fv("normalAnomalyRate")} (target 1%), and the central model flags ${fv("centralUnseenAnomaly")} of unseen-family flows as ANOMALY. A leave-one-family-out analysis shows how much TON_IoT families resemble one another (Sections 3, 6.1–6.3, 6.11).`));
  C.push(B(`**C2. A diagnosis of the federated gap.** The large gap observed with the usual protocol comes mainly from under-training (fewer update steps, optimiser resets). Under matched training the IID federated model is not significantly worse than the central one in ANOMALY rate, although it missed more attacks in 9 of 10 seeds; the remaining gap appears at Dirichlet 0.1, where local-only models do better. Per-client calibration is needed for small non-IID clients (Sections 6.5–6.6).`));
  C.push(B(`**C3. Threshold validity under quantisation and corruption.** Inherited floating-point thresholds keep the ANOMALY level of the 53-feature INT8 model (its UNCERTAIN band drifts) but fail for the 21-feature device model. Recalibration restores the false-alarm level at a measurable cost in missed attacks. Recalibration after input corruption restores the false-alarm level but not detection (Sections 6.7–6.10).`));
  C.push(B("**C4. A pre-specified evaluation of host-level evidence accumulation (Phase 10).** Host-conditional p-values, likelihood-ratio e-values, CUSUM, Shiryaev–Roberts, EWMA, evidence decay, adaptive mixtures and classical p-value combinations are compared under one operational budget. The pre-specified configuration improved detection but exceeded the budget; exploratory analyses point to benign-host heterogeneity, not the choice of accumulator, as the factor limiting sparse-attack detection. They also show that budgets calibrated on validation data do not transfer reliably to test hosts, and that anytime-valid theory thresholds fail when benign hosts are not exchangeable. All of this is reported, including the negative outcome for the pre-specified configuration (Sections 4, 6.12)."));
  C.push(B("**C5. Reproducible artefacts.** Code, notebooks, per-seed outputs, the Phase 10 protocol with its deviations, and a verified reference list are released (see Data and Code Availability)."));
  C.push(P("**Organisation.** Section 2 reviews related work and states which parts of this study are new. Section 3 describes the TrustFed-TinyIDS framework. Section 4 presents the Phase 10 host-level mechanism and its formulation. Section 5 gives the experimental setup and evaluation protocol, and Section 6 the results. Section 7 discusses them, Section 8 lists limitations and threats to validity, and Section 9 concludes."));
}

function secRelated(C) {
  C.push(H1("2. Related Work"));
  C.push(H2("2.1 Federated learning for IoT intrusion detection"));
  C.push(P("Surveys of federated IDS describe a field that grew quickly but lacks common evaluation criteria: architectures, aggregation rules, datasets and splits vary from paper to paper [@lavaur2022evolution,khraisat2025survey,hernandezramos2025intrusion]. Most systems are supervised or semi-supervised classifiers of known classes [@zhao2023semisupervised,singh2024evaluating]. Device heterogeneity is handled by clustering clients [@saezdecamara2023clustered] or by personalisation, for example meta-learned local adaptation [@yan2025global] and personalised FL [@sun2025robust]. Federated anomaly detectors closer to the present setting include DÏoT, a federated self-learning anomaly detector for IoT devices [@nguyen2019diot], and federated PCA on Grassmann manifolds evaluated on TON_IoT [@nguyen2024federated]; outlier-exposure autoencoders for zero-day DDoS use a small number of labelled attack flows per site [@pourahmadi2023spotting]. Two gaps recur. Federated and central models are often compared under different amounts of local training, so a performance gap may reflect the protocol rather than federation itself. And personalisation is applied to model weights, while the calibration of alarm thresholds per client is rarely studied. Section 6.5 addresses the first gap with matched training; Section 6.6 and Phase 10 address the second, at client and at host level."));
  C.push(H2("2.2 Unseen and zero-day attack detection"));
  C.push(P("Open-set IDS combine a classifier of known classes with an unknown-detection score: reconstruction error of a conditional VAE on TON_IoT [@yu2024deep], dynamic open-set updates for industrial IoT [@yang2025lightweight], energy scores [@souza2025novel], hierarchical pipelines [@arthur2025empirical] and feature-influence reconstruction combined with ensemble uncertainty [@fawaz2026detecting]. One-class autoencoders trained on benign traffic avoid attack labels altogether [@mirsky2018kitsune,yao2023lightweight,yang2022griffin]. Leave-one-attack-out protocols have become more common [@fawaz2026detecting,hung2026explainable], and they reveal how strongly results depend on which family is held out. Two weaknesses are shared by much of this work: thresholds are heuristic, so the false-alarm rate on new benign traffic is not controlled, and the similarity between held-out and training families is rarely measured. The present study uses conformal thresholds for the first weakness and a leave-one-family-out analysis with a supervised reference model for the second."));
  C.push(H2("2.3 Conformal prediction and uncertainty-aware detection"));
  C.push(P("Conformal p-values turn anomaly scores into tests with finite-sample validity [@vovk2005algorithmic,bates2023testing]. In intrusion detection they now appear in several forms. **Per-sample false-alarm control** uses one-class conformal detectors for zero-day IoT attacks [@farsimadan2026confid], tiny autoencoders with conformal p-values on TON_IoT [@datta2026cassidy], and a demonstration that percentile thresholds on benign reconstruction error are split-conformal [@massaad2026beyond]. **Abstention and reject options** include benign-calibrated unknown gates followed by class-conditional conformal sets [@younas2026operationally], conformal selective decisions for lightweight IoT IDS [@zhao2026riskcontrolled] and class-conditional rejection in MQTT networks [@gulappagol2026uncertaintyaware]. **Drift monitoring** covers conformal evaluation that triggers retraining [@barrett2026firce,barrett2026fades]. Mondrian (category-conditional) calibration appears in IDS only class by class [@zoller2026reliable,gulappagol2026uncertaintyaware]; calibration per host or device was not found. Outside networking, conformal p-values have been combined over windows for out-of-distribution detection in cyber-physical time series [@kaur2023codit,kaur2024outofdistribution]. A common limitation is that guarantees are marginal over the benign population and decisions are made per sample. The first means heterogeneous hosts can individually violate the bound; the second limits detection at strict false-alarm levels, as the open-world results above show. A related line examines how conformal guarantees degrade under adversarial manipulation of features [@li2026robustconformal]."));
  C.push(H2("2.4 Trust-aware and reputation-based intrusion detection"));
  C.push(P("Trust and reputation systems score entities from the history of their behaviour [@josang2007survey]; in sensor and IoT networks they have been used to isolate misbehaving nodes [@ganeriwal2008reputationbased,alghofaili2023dynamic,ahmadi2024trust] and against Sybil, on-off and ballot-stuffing attacks on the trust system itself [@hassan2024letmiot,rasagna2026zam]. Recent frameworks connect trust scores to IDS output or to federated training: trust management for collaborative IDS that is resilient to false positives [@hayawi2025false], Markov-chain trust prediction fed by an IDS [@bampatsikos2025trust], zero-trust IoT frameworks with distributed blacklisting [@baykara2025zetros], trust-aware federated IDS [@houichi2026trustaware,wardana2024lightweight] and FL-based \"zero-trust\" IDS in which the term refers to keeping data local [@javeed2024federated]. Trust scores in this literature are typically weighted averages, peer ratings or learned scores without a stated false-escalation rate. In the present framework a host's trust is a monotone function of a calibrated statistic (Section 4.4), so the operating point is expressed directly as false escalations per host per week. This makes trust comparable to the operator's budget; it is not claimed to be a better trust model."));
  C.push(H2("2.5 Sequential evidence accumulation and low-rate attacks"));
  C.push(P("Sequential change detection — Page's CUSUM [@page1954continuous], the Shiryaev–Roberts procedure [@shiryaev1963optimum,roberts1966comparison], EWMA charts [@roberts1959control,lucas1990exponentially] and their optimality theory [@lorden1971procedures,moustakides1986optimal,tartakovsky2014sequential] — has a long history in network security, for example SYN-flood detection [@wang2002detecting] and adaptive change-point detection of intrusions [@tartakovsky2006novel]. These detectors need parametric pre- and post-change models. They remain in use with heuristic inputs such as entropy [@g2026lightweight,yu2024renyi]. Low-rate attacks are a known blind spot of volume-based detection [@kuzmanovic2003lowrate,rios2022detection], addressed by end-host methods [@lei2025hawkeye] and by supervised or federated detectors [@ali2023low,anilkumar2026generative,hung2025lowrate]. The closest IoT precedent is CUMAD, which feeds autoencoder alarms into a sequential probability ratio test per device and reduces false positives on N-BaIoT [@mainuddin2023detecting]. Its sequential test relies on assumed anomaly-event rates rather than distribution-free inputs."));
  C.push(P("A distribution-free alternative comes from conformal testing. Conformal test martingales detect departures from exchangeability [@vovk2003testing,fedorova2012plugin,vovk2021testing], inductive conformal martingales detect change points and concept drift [@volkhonskiy2017inductive,vovk2021retrain,eliades2021icm,eliades2024icm], and the conformal CUSUM procedure has recently been given validity and efficiency guarantees [@vovk2025cusum]. E-values and e-detectors generalise these constructions, with average-run-length guarantees under weak assumptions [@vovk2021evalues,shin2024edetectors,ramdas2023gametheoretic]; weighted conformal martingales monitor deployed models [@prinster2025watch]. Recent work argues that standard conformal martingales can be inefficient for change detection [@bhattacharyya2026optimal]. The closest security application found is the detection of adversarial image sequences with conformal test martingales [@dong2026ctm]. Two classical tools for sparse signals among many nulls — Higher Criticism [@donoho2004higher] and the truncated product method [@zaykin2002truncated] — are natural baselines for host windows in which only a few flows are malicious."));
  C.push(H2("2.6 TinyML and lightweight intrusion detection"));
  C.push(P("TinyML IDS report kilobyte-scale models and millisecond-scale latency on microcontrollers or single-board computers: NAS-optimised detectors trained partly on TON_IoT [@ortizgarces2026nasoptimized], CNN detectors for CAN buses on nRF52840 [@im2025tinymlbased], quantised classical models on 8-bit and RISC-V microcontrollers with bit-exact checks [@debernardis2026lightweight], INT8 post-training quantisation for IoMT [@anuva2025lidit], ensembles and energy-aware designs [@hamdouchi2025evaluating,c2025tinymlbased,nassef2026lightweight] and federated TinyML architectures [@li2025cognitive,park2026fedtinyml]. A deployment study warns that quantisation can increase latency or power for models that are already small [@panopio2026from]. Conformal abstention has been shown to fit on microcontrollers outside intrusion detection [@lamaakal2025tcuq]. Most TinyML IDS are supervised and closed-set, and none of those reviewed checks whether calibrated thresholds remain valid after quantisation."));
  C.push(H2("2.7 Critical comparison and positioning"));
  const rows = [
    ["CUMAD [@mainuddin2023detecting]", "AE + SPRT per IoT device", "Assumed event rates", "Sequential, per device", "No / no", "Parametric test; no distribution-free false-alarm control"],
    ["ConFID [@farsimadan2026confid]", "One-class, benign-trained", "Conformal FPR guarantee", "Per flow", "No / no", "No host-level aggregation (per the published summary)"],
    ["CASSIDY [@datta2026cassidy]", "Tiny AE, TON_IoT", "Conformal p-values", "Per sample; drift adaptation", "No / small model", "No host aggregation, no federation"],
    ["Massaad et al. [@massaad2026beyond]", "AE, CAN bus", "Split conformal = percentile threshold", "Per message; adaptive threshold", "No / no", "In-vehicle domain"],
    ["HTCCA-Conformal [@younas2026operationally]", "Unknown gate + class-conditional CP", "Benign-calibrated FPR budget", "Per flow; review routing", "No / no", "≈30.6% unknown-alert detection at 1% FPR"],
    ["UAR-IDS [@gulappagol2026uncertaintyaware]", "Embedding Mahalanobis", "Class-conditional conformal", "Per flow", "No / no", "Per class, not per device; modest AUROC"],
    ["Zöller & Lawall [@zoller2026reliable]", "Tabular foundation model", "APS and Mondrian CP (per class)", "Per flow", "No / no", "Supervised; set size used as a diagnostic"],
    ["FADES [@barrett2026fades]", "Supervised IDS", "Conformal evaluation", "Streaming drift estimate", "No / no", "Targets retraining, not attack alarms"],
    ["Tartakovsky et al. [@tartakovsky2006novel]", "Traffic statistics", "Parametric", "CUSUM / SR change detection", "No / no", "Not distribution-free"],
    ["Conformal CUSUM [@vovk2025cusum]", "Generic", "Conformal martingale", "Sequential", "– / –", "Theory; no security evaluation"],
    ["Nguyen et al. [@nguyen2024federated]", "Federated PCA, TON_IoT", "None stated", "Per sample", "Yes / light model", "Linear model; no calibrated alarms"],
    ["Park et al. [@park2026fedtinyml]", "Federated TinyML IDS", "None", "Per sample", "Yes / yes", "Preprint; no calibration or host aggregation"],
    ["Fawaz et al. [@fawaz2026detecting]", "XAI reconstruction + uncertainty", "Not conformal", "Per sample", "No / no", "Leave-one-attack-out; gains vary by dataset"],
    ["**This work**", "Benign-only AE (53 and 21 features)", "Conformal α/β three-way rule; per-client and host-conditional calibration", "Host windows, CUSUM, SR, EWMA, e-values (Phase 10)", "Yes / INT8", "Simulated host streams; one dataset; budgets did not fully transfer"],
  ];
  C.push(...table(["Study", "Detector", "Calibration / uncertainty", "Temporal or host aggregation", "FL / TinyML", "Main limitation relative to this study"], rows,
    [1800, 1550, 1700, 1650, 1100, 1838],
    "Closest prior work. Entries describe each study only as stated in its retrieved title, abstract or proceedings summary; \"no\" means the aspect was not reported there.",
    { key: "relwork", leftAll: true }));
  C.push(P("**Novelty assessment.** The individual techniques used in this paper are established. They include conformal p-values and Mondrian calibration [@vovk2005algorithmic,vovk2003mondrian], the validity of the maximum of p-values [@vovk2020combining], likelihood-ratio e-values and calibrators [@vovk2021evalues], CUSUM and Shiryaev–Roberts e-detectors [@shin2024edetectors,vovk2025cusum], Higher Criticism and the truncated product, FedAvg and FedProx, and INT8 quantisation. The search (127 verified records; see Data and Code Availability) found no study that calibrates intrusion alarms per host with conformal p-values and accumulates them over a host's flows under an operational false-escalation budget. Combining existing techniques is not by itself a methodological contribution, and the Phase 10 results show that the most elaborate combination did not perform best. The defensible contribution is therefore empirical. It is a controlled, pre-specified, multi-seed comparison, supplemented by clearly labelled exploratory analyses, which indicate that the reference against which p-values are computed matters more than how evidence is accumulated. The comparison also documents where the guarantees stop holding: per host, across benign splits, after quantisation, and under federated heterogeneity."));
}
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
// ---------------- assembler ----------------
citeNum = function (key) {                       // resolve legacy keys to the verified-reference keys
  key = key.trim(); key = CITE_ALIAS[key] || key;
  let i = CITE_ORDER.indexOf(key);
  if (i < 0) { CITE_ORDER.push(key); i = CITE_ORDER.length - 1; }
  return i + 1;
};
const C = [];
secTitle(C);
secAbstract(C);
secIntro(C);
secRelated(C);
C.push(H1("3. The TrustFed-TinyIDS Framework"));
secFramework(C);
secPhase10Method(C);
C.push(H1("5. Experimental Setup and Evaluation Protocol"));
secSetup(C);
secPhase10Setup(C, "5.6");
C.push(H1("6. Results and Comparative Analysis"));
secResults(C);
secPhase10Results(C);
secDiscussion(C);
secLimitations(C);
secConclusion(C);
secDeclarations(C);
secReferences(C);
const OUT_MS = path.join(EN_DIR, "..", "TrustFed-TinyIDS_Manuscript_EN.docx");
const doc = new Document({
  creator: "Mohamed Mereyani", title: "TrustFed-TinyIDS manuscript", styles: EN_STYLES, numbering: EN_NUMBERING,
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: "TrustFed-TinyIDS · Mohamed Mereyani · Page ", size: 17, color: MUTED }),
      new TextRun({ children: [PageNumber.CURRENT], size: 17, color: MUTED }), new TextRun({ text: " / ", size: 17, color: MUTED }),
      new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 17, color: MUTED })] })] }) },
    children: C }],
});
console.log("tables", TAB, "figures", FIG, "references", CITE_ORDER.length);
console.log("flP3IIDMissedGap:", abstractCoreFacts.flP3IIDMissedGap.desc);
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT_MS, buf); console.log("written", OUT_MS); });
