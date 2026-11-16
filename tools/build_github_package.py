"""Assemble the GitHub-ready TrustFed-TinyIDS repository folder and ZIP from the working project.

Copies (never moves) code, notebooks, results and documents into
  <Vize Projesi>/GitHub_Package/TrustFed-TinyIDS/
and zips it to <Vize Projesi>/GitHub_Package/TrustFed-TinyIDS_github.zip.

Excluded on purpose: the TON_IoT CSV and every array of dataset feature vectors (prepared*.npz), caches,
node_modules, temporary files and Office lock files. The dev_val labels and multiplicities needed by Phase 10
are exported to a small metadata file instead of the feature matrix.
"""
from __future__ import annotations

import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np

FA = Path(__file__).resolve().parents[1]                  # Final_Asama/
VP = FA.parent                                            # Vize Projesi/
OUT = VP / "GitHub_Package" / "TrustFed-TinyIDS"
ZIP = VP / "GitHub_Package" / "TrustFed-TinyIDS_github.zip"
SKIP_DIRS = {"__pycache__", ".ipynb_checkpoints", "node_modules", ".pytest_cache"}
SKIP_SUFFIX = {".pyc", ".tmp", ".log"}
SKIP_PREFIX = ("~$",)
COLAB_RUNS = ["20261110-222358_final_F1_fl_teshis", "20261111-042106_midterm_phase4",
              "20261111-055215_midterm_phase4b_resolution", "20261111-060847_final_F2_lofo",
              "20261111-064904_final_F5_seyrek_saldiri", "20261112-060216_final_F3_asama5_9",
              "20261112-120717_final_F4_cihaz_modeli"]
ARTIFACT_DIRS = ["scores", "resolution", "sparse", "final_f3", "final_f4", "fl_diag", "lofo", "models", "decisions",
                 "featcmp", "training"]
ARTIFACT_FILES = ["ae_selection.json", "checkpoint_fingerprint.json", "data_file_info.json", "environment.json",
                  "training_summary.json"]


def copytree(src: Path, dst: Path, exclude_glob=()):
    for p in src.rglob("*"):
        rel = p.relative_to(src)
        if any(part in SKIP_DIRS for part in rel.parts) or p.name.startswith(SKIP_PREFIX):
            continue
        if p.is_dir() or p.suffix in SKIP_SUFFIX or any(p.match(g) for g in exclude_glob):
            continue
        q = dst / rel
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, q)


def cp(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for child in OUT.iterdir():                     # empty the folder (the folder itself may be open elsewhere)
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    code = FA / "TrustFed-TinyIDS-Final"
    copytree(code / "trustids", OUT / "trustids")
    copytree(code / "notebooks", OUT / "notebooks")
    for f in ["build_final_notebooks.py", "final_cells.py", "smoke_test_final.py", "val_hist_analizi.py",
              "build_github_package.py"]:
        cp(FA / "tools" / f, OUT / "tools" / f)
    copytree(FA / "tests", OUT / "tests")
    # Phase 10
    p10 = FA / "phase10"
    for f in ["run_phase10.py", "select_phase10.py", "analyze_phase10.py", "analyze_extra_phase10.py", "tradeoff_phase10.py", "host_heterogeneity.py", "check_f5_reproduction.py", "overhead_phase10.py", "make_p10_values.py",
              "PROTOCOL_PHASE10.md"]:
        if (p10 / f).exists():
            cp(p10 / f, OUT / "experiments" / "phase10" / f)
    copytree(p10 / "results", OUT / "experiments" / "phase10" / "results")
    copytree(p10 / "logs", OUT / "experiments" / "phase10" / "logs_console", exclude_glob=())
    # Colab results of phases 1-9
    for r in COLAB_RUNS:
        copytree(FA / "colab_sonuclari" / r, OUT / "results" / "colab_runs" / r)
    copytree(FA / "colab_sonuclari" / "notebooks", OUT / "results" / "executed_notebooks")
    art = FA / "colab_sonuclari" / "artifacts"
    for d in ARTIFACT_DIRS:
        if (art / d).exists():
            copytree(art / d, OUT / "results" / "artifacts" / d, exclude_glob=("prepared.npz", "prepared_*.npz"))
    for f in ARTIFACT_FILES:
        if (art / f).exists():
            cp(art / f, OUT / "results" / "artifacts" / f)
    for d in ["prepared", "prepared_device", "prepared_leakage"]:     # reports only, no feature matrices
        for f in (art / d).glob("*.json"):
            cp(f, OUT / "results" / "artifacts" / d / f.name)
    z = np.load(art / "prepared" / "prepared.npz", allow_pickle=True)
    np.savez_compressed(OUT / "results" / "artifacts" / "prepared" / "dev_val_meta.npz",
                        type_dev_val=z["type_dev_val"], mult_dev_val=z["mult_dev_val"])
    copytree(FA / "analiz_ek", OUT / "results" / "analysis_extra")
    # report builders (Turkish course report, kept as a previous version) and the English manuscript
    for f in ["make_final_values.py", "values.json"]:
        cp(FA / "rapor" / f, OUT / "docs" / "previous_versions" / "final_report_tr" / f)
    cp(FA / "rapor" / "TrustFed-TinyIDS_Final_Raporu.docx",
       OUT / "docs" / "previous_versions" / "final_report_tr" / "TrustFed-TinyIDS_Final_Report_TR.docx")
    man = FA / "manuscript"
    if man.exists():
        copytree(man, OUT / "docs" / "manuscript", exclude_glob=("*_test.docx", "*.bak"))
    # legacy midterm code (phases 1-4, version 5.2), code only
    legacy = VP / "TrustFed-TinyIDS"
    for d in ["trustids", "notebooks", "configs", "tests", "tools", "experiments"]:
        if (legacy / d).exists():
            copytree(legacy / d, OUT / "legacy" / "midterm_v5.2" / d)
    for f in ["requirements.txt", "README.md"]:
        cp(legacy / f, OUT / "legacy" / "midterm_v5.2" / f)
    # repository documents written for the package
    for f in (FA / "github_docs").glob("*"):
        if f.is_file():
            cp(f, OUT / f.name)
    # checksums and zip
    lines = []
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT).as_posix()}")
    (OUT / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                zf.write(p, Path("TrustFed-TinyIDS") / p.relative_to(OUT))
    n = sum(1 for p in OUT.rglob("*") if p.is_file())
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"{n} files -> {OUT}\nzip: {ZIP} ({ZIP.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
