// ---------------- assembler: Supplementary Material ----------------
citeNum = function (key) {                       // resolve legacy keys to the verified-reference keys
  key = key.trim(); key = CITE_ALIAS[key] || key;
  let i = CITE_ORDER.indexOf(key);
  if (i < 0) { CITE_ORDER.push(key); i = CITE_ORDER.length - 1; }
  return i + 1;
};
DOC_MODE = "supp"; PFX = "S";
const C = [];
C.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 480, after: 200 },
  children: [new TextRun({ text: "Supplementary Material", bold: true, size: 34, color: NAVY })] }));
C.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
  children: [new TextRun({ text: "Reliability of Calibrated IoT Intrusion Detection under Federated Training, Quantization, and Host-Level Aggregation: An Empirical Study", italics: true, size: 24 })] }));
C.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 }, children: [new TextRun({ text: "Mohamed Mereyani · Siirt University", size: 20, color: MUTED })] }));
C.push(P("This document contains the complete experimental record behind the main text: the full description of the framework (S1), the formulation of every host-level rule evaluated (S2), the detailed experimental protocols (S3), and every result table and figure (S4), including secondary experiments, ablations, risk–coverage analyses, per-family and per-protocol results, and all Phase 10 and Phase 10b baselines. No result has been removed, with one exception: a test-tuned diagnostic was withdrawn because it set thresholds on test data; the withdrawal is explained in S4.12.4. Tables and figures are numbered S1, S2, …; citations refer to the reference list at the end of this document. Raw per-seed outputs, code and protocols are in the public repository (https://github.com/Mereyani/TrustFed-TinyIDS)."));
C.push(H1("3. Detailed Framework Description"));
secFramework(C);
secPhase10Method(C);
C.push(H1("5. Detailed Experimental Setup"));
secSetup(C);
secPhase10Setup(C, "5.6");
secPhase10bSetup(C, "5.7");
C.push(H1("6. Detailed Results"));
secResults(C);
secPhase10Results(C);
secPhase10bResults(C);
C.push(H1("References for the Supplementary Material"));
secReferencesBody(C);
fs.writeFileSync(path.join(EN_DIR, "supp_xref.json"), JSON.stringify(XREF, null, 1));
const OUT_S = path.join(EN_DIR, "..", "v4", "TrustFed-TinyIDS_Supplementary_Material.docx");
fs.mkdirSync(path.dirname(OUT_S), { recursive: true });
const docS = new Document({ creator: "Mohamed Mereyani", title: "Supplementary Material", styles: EN_STYLES, numbering: EN_NUMBERING,
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: "Supplementary Material · Page ", size: 17, color: MUTED }),
      new TextRun({ children: [PageNumber.CURRENT], size: 17, color: MUTED }), new TextRun({ text: " / ", size: 17, color: MUTED }),
      new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 17, color: MUTED })] })] }) },
    children: C }] });
console.log("supp tables", TAB, "figures", FIG, "references", CITE_ORDER.length);
Packer.toBuffer(docS).then((b) => { fs.writeFileSync(OUT_S, b); console.log("written", OUT_S); });
