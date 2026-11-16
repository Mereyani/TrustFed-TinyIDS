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
