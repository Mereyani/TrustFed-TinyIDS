"""Phase 4: metrics for binary and selective (three-way) detection, reliability evidence
and statistics. All definitions follow proposal §6 and the professor's Plan.txt.

Error of an auto-decision = an attack decided NORMAL, or a benign decided ANOMALY.
Coverage          = #{NORMAL or ANOMALY} / N
Abstention rate   = #{UNCERTAIN} / N            (also reported for benign and attack separately)
Selective risk    = #{errors among auto-decided} / #{auto-decided}
Unseen recall     = #{held-out attack -> ANOMALY} / #{held-out attack}
Deferred attacks  = #{held-out attack -> UNCERTAIN} / #{held-out attack}

Prevalence reweighting (to attack prevalence pi): every benign sample gets weight
(1 - pi) / N_benign and every attack sample gets weight pi / N_attack; rates are then
weighted means. This removes the dependence of selective risk and PR-AUC on the test-set
base rate.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import average_precision_score, roc_auc_score

from .conformal import ANOMALY, NORMAL, UNCERTAIN


# --------------------------------------------------------------------------- helpers
def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def prevalence_weights(y_attack: np.ndarray, pi: float | None) -> np.ndarray:
    y = np.asarray(y_attack).astype(bool)
    if pi is None:
        return np.ones(len(y))
    w = np.empty(len(y))
    w[~y] = (1 - pi) / max(1, (~y).sum())
    w[y] = pi / max(1, y.sum())
    return w * len(y)


# --------------------------------------------------------------------------- binary (professor's metrics)
def binary_metrics(y_attack: np.ndarray, scores: np.ndarray, pred_attack: np.ndarray,
                   pi: float | None = None) -> dict:
    y = np.asarray(y_attack).astype(bool)
    pred = np.asarray(pred_attack).astype(bool)
    w = prevalence_weights(y, pi)
    tp = np.sum(w * (pred & y)); fp = np.sum(w * (pred & ~y))
    fn = np.sum(w * (~pred & y)); tn = np.sum(w * (~pred & ~y))
    prec = tp / (tp + fp) if tp + fp else np.nan
    rec = tp / (tp + fn) if tp + fn else np.nan
    f1 = 2 * prec * rec / (prec + rec) if prec and rec and not np.isnan(prec + rec) else np.nan
    out = {"precision": prec, "recall": rec, "f1": f1, "fpr": fp / (fp + tn) if fp + tn else np.nan}
    if y.any() and (~y).any():
        out["pr_auc"] = average_precision_score(y, scores, sample_weight=w)
        out["roc_auc"] = roc_auc_score(y, scores)
    return out


# --------------------------------------------------------------------------- selective (three-way)
def selective_metrics(y_attack: np.ndarray, decision: np.ndarray, pi: float | None = None) -> dict:
    y = np.asarray(y_attack).astype(bool)
    d = np.asarray(decision)
    w = prevalence_weights(y, pi)
    auto = d != UNCERTAIN
    err = auto & ((y & (d == NORMAL)) | (~y & (d == ANOMALY)))
    out = {
        "coverage": np.sum(w * auto) / np.sum(w),
        "abstention": np.sum(w * ~auto) / np.sum(w),
        "selective_risk": np.sum(w * err) / np.sum(w * auto) if np.sum(w * auto) else np.nan,
        "benign_anomaly_rate": np.mean(d[~y] == ANOMALY) if (~y).any() else np.nan,
        "benign_uncertain_rate": np.mean(d[~y] == UNCERTAIN) if (~y).any() else np.nan,
        "attack_anomaly_rate": np.mean(d[y] == ANOMALY) if y.any() else np.nan,
        "attack_uncertain_rate": np.mean(d[y] == UNCERTAIN) if y.any() else np.nan,
        "attack_missed_rate": np.mean(d[y] == NORMAL) if y.any() else np.nan,
    }
    pred_attack = d == ANOMALY
    tp = np.sum(w * (pred_attack & y)); fp = np.sum(w * (pred_attack & ~y))
    out["precision_auto"] = tp / (tp + fp) if tp + fp else np.nan
    return out


def per_family_table(types: np.ndarray, decision: np.ndarray, groups: dict,
                     collision: np.ndarray | None = None, exclude_from_macro: tuple = ()) -> pd.DataFrame:
    """One row per family: ANOMALY / UNCERTAIN / NORMAL rates with Wilson 95% CIs.

    groups maps a group name ('normal', 'known', 'held-out') to the list of families in it.
    If `collision` is given, the primary pessimistic recall (collided attacks counted as missed)
    is added. Families in `exclude_from_macro` (e.g. mitm below 200 unique vectors) are shown
    but left out of the macro average (pre-registered fallback).
    """
    rows = []
    for gname, fams in groups.items():
        for fam in fams:
            m = types == fam
            n = int(m.sum())
            if n == 0:
                continue
            k_a = int(np.sum(decision[m] == ANOMALY)); k_u = int(np.sum(decision[m] == UNCERTAIN))
            lo, hi = wilson_ci(k_a, n)
            row = {"group": gname, "family": fam, "n": n,
                   "anomaly_rate": k_a / n, "anomaly_ci_low": lo, "anomaly_ci_high": hi,
                   "uncertain_rate": k_u / n, "normal_rate": 1 - (k_a + k_u) / n,
                   "in_macro": fam not in exclude_from_macro}
            if collision is not None and gname != "normal":
                c = np.asarray(collision)[m]
                row["collided"] = int(c.sum())
                row["anomaly_rate_collisions_as_missed"] = float(np.mean((decision[m] == ANOMALY) & ~c))
            rows.append(row)
    df = pd.DataFrame(rows)
    if len(df):
        cols = [c for c in ["anomaly_rate", "uncertain_rate", "normal_rate", "anomaly_rate_collisions_as_missed"] if c in df]
        macro = df[df["in_macro"]].groupby("group")[cols].mean()
        macro["family"] = "macro-average"
        macro["n"] = df[df["in_macro"]].groupby("group")["n"].sum()
        df = pd.concat([df, macro.reset_index()], ignore_index=True)
    return df


# --------------------------------------------------------------------------- reliability evidence (E2)
def risk_coverage_curve(y_attack: np.ndarray, pvalues: np.ndarray, alpha: float,
                        betas: np.ndarray | None = None, pi: float | None = None) -> pd.DataFrame:
    """Sweep beta at fixed alpha: each point is (coverage, selective risk)."""
    from .conformal import decide
    if betas is None:
        betas = np.unique(np.concatenate([[0.0], np.quantile(pvalues, np.linspace(0, 1, 200)) - alpha]))
        betas = betas[(betas >= 0) & (betas <= 1 - alpha)]
    rows = [{"beta": b, **selective_metrics(y_attack, decide(pvalues, alpha, b), pi)} for b in betas]
    return pd.DataFrame(rows).sort_values("coverage")


def aurc(y_attack: np.ndarray, confidence: np.ndarray, correct: np.ndarray) -> dict:
    """Area under the risk-coverage curve when samples are abstained in order of lowest
    confidence (Geifman & El-Yaniv). Integrated over coverage in (0, 1]. Also returns the
    oracle AURC (perfect ranking) and the excess AURC = AURC - oracle."""
    order = np.argsort(-np.asarray(confidence), kind="stable")
    err = (~np.asarray(correct).astype(bool))[order].astype(float)
    n = len(err)
    risks = np.cumsum(err) / np.arange(1, n + 1)
    a = float(np.mean(risks))
    e = err.sum()
    oracle_err = np.concatenate([np.zeros(n - int(e)), np.ones(int(e))])
    oracle = float(np.mean(np.cumsum(oracle_err) / np.arange(1, n + 1)))
    return {"aurc": a, "oracle_aurc": oracle, "excess_aurc": a - oracle}


def random_abstention_control(y_attack: np.ndarray, decision: np.ndarray, repeats: int,
                              seed: int, pi: float | None = None) -> dict:
    """Matched-coverage control: keep the same binary predictions as the selective rule
    (ANOMALY vs not), but abstain on a RANDOM subset of the same size as the UNCERTAIN set.
    If the trust signal carries information, the real selective risk is lower."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y_attack).astype(bool)
    d = np.asarray(decision)
    k = int(np.sum(d == UNCERTAIN))
    base_pred_attack = d == ANOMALY
    real = selective_metrics(y, d, pi)["selective_risk"]
    sims = []
    for _ in range(repeats):
        dd = np.where(base_pred_attack, ANOMALY, NORMAL).astype(np.int8)
        dd[rng.choice(len(dd), size=k, replace=False)] = UNCERTAIN
        sims.append(selective_metrics(y, dd, pi)["selective_risk"])
    sims = np.array(sims)
    return {"real_selective_risk": real, "random_mean": float(np.mean(sims)),
            "random_ci": (float(np.quantile(sims, 0.025)), float(np.quantile(sims, 0.975))),
            "delta": float(np.mean(sims) - real)}


