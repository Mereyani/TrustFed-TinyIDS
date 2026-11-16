// test_build_en.js — test assembler for the English core modules.
// Concatenates _head_en.js + _core_en.js + a minimal tail, runs it with the docx package of rapor/node_modules,
// and writes manuscript/en/_core_test.docx.   Usage (from anywhere):  node test_build_en.js
const fs = require("fs"), path = require("path"), os = require("os"), { execFileSync } = require("child_process");
const EN = __dirname;
const NODE_MODULES = path.join(EN, "..", "..", "rapor", "node_modules");

const TAIL = `
// ---------------- minimal test tail ----------------
const C = [];
C.push(H1("3. The TrustFed-TinyIDS Framework")); secFramework(C);
C.push(H1("5. Experimental Setup and Evaluation Protocol")); secSetup(C);
C.push(H1("6. Results and Comparative Analysis")); secResults(C);
C.push(H1("7. Discussion")); secDiscussionCore(C);
C.push(H1("8. Limitations")); secLimitationsCore(C);
C.push(H1("9. Conclusion")); secConclusionCore(C);
C.push(H1("References (citation order)"));
CITE_ORDER.forEach((k, i) => C.push(P("[" + (i + 1) + "] " + k, { align: AlignmentType.LEFT })));
const doc = new Document({ creator: "", lastModifiedBy: "", title: "TrustFed-TinyIDS core (English test build)",
  styles: EN_STYLES, numbering: EN_NUMBERING,
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    children: C }] });
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT_EN, buf);
  console.log("written", OUT_EN);
  console.log("tables:", TAB, "figures:", FIG);
  console.log("XREF:", JSON.stringify(XREF));
  console.log("CITE_ORDER:", JSON.stringify(CITE_ORDER));
  console.log("abstractCoreFacts:", Object.keys(abstractCoreFacts).length, "entries");
  for (const [k, v] of Object.entries(abstractCoreFacts)) console.log("  ", k, "=", v.value);
});
`;
const src = ["_head_en.js", "_core_en.js"].map((f) => fs.readFileSync(path.join(EN, f), "utf8")).join("\n") + TAIL;
const tmp = path.join(os.tmpdir(), `tft_core_test_${process.pid}.js`);
fs.writeFileSync(tmp, src);
try {
  const out = execFileSync(process.execPath, [tmp], { env: { ...process.env, NODE_PATH: NODE_MODULES, TFT_EN_DIR: EN }, encoding: "utf8" });
  process.stdout.write(out);
} finally { fs.unlinkSync(tmp); }
