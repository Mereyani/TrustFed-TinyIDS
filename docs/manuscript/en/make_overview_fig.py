"""Study overview figure for the v4 manuscript (no data; a schematic of the pipeline and reliability checks)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
fig, ax = plt.subplots(figsize=(11, 4.6)); ax.set_xlim(0, 110); ax.set_ylim(0, 46); ax.axis("off")
def box(x, y, w, h, t, fc="#eef4fb", ec="#2a78d6", fs=8.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, weight="bold" if bold else "normal", wrap=True)
def arrow(x1, y1, x2, y2, c="#1f3a5f"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", color=c, lw=1.3))
# pipeline
box(1, 30, 15, 10, "Benign-only\nautoencoder\n(53 or 21 features)")
box(21, 30, 17, 10, "Conformal p-value\nvs benign\ncalibration scores")
box(43, 30, 17, 10, "Three-way rule\nANOMALY / UNCERTAIN /\nNORMAL (α, β)")
box(65, 30, 19, 10, "Host-level aggregation\nwindow counts, CUSUM,\nEWMA, e-values")
box(89, 30, 19, 10, "Host escalation\n(budget: false esc.\nper host-week)")
for a, b in [(16.8, 38.2), (38.8, 60.8), (60.8, 65)]: pass
arrow(16.4, 35, 20.6, 35); arrow(38.4, 35, 42.6, 35); arrow(60.4, 35, 64.6, 35); arrow(84.4, 35, 88.6, 35)
# stressors
st = "#fff4e5"; se = "#d6602a"
box(1, 12, 15, 9, "Federated training\nP1–P4; IID,\nDirichlet 1.0 / 0.1", st, se, 8)
box(21, 12, 17, 9, "INT8 quantisation\nand input corruption\n(inherited vs recalibrated)", st, se, 8)
box(43, 12, 17, 9, "Pooled vs per-client\nand host-conditional\ncalibration", st, se, 8)
box(65, 12, 19, 9, "Sparse attacks\n(attack share ρ),\nW = 20–200 flows", st, se, 8)
box(89, 12, 19, 9, "Transfer to other\nbenign units:\nMAIN, SWAP, DEVICE, DEDUP", st, se, 8)
for x in (8.5, 29.5, 51.5, 74.5, 98.5): arrow(x, 21.6, x, 29.4, se)
ax.text(55, 7.5, "Reliability checked at each step: marginal benign alarm rate (flow), worst-client FPR (federated), threshold validity (INT8, corruption),",
        ha="center", fontsize=8, color="#5b6270")
ax.text(55, 4.2, "realised false escalations per host-week, mean and worst host (host level). Thresholds are always set on calibration data only.",
        ha="center", fontsize=8, color="#5b6270")
ax.text(1, 43.5, "Detection pipeline", fontsize=9, weight="bold", color="#1f3a5f")
ax.text(10.2, 25.2, "Stressors examined", fontsize=9, weight="bold", color="#d6602a")
fig.tight_layout(); fig.savefig("figs/v4_overview.png", dpi=220); print("ok")