def error_by_pvalue_bin(y_attack: np.ndarray, pvalues: np.ndarray, decision: np.ndarray,
                        bins: list) -> pd.DataFrame:
    """Share of attacks and decision error per p-value bin (does low p really mean 'attack'?)."""
    y = np.asarray(y_attack).astype(bool)
    cats = pd.cut(pvalues, bins=bins, include_lowest=True)
    err = (y & (decision == NORMAL)) | (~y & (decision == ANOMALY))
    df = pd.DataFrame({"bin": cats, "attack": y, "error": err})
    return df.groupby("bin", observed=False).agg(n=("attack", "size"), attack_share=("attack", "mean"),
                                                 error_rate=("error", "mean")).reset_index()


def band_for_abstention(scores: np.ndarray, tau_H: float, n_abstain: int) -> float:
    """Matched-coverage helper for E2 (label-free). Same tie convention as the decision rule:
    UNCERTAIN = (tau_L, tau_H]. Returns tau_L so that #{tau_L < s <= tau_H} = n_abstain
    (exactly for continuous scores; as close as possible from below when scores tie)."""
    s = np.asarray(scores)
    below = np.sort(s[s <= tau_H])
    if n_abstain <= 0 or len(below) == 0:
        return float(tau_H)
    if n_abstain >= len(below):
        return float(-np.inf)
    return float(below[len(below) - n_abstain - 1])


