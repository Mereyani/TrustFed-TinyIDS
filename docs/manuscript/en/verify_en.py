"""Verification of the English core build against the Turkish report.
(b) multiset of decimal numbers: Turkish report sections 3-8 vs manuscript/en/_core_test.docx
(c) no Turkish characters/words, no 'draft'/'taslak', no NaN/undefined/null/Infinity in the English text.
Run:  python -I verify_en.py      (after: node test_build_en.js)
"""
import re, sys, zipfile
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
EN = Path(__file__).resolve().parent
TR_DOCX = EN.parents[1] / "rapor" / "TrustFed-TinyIDS_Final_Raporu.docx"
EN_DOCX = EN / "_core_test.docx"


def paragraphs(docx):
    x = zipfile.ZipFile(docx).read("word/document.xml").decode("utf-8")
    return ["".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", p)) for p in re.findall(r"<w:p[ >].*?</w:p>", x, flags=re.S)]


tr_all = paragraphs(TR_DOCX)
i0 = next(i for i, p in enumerate(tr_all) if p.startswith("3. Veri ve ön işleme"))
i1 = next(i for i, p in enumerate(tr_all) if p.startswith("Ek A."))
tr = tr_all[i0:i1]
en_all = paragraphs(EN_DOCX)
en = en_all[: next(i for i, p in enumerate(en_all) if p.startswith("References (citation order)"))]

# ---------- (b) numbers ----------
VERSION = r"\d+\.\d+\.\d+"                                   # software versions (2.21.0 etc.)
def clean_tr(p):
    p = re.sub(VERSION, " ", p)
    p = p.replace("Dirichlet=1.0", "Dirichlet=1,0").replace("Dirichlet=0.1", "Dirichlet=0,1")   # point-decimal labels in Turkish tables
    p = re.sub(r"^(?:\d+\.\d{1,2}|\d+\.)\s+(?=[^\s/(–\-])", "", p) if len(p) < 90 else p                      # heading numbers
    p = re.sub(r"Bölüm \d+(?:\.\d+)?(?:[–-]\d+(?:\.\d+)?)?(?: ve \d+(?:\.\d+)?)?(?:’\S*)?", " ", p)
    p = re.sub(r"Tablo \d+\.?|Şekil \d+\.?", " ", p)
    return p
def clean_en(p):
    p = re.sub(VERSION, " ", p)
    p = re.sub(r"^(?:\d+\.\d{1,2}|\d+\.)\s+(?=[^\s/(–\-])", "", p) if len(p) < 90 else p
    p = re.sub(r"Sections? \d+(?:\.\d+)?(?:[–-]\d+(?:\.\d+)?)?(?: and \d+(?:\.\d+)?)?", " ", p)
    p = re.sub(r"Table \d+\.?|Fig\. \d+\.?", " ", p)
    p = re.sub(r"\[\d+(?:, \d+)*\]", " ", p)                     # citation numbers
    return p
NOT_AFTER = r"(?<![A-Za-zÀ-ÿğışçöüİĞŞÇÖÜ_\d.,])"               # skip digits glued to letters (F3, P1, A3, s0)
def nums_tr(p):
    out = []
    for m in re.finditer(NOT_AFTER + r"(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)", clean_tr(p)):
        out.append(m.group(1).replace(".", "").replace(",", "."))
    return out
def nums_en(p):
    out = []
    for m in re.finditer(NOT_AFTER + r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)", clean_en(p)):
        out.append(m.group(1).replace(",", ""))
    return out

ct = Counter(n for p in tr for n in nums_tr(p)); ce = Counter(n for p in en for n in nums_en(p))
only_tr, only_en = ct - ce, ce - ct
print(f"(b) numbers: Turkish sections 3-8 = {sum(ct.values())}, English core = {sum(ce.values())}")
print("    only in Turkish:", dict(sorted(only_tr.items())) or "none")
print("    only in English:", dict(sorted(only_en.items())) or "none")
def where(n):
    for lab, paras, fn in [("TR", tr, nums_tr), ("EN", en, nums_en)]:
        hits = [(fn(p).count(n), p) for p in paras if n in fn(p)]
        print(f"      [{n}] {lab}: {sum(h for h, _ in hits)}x in {len(hits)} paragraph(s)")
        for h, p in hits[:8]: print(f"           {h}x … {p[:150]}")
for n in sorted(set(only_tr) | set(only_en)): where(n)

# ---------- (c) Turkish residue / forbidden words ----------
text = "\n".join(en_all)
chars = sorted(set(re.findall(r"[ğşıİçöüĞŞÇÖÜ]", text)))
TR_WORDS = ["ve", "bir", "için", "ile", "değil", "olarak", "tohum", "tohumlar", "öznitelik", "oznitelik", "saldırı", "kalibrasyon", "eşik",
            "yığın", "merkezi", "federe", "yerel", "görülmemiş", "bilinen", "kaçan", "havuz", "istemci", "bölme", "sızıntı", "aile", "seyrek",
            "ozet", "tum", "orijinal", "kucuk", "yakinsama", "kalici", "teshis", "asama", "cihaz", "skor", "seçici", "kapsama", "puan", "ek test",
            "Bölüm", "Tablo", "Şekil", "Aşama"]
bad_words = {w: len(re.findall(rf"(?<!\w){re.escape(w)}(?!\w)", text, flags=re.I)) for w in TR_WORDS}
bad_words = {w: n for w, n in bad_words.items() if n}
forbidden = {w: len(re.findall(rf"\b{w}\b", text, flags=re.I)) for w in ["draft", "taslak", "NaN", "undefined", "null", "Infinity", "midterm", "professor"]}
forbidden = {w: n for w, n in forbidden.items() if n}
print("(c) Turkish characters:", chars or "none")
print("    Turkish words:", bad_words or "none")
print("    forbidden tokens:", forbidden or "none")
print("    'we ' occurrences:", len(re.findall(r"\bwe\b", text, flags=re.I)), "| first person 'I ':", len(re.findall(r"(?<![A-Za-z])I(?= )", text)))
