"""Phase 3: benign-only conformal p-values and the three-way trust-aware decision.

p(x) = (1 + #{i in cal : s_i >= s(x)}) / (n_cal + 1)

  ANOMALY   if p <= alpha
  UNCERTAIN if alpha < p <= alpha + beta
  NORMAL    if p >  alpha + beta

What is guaranteed (marginally over the calibration draw, and only if benign test and
calibration samples are exchangeable):
  P(ANOMALY   | benign) <= alpha
  P(UNCERTAIN | benign) <= beta + 1/(n_cal + 1)
Nothing is guaranteed about attacks, and p is NOT P(attack | x).
"""
from __future__ import annotations

import math

import numpy as np
from scipy import stats

NORMAL, UNCERTAIN, ANOMALY = 0, 1, 2
DECISION_NAMES = {NORMAL: "NORMAL", UNCERTAIN: "UNCERTAIN", ANOMALY: "ANOMALY"}


def conformal_pvalues(cal_scores: np.ndarray, test_scores: np.ndarray) -> np.ndarray:
    """Vectorised; ties count as 'at least as extreme', so p-values are conservative."""
    cal = np.sort(np.asarray(cal_scores))
    n = len(cal)
    n_ge = n - np.searchsorted(cal, np.asarray(test_scores), side="left")
    return (1.0 + n_ge) / (n + 1.0)


def randomized_pvalues(cal_scores: np.ndarray, test_scores: np.ndarray, seed: int) -> np.ndarray:
    """Randomized (smoothed) conformal p-values for scores with ties (INT8, Isolation Forest):
    p = (#{s_i > s} + U * (1 + #{s_i = s})) / (n + 1),  U ~ Uniform(0, 1).
    Exactly uniform under exchangeability, so the UNCERTAIN bound needs no no-ties assumption."""
    cal = np.sort(np.asarray(cal_scores))
    s = np.asarray(test_scores)
    n = len(cal)
    n_gt = n - np.searchsorted(cal, s, side="right")
    n_eq = np.searchsorted(cal, s, side="right") - np.searchsorted(cal, s, side="left")
    u = np.random.default_rng(seed).uniform(size=len(s))
    return (n_gt + u * (1 + n_eq)) / (n + 1.0)


def tie_report(cal_scores: np.ndarray) -> dict:
    """Share of calibration scores that are not unique; > 0.1% triggers randomized p-values."""
    cal = np.asarray(cal_scores)
    n_distinct = len(np.unique(cal))
    return {"n": len(cal), "distinct": n_distinct, "tie_mass": 1 - n_distinct / max(1, len(cal)),
            "use_randomized": (1 - n_distinct / max(1, len(cal))) > 0.001}


ALWAYS_RANDOMIZED_MODELS = {"iforest", "latent", "int8"}   # tie-prone scores: IF paths, ReLU latent codes with
#   many identical points, INT8 outputs. Fixed per model so the p-value type never flips across seeds (R4-r5).


def pvalues(cal_scores, test_scores, seed: int = 0, model: str | None = None) -> np.ndarray:
    """Default entry point. Randomized p-values for tie-prone models (IF, INT8) always, and for
    any score whose calibration tie mass exceeds 0.1%; deterministic otherwise (continuous AE
    scores), which keeps the deployable thresholds exactly equivalent to the p-value rule."""
    if model in ALWAYS_RANDOMIZED_MODELS or tie_report(cal_scores)["use_randomized"]:
        return randomized_pvalues(cal_scores, test_scores, seed)
    return conformal_pvalues(cal_scores, test_scores)


