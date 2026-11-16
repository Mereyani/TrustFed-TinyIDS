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
