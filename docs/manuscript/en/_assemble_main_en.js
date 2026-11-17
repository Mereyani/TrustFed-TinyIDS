// ---------------- assembler: main manuscript (v4) ----------------
citeNum = function (key) {
  key = key.trim(); key = CITE_ALIAS[key] || key;
  let i = CITE_ORDER.indexOf(key);
  if (i < 0) { CITE_ORDER.push(key); i = CITE_ORDER.length - 1; }
  return i + 1;
};
DOC_MODE = "main"; PFX = "";
const C = [];
mTitle(C); mAbstract(C); mIntro(C); mRelated(C); mDesign(C); mResults(C); mDiscussion(C); mThreats(C); mConclusion(C);
secDeclarations(C);
C.push(H1("Supplementary Material"));
C.push(P("The Supplementary Material (separate file) contains the detailed framework description (S1), the formulation of all host-level rules with assumptions (S2), detailed protocols (S3), and all detailed results, secondary experiments and baselines (S4)."));
secReferences(C);
const OUT_M = path.join(EN_DIR, "..", "v4", "TrustFed-TinyIDS_Reliability_Manuscript.docx");
fs.mkdirSync(path.dirname(OUT_M), { recursive: true });
const docM = new Document({ creator: "Mohamed Mereyani", title: MTITLE, styles: EN_STYLES, numbering: EN_NUMBERING,
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: "Mohamed Mereyani · Page ", size: 17, color: MUTED }),
      new TextRun({ children: [PageNumber.CURRENT], size: 17, color: MUTED }), new TextRun({ text: " / ", size: 17, color: MUTED }),
      new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 17, color: MUTED })] })] }) },
    children: C }] });
console.log("main tables", TAB, "figures", FIG, "references", CITE_ORDER.length);
Packer.toBuffer(docM).then((b) => { fs.writeFileSync(OUT_M, b); console.log("written", OUT_M); });
