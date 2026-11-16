"""Unit tests for the UNCERTAIN-resolution layer. Run: python tests/test_resolution.py"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trustids import resolution as R  # noqa: E402


def test_operational_budget_round_trip():
    for W in [20, 50, 100]:
        for F in [1000, 5000]:
            a = R.window_budget(1.0, W, F)
            assert abs(R.per_week(a, W, F) - 1.0) < 1e-12
    assert abs(R.window_budget(1.0, 20, 5000) - 20 / 35000) < 1e-15


def test_k_threshold_meets_budget_on_exchangeable_windows():
    rng = np.random.default_rng(0)
    for a in [0.01, 0.002]:
        viol = []
        for trial in range(200):
            K_cal = rng.binomial(20, 0.05, size=3000)
            K_test = rng.binomial(20, 0.05, size=20000)
            k = R.k_threshold(K_cal, a)
            viol.append(np.mean(K_test >= k))
        assert np.mean(viol) <= a * 1.1, (a, np.mean(viol))     # marginal guarantee (in expectation)


def test_k_threshold_impossible_budget_never_fires():
    K_cal = np.array([0, 1, 2, 3, 4])
    k = R.k_threshold(K_cal, 0.01)                 # (n+1)*a < 1: no k can meet it
    assert k == 5 and R.min_cal_windows(0.01) == 99


def test_sampled_windows_are_single_host_and_distinct():
    rng = np.random.default_rng(1)
    groups = {"a": np.arange(0, 50), "b": np.arange(50, 60), "c": np.arange(60, 65)}
    win, hosts = R.sample_windows(groups, 8, 300, rng)
    assert win.shape == (300, 8) and set(hosts) <= {"a", "b"}          # c has < W rows
    for w, h in zip(win, hosts):
        assert len(set(w)) == 8 and set(w) <= set(groups[h])
    dw, dh = R.disjoint_windows(groups, 8, rng)
    assert len(dw) == 6 + 1 and len(np.unique(dw)) == dw.size           # 50//8 + 10//8, no overlap


def test_mixed_windows_composition_and_counts():
    rng = np.random.default_rng(2)
    att, ben = np.arange(0, 100), np.arange(100, 400)
    w = R.mixed_windows(att, ben, 20, 0.25, 50, rng)
    assert np.all((w < 100).sum(1) == 5)
    flag = np.zeros(400, bool); flag[:100] = True
    assert np.all(R.counts(flag, w) == 5)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