def band_for_weighted_abstention(scores: np.ndarray, tau_H: float, weights: np.ndarray,
                                 target_mass: float) -> float:
    """Evaluation-time helper for prevalence-weighted comparisons: tau_L such that the WEIGHTED
    mass of (tau_L, tau_H] is as close as possible to target_mass. Uses labels through the
    weights, so it is an analysis construct (never a deployable rule)."""
    s, w = np.asarray(scores), np.asarray(weights)
    m = s <= tau_H
    order = np.argsort(-s[m], kind="stable")
    cum = np.cumsum(w[m][order])
    k = int(np.searchsorted(cum, target_mass, side="left"))
    srt = s[m][order]
    if k >= len(srt):
        return float(-np.inf)
    return float(srt[k]) if k > 0 else float(tau_H)


def matched_coverage_comparison(y_attack, dec_ref, scores_alt, tau_H_alt, pi=None) -> dict:
    """E2: the alternative keeps its own upper threshold and gets the same abstention as the
    reference rule, then selective risk is compared.

    pi=None : label-free matching on the abstention COUNT (pre-registered primary analysis).
    pi=x    : matching on the prevalence-WEIGHTED abstention mass (exploratory; uses labels).
    The false-alarm / miss decomposition uses the same weights, so the parts sum to delta_sr.
    """
    from .conformal import decide_by_thresholds
    y = np.asarray(y_attack).astype(bool)
    d_ref = np.asarray(dec_ref)
    w = prevalence_weights(y, pi)
    if pi is None:
        tau_L = band_for_abstention(scores_alt, tau_H_alt, int(np.sum(d_ref == UNCERTAIN)))
    else:
        tau_L = band_for_weighted_abstention(scores_alt, tau_H_alt, w, float(np.sum(w * (d_ref == UNCERTAIN))))
    dec_alt = decide_by_thresholds(np.asarray(scores_alt), tau_L, tau_H_alt)
    ref = selective_metrics(y, d_ref, pi)
    alt = selective_metrics(y, dec_alt, pi)

    def parts(d):
        auto = d != UNCERTAIN
        n = max(1e-12, np.sum(w * auto))
        return (np.sum(w * (auto & ~y & (d == ANOMALY))) / n, np.sum(w * (auto & y & (d == NORMAL))) / n)

    fa_ref, miss_ref = parts(d_ref)
    fa_alt, miss_alt = parts(dec_alt)
    return {"abstain_ref": int(np.sum(d_ref == UNCERTAIN)), "abstain_alt": int(np.sum(dec_alt == UNCERTAIN)),
            "coverage_ref": ref["coverage"], "coverage_alt": alt["coverage"],
            "sr_ref": ref["selective_risk"], "sr_alt": alt["selective_risk"],
            "delta_sr": alt["selective_risk"] - ref["selective_risk"],
            "delta_false_alarm_part": fa_alt - fa_ref, "delta_miss_part": miss_alt - miss_ref,
            "alt_benign_anomaly_rate": alt["benign_anomaly_rate"], "tau_L_alt": tau_L}