def decide(p: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    d = np.full(len(p), NORMAL, dtype=np.int8)
    d[p <= alpha + beta] = UNCERTAIN
    d[p <= alpha] = ANOMALY
    return d


def thresholds(cal_scores: np.ndarray, alpha: float, beta: float) -> dict:
    """Score thresholds EXACTLY equivalent to the deterministic p-value rule, ties included
    (the professor's tau_L and tau_H). With k = floor(level * (n + 1)) and tau = the k-th
    largest calibration score:

        s(x) > tau_H  <=>  p(x) <= alpha        s(x) > tau_L  <=>  p(x) <= alpha + beta

    The STRICT inequality is the single tie convention used everywhere (committee R4-2);
    `decide_by_thresholds` uses it and tests/test_conformal.py checks the equivalence.
    """
    cal = np.sort(np.asarray(cal_scores))
    n = len(cal)
    grid = np.arange(1, n + 2) / (n + 1.0)   # the attainable p-values, computed exactly as in decide()

    def tau(level):
        # k = largest integer with k/(n+1) <= level, using the same float arithmetic as the
        # p-value comparison (avoids floor() rounding mismatches at arbitrary levels; R3-B4)
        k = int(np.sum(grid <= level))
        if k < 1:
            return float("inf")
        return float(cal[n - k])

    return {"tau_H": tau(alpha), "tau_L": tau(alpha + beta), "n_cal": n}


def heuristic_thresholds(train_scores: np.ndarray, k_low: float, k_high: float) -> dict:
    """Baseline B3: mean + k*std of TRAINING errors (common practice, optimistic)."""
    mu, sd = float(np.mean(train_scores)), float(np.std(train_scores))
    return {"tau_L": mu + k_low * sd, "tau_H": mu + k_high * sd}


def decide_by_thresholds(scores: np.ndarray, tau_L: float, tau_H: float) -> np.ndarray:
    """Three-way rule on raw scores with the strict-inequality tie convention."""
    s = np.asarray(scores)
    d = np.full(len(s), NORMAL, dtype=np.int8)
    d[s > tau_L] = UNCERTAIN
    d[s > tau_H] = ANOMALY
    return d


# --------------------------------------------------------------------------- validity checks (E1)
def validity_resplits(benign_pool: np.ndarray, n_cal: int, alpha: float, beta: float,
                      R: int, seed: int, model: str | None = None) -> dict:
    """Re-split pooled benign (cal + test) scores R times with the model fixed.

    Returns the realised benign ANOMALY rate and UNCERTAIN rate for each resplit.
    Only array indexing is involved, so this is cheap even for R in the thousands.
    """
    rng = np.random.default_rng(seed)
    pool = np.asarray(benign_pool)
    fpr, unc = np.empty(R), np.empty(R)
    for r in range(R):
        perm = rng.permutation(len(pool))
        cal, test = pool[perm[:n_cal]], pool[perm[n_cal:]]
        d = decide(pvalues(cal, test, seed=seed * 100003 + r, model=model), alpha, beta)
        fpr[r] = np.mean(d == ANOMALY)
        unc[r] = np.mean(d == UNCERTAIN)
    return {"fpr": fpr, "uncertain": unc, "n_cal": n_cal, "n_test": len(pool) - n_cal}


def bulk_shift_monitor(window_scores: np.ndarray, reference_scores: np.ndarray, tau_L: float,
                       level: float = 0.01) -> dict:
    """CANDIDATE C3 (gated by the professor; final phase only, not part of the midterm).

    Label-free check of one window of deployed scores against a held-back benign reference
    (cal-B, disjoint from the cal-A set that defines the thresholds; committee R3-N3).
    Only scores in the NORMAL region (s <= tau_L), where attacks rarely land, are compared,
    with a two-sample KS test. Known blind spot (R2-M1, R4-3): it cannot see shifts that only
    move scores above tau_L (the UNCERTAIN and ANOMALY regions, where FPR is decided);
    tail-only shifts are therefore a required negative control.
    """
    w = np.asarray(window_scores)
    ref = np.asarray(reference_scores)
    w_b, r_b = w[w <= tau_L], ref[ref <= tau_L]
    if len(w_b) < 20 or len(r_b) < 20:
        return {"n_used": int(len(w_b)), "ks_stat": np.nan, "p_value": np.nan, "alarm": False}
    res = stats.ks_2samp(w_b, r_b)
    return {"n_used": int(len(w_b)), "ks_stat": float(res.statistic), "p_value": float(res.pvalue),
            "alarm": bool(res.pvalue < level)}


def beta_law(n_cal: int, level: float) -> stats.rv_continuous:
    """Distribution of the conditional false-alarm rate of split conformal at a given level.

    Given the calibration set, P(p <= level | cal) ~ Beta(l, n + 1 - l) with
    l = floor((n + 1) * level) (Vovk 2012; Angelopoulos & Bates 2021).
    """
    l = math.floor((n_cal + 1) * level)
    return stats.beta(l, n_cal + 1 - l)
