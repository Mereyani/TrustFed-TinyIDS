"""Unit tests for the conformal decision layer. Run: python -m pytest tests  (or python tests/test_conformal.py)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trustids import conformal as C  # noqa: E402
from trustids import metrics as MT  # noqa: E402


def test_threshold_rule_equals_pvalue_rule_with_ties():
    rng = np.random.default_rng(0)
    for trial in range(50):
        cal = np.round(rng.exponential(size=rng.integers(200, 3000)), 1)   # heavy ties, like INT8
        test = np.round(rng.exponential(size=2000) * 1.5, 1)
        a, b = [(0.01, 0.04), (0.05, 0.05), (0.02, 0.08)][trial % 3]
        d_p = C.decide(C.conformal_pvalues(cal, test), a, b)
        th = C.thresholds(cal, a, b)
        d_t = C.decide_by_thresholds(test, th["tau_L"], th["tau_H"])
        assert np.array_equal(d_p, d_t), f"mismatch in trial {trial}"


def test_pvalues_are_superuniform_and_randomized_uniform():
    rng = np.random.default_rng(1)
    cal, test = rng.normal(size=5000), rng.normal(size=200000)
    p = C.conformal_pvalues(cal, test)
    for a in [0.01, 0.05, 0.1]:
        assert np.mean(p <= a) <= a + 0.01
    calt, testt = np.round(cal, 1), np.round(test, 1)
    pr = C.randomized_pvalues(calt, testt, seed=0)
    for a in [0.01, 0.05, 0.1]:
        assert abs(np.mean(pr <= a) - a) < 0.01


def test_validity_resplits_match_theory():
    rng = np.random.default_rng(2)
    pool = rng.lognormal(size=6000)
    res = C.validity_resplits(pool, 3000, 0.05, 0.05, R=300, seed=0)
    s = MT.validity_summary(res["fpr"], 3000, res["n_test"], 0.05)
    assert s["rule_a_mean_ok"] and s["rule_c_ok"], s
    u = MT.validity_summary(res["uncertain"], 3000, res["n_test"], 0.10, lower=0.05)
    assert u["rule_a_mean_ok"] and u["rule_c_ok"], u


def test_threshold_rule_equals_pvalue_rule_at_arbitrary_levels():
    rng = np.random.default_rng(3)
    cal, test = rng.normal(size=999), rng.normal(size=5000) * 1.3
    for a in np.linspace(0.003, 0.3, 97):
        b = 0.05
        th = C.thresholds(cal, a, b)
        assert np.array_equal(C.decide(C.conformal_pvalues(cal, test), a, b),
                              C.decide_by_thresholds(test, th["tau_L"], th["tau_H"])), a


def test_matched_coverage_achieves_requested_abstentions():
    rng = np.random.default_rng(4)
    s = rng.lognormal(size=1000)
    tau_H = np.quantile(s, 0.95)
    for k in [0, 1, 10, 100, 500, 949]:
        tl = MT.band_for_abstention(s, tau_H, k)
        d = C.decide_by_thresholds(s, tl, tau_H)
        assert np.sum(d == C.UNCERTAIN) == k, (k, np.sum(d == C.UNCERTAIN))
    st = np.round(s, 1)   # tied scores: never more than requested
    for k in [10, 100, 500]:
        d = C.decide_by_thresholds(st, MT.band_for_abstention(st, tau_H, k), tau_H)
        assert np.sum(d == C.UNCERTAIN) <= k


def test_preprocessor_numeric_columns_survive_dirty_splits():
    import pandas as pd
    from trustids.data import Preprocessor
    train = pd.DataFrame({"a": [str(v) for v in range(200)], "b": ["x", "y"] * 100})
    test = pd.DataFrame({"a": ["5", "-", "junk", "7"] * 10, "b": ["x"] * 40})
    pre = Preprocessor().fit(train, ["a", "b"])
    out = pre.transform(test)
    a_col = pre.feature_names_.index("a")
    assert len(np.unique(out[:, a_col])) > 1   # not collapsed to the median


def test_global_dedup_keeps_one_copy_per_label_and_sums_multiplicity():
    import pandas as pd
    from trustids.config import Config
    from trustids.data import global_dedup
    cfg = Config(project_dir=".")
    fams = ["normal"] + cfg.dev_families + cfg.heldout_families
    rows = []
    for i, f in enumerate(fams):                        # 30 distinct vectors per family
        for j in range(30):
            rows.append({"a": i * 1000 + j, "b": "x", "type": f})
    df = pd.DataFrame(rows)
    dup = df[df["type"] == "normal"].head(5)            # exact duplicates -> multiplicity 2
    coll = df[df["type"] == "normal"].iloc[10:13].assign(type="xss")    # benign/held-out collisions
    df2 = pd.concat([df, dup, coll], ignore_index=True)
    d, rep = global_dedup(df2, ["a", "b"], cfg, max_card=30)
    assert len(d) == len(df) + 3                         # duplicates merged, both collision copies kept
    assert rep["benign_attack_collision_vectors"] == 3
    assert int(d.loc[d["type"] == "normal", "_collision"].sum()) == 0     # flag sits on the attack copy
    assert int(d.loc[d["type"] == "xss", "_collision"].sum()) == 3
    assert int(d.loc[d["type"] == "normal", "_mult"].max()) == 2


def test_plateau_rule_fires_only_when_improvement_is_small():
    from trustids.models import plateau_reached
    fast = list(np.exp(-np.arange(200) / 30.0) + 1.0)        # still improving clearly
    assert not plateau_reached(np.minimum.accumulate(fast[:100]).tolist(), 50, 0.005)
    flat = [1.0] * 60 + [0.9999] * 60                          # converged: < 0.5% over 50 epochs
    assert plateau_reached(np.minimum.accumulate(flat).tolist(), 50, 0.005)
    assert not plateau_reached([1.0] * 30, 50, 0.005)        # too short to judge


def test_weighted_decomposition_sums_to_delta_sr():
    rng = np.random.default_rng(5)
    y = rng.random(5000) < 0.3
    s_ref = rng.normal(size=5000) + 1.5 * y
    s_alt = rng.normal(size=5000) + 1.0 * y
    cal = rng.normal(size=3000)
    d_ref = C.decide(C.conformal_pvalues(cal, s_ref), 0.01, 0.04)
    tau_alt = np.quantile(cal, 0.99)
    for pi in [None, 0.01, 0.1]:
        r = MT.matched_coverage_comparison(y, d_ref, s_alt, tau_alt, pi)
        assert abs(r["delta_false_alarm_part"] + r["delta_miss_part"] - r["delta_sr"]) < 1e-12, (pi, r)
        if pi is None:
            assert r["abstain_ref"] == r["abstain_alt"]
        else:
            assert abs(r["coverage_ref"] - r["coverage_alt"]) < 0.01


def test_tiering_union_equals_binary_at_alpha_plus_beta():
    rng = np.random.default_rng(6)
    y = rng.random(4000) < 0.2
    p = np.clip(rng.random(4000) * np.where(y, 0.2, 1.0), 1e-6, 1)
    t = MT.tiering_vs_binary(y, p, 0.01, 0.04).set_index("rule")
    three = t.loc["three-way α=0.01, β=0.04"]
    wide = t.loc["binary α+β=0.05"]
    narrow = t.loc["binary α=0.01"]
    assert abs(three["attack_immediate_alarm"] + three["attack_review"] - wide["attack_immediate_alarm"]) < 1e-12
    assert abs(three["attack_missed"] - wide["attack_missed"]) < 1e-12
    assert abs(three["precision_alarm_tier"] - narrow["precision_alarm_tier"]) < 1e-12


def test_tie_prone_models_always_use_randomized_pvalues():
    cal, test = np.arange(1000, dtype=float), np.arange(0, 1000, 7, dtype=float)   # no ties at all
    det = C.conformal_pvalues(cal, test)
    assert np.array_equal(C.pvalues(cal, test, seed=1, model="ae"), det)           # continuous -> deterministic
    for m in ["iforest", "latent", "int8"]:
        assert not np.array_equal(C.pvalues(cal, test, seed=1, model=m), det)       # always randomized


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