def tiering_vs_binary(y_attack: np.ndarray, pvalues: np.ndarray, alpha: float, beta: float,
                      pi: float | None = None, per_flows: int = 10_000) -> pd.DataFrame:
    """What the UNCERTAIN band really buys (committee round 5): the union ANOMALY ∪ UNCERTAIN of
    the three-way rule equals the binary rule at alpha + beta, so the value is the SPLIT of the
    flagged set into an immediate-alarm tier and a review tier. Reports, per rule, the benign and
    attack shares of each tier, per-tier precision (prevalence-weighted if pi is given) and the
    analyst workload per `per_flows` flows."""
    y = np.asarray(y_attack).astype(bool)
    p = np.asarray(pvalues)
    w = prevalence_weights(y, pi)
    wn = w / w.sum()
    rules = {f"binary α={alpha}": (p <= alpha, np.zeros(len(p), bool)),
             f"binary α+β={round(alpha + beta, 4)}": (p <= alpha + beta, np.zeros(len(p), bool)),
             f"three-way α={alpha}, β={beta}": (p <= alpha, (p > alpha) & (p <= alpha + beta))}
    rows = []
    for name, (alarm, review) in rules.items():
        def prec(m):
            return float(np.sum(wn * (m & y)) / np.sum(wn * m)) if np.sum(wn * m) > 0 else np.nan
        rows.append({"rule": name,
                     "benign_immediate_alarm": float(np.mean(alarm[~y])), "benign_review": float(np.mean(review[~y])),
                     "attack_immediate_alarm": float(np.mean(alarm[y])), "attack_review": float(np.mean(review[y])),
                     "attack_missed": float(np.mean(~(alarm | review)[y])),
                     "precision_alarm_tier": prec(alarm), "precision_review_tier": prec(review),
                     "alarms_per_flows": float(np.sum(wn * alarm) * per_flows),
                     "reviews_per_flows": float(np.sum(wn * review) * per_flows)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- validity decision rule (E1)
def theory_betabinom(n_cal: int, n_test: int, level: float, lower: float = 0.0):
    """Theoretical law of the realised benign rate of decisions with p in (lower, level].

    The conditional probability is a spacing of uniform order statistics, Beta(l, n+1-l) with
    l = floor((n+1)*level) - floor((n+1)*lower); the count among n_test benign test points is
    then Beta-Binomial(n_test; l, n_cal + 1 - l)."""
    import math
    l = math.floor((n_cal + 1) * level) - math.floor((n_cal + 1) * lower)
    return stats.betabinom(n_test, l, n_cal + 1 - l), l


def validity_summary(realized: np.ndarray, n_cal: int, n_test: int, level: float,
                     lower: float = 0.0) -> dict:
    """Pre-registered decision rule for E1 (round-2 committee, R3-N1).

    Per-resplit FPR exceeds alpha in ~half of resplits even when the method is valid,
    so 'fraction above alpha' is NOT the test. Instead:
      (a) mean realised rate <= level + 2*SE;
      (b) compare the realised distribution with the theoretical Beta-Binomial law
          BB(n_test; l, n_cal + 1 - l), l = floor((n_cal + 1) * level);
      (c) share of resplits above the 95th percentile of that law should be about 5%.
    """
    realized = np.asarray(realized)
    bb, l = theory_betabinom(n_cal, n_test, level, lower)
    budget = (level - lower) + (1.0 / (n_cal + 1) if lower > 0 else 0.0)
    q95 = bb.ppf(0.95) / n_test
    se = realized.std(ddof=1) / np.sqrt(len(realized)) if len(realized) > 1 else np.nan
    return {"budget": budget, "mean": float(realized.mean()), "se": float(se),
            "rule_a_mean_ok": bool(realized.mean() <= budget + 2 * se),
            "theory_mean": l / (n_cal + 1), "theory_q95": float(q95),
            "share_above_theory_q95": float(np.mean(realized > q95)),
            "rule_c_ok": bool(np.mean(realized > q95) <= 0.10)}


# --------------------------------------------------------------------------- statistics
def bootstrap_ci(values: np.ndarray, repeats: int, seed: int, stat=np.mean) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    v = np.asarray(values)
    boots = [stat(rng.choice(v, size=len(v), replace=True)) for _ in range(repeats)]
    return float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


def paired_wilcoxon_holm(table: pd.DataFrame, a: str, b: str, by: str) -> pd.DataFrame:
    """Paired Wilcoxon (over seeds) of columns a vs b within each group `by`, Holm-corrected."""
    rows = []
    for g, sub in table.groupby(by):
        diff = sub[a].to_numpy() - sub[b].to_numpy()
        if np.allclose(diff, 0):
            p = 1.0
        else:
            p = stats.wilcoxon(sub[a], sub[b]).pvalue
        rows.append({by: g, "median_diff": float(np.median(diff)), "p_raw": float(p), "n": len(sub)})
    res = pd.DataFrame(rows).sort_values("p_raw").reset_index(drop=True)
    m = len(res)
    adj, running = [], 0.0
    for i, p in enumerate(res["p_raw"]):
        running = max(running, min(1.0, (m - i) * p))
        adj.append(running)
    res["p_holm"] = adj
    return res
