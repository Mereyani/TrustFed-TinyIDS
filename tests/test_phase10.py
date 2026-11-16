"""Unit tests for trustids.phase10 (host-level evidence accumulation)."""
import sys
from pathlib import Path

import numpy as np

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root / "TrustFed-TinyIDS-Final" if (_root / "TrustFed-TinyIDS-Final").exists() else _root))
from trustids import phase10 as P10, resolution as R  # noqa: E402


def _lr(seed=0, n_cal=999):
    rng = np.random.default_rng(seed)
    p = np.r_[rng.uniform(0, 0.02, 3000), rng.uniform(0, 1, 2000)]
    p = np.maximum(np.ceil(p * (n_cal + 1)) / (n_cal + 1), 1 / (n_cal + 1))
    fam = np.r_[np.repeat("a", 3000), np.repeat("b", 2000)]
    return P10.fit_likelihood_ratio(p, fam, np.ones(len(p)), n_cal), n_cal


def test_null_mass_sums_to_one():
    e = P10.bin_edges(3348)
    assert abs(P10.null_mass(3348, e).sum() - 1) < 1e-12


def test_lr_is_nonincreasing_and_normalised():
    lr, _ = _lr()
    assert np.all(np.diff(lr["r"]) <= 1e-12)
    assert abs(np.sum(lr["f0"] * lr["r"]) - 1) < 1e-9


def test_evalue_valid_under_discrete_uniform_null():
    lr, n = _lr()
    grid = np.arange(1, n + 2) / (n + 1)                 # every conformal p-value, equally likely under H0
    for rho0 in (0.01, 0.05, 0.25, 1.0):
        assert P10.lr_evalue(grid, lr, rho0).mean() <= 1 + 1e-9


def test_evalue_valid_under_superuniform_null():
    lr, n = _lr()
    grid = np.arange(1, n + 2) / (n + 1)
    p = np.minimum(1.0, grid + 0.05)                     # stochastically larger than uniform
    assert P10.lr_evalue(p, lr, 0.1).mean() <= 1 + 1e-9


def test_mixture_calibrator_integrates_to_one():
    # antiderivative of f is (p - 1) / ln p, so the mass on (0, d) is (d - 1) / ln d and the total is 1
    d = 1e-6
    u = d + (1 - d) * (np.arange(1, 2_000_001) - 0.5) / 2_000_000
    body = P10.mixture_calibrator(u).mean() * (1 - d)
    assert abs(body + (d - 1) / np.log(d) - 1) < 2e-3


def test_conformal_threshold_matches_existing_k_threshold():
    rng = np.random.default_rng(1)
    for _ in range(50):
        K = rng.integers(0, 15, rng.integers(5, 400))
        a = rng.choice([0.001, 0.01, 0.03, 0.1, 0.5])
        k = R.k_threshold(K, a)
        t = P10.conformal_threshold(K.astype(float), a)
        for v in range(0, 17):
            assert (v >= k) == (v >= t)


def _py(kind, xs, par, s0, h):
    s = -1e9 if kind == 2 else (s0 if kind == 3 else 0.0)
    st, n_al, first = s, 0, 0
    for t, x in enumerate(xs):
        if kind == 0:
            s = max(0.0, s + x)
        elif kind == 1:
            s = max(0.0, par * s + x)
        elif kind == 2:
            s = x + np.log1p(np.exp(s)) if s < 30 else x + s + np.log1p(np.exp(-s))
        else:
            s = (1 - par) * s + par * x
        if s >= h:
            n_al += 1
            first = first or t + 1
            s = st
    return n_al, first


def test_kernels_match_reference():
    rng = np.random.default_rng(2)
    x = rng.normal(-0.05, 1.0, 500)
    ids = rng.integers(0, 500, (3, 400))
    for kind, par, s0, h in [(0, 0, 0, 3.0), (1, 0.9, 0, 2.0), (2, 0, 0, 4.0), (3, 0.1, 0.0, 0.5)]:
        _, n_al, first = P10.run_streams(x, ids, kind, par, s0, h, np.zeros(3), False)
        for i in range(3):
            a, f = _py(kind, x[ids[i]], par, s0, h)
            assert n_al[i] == a and first[i] == f


def test_mixture_sr_equals_single_sr_when_one_component():
    rng = np.random.default_rng(3)
    x = rng.normal(-0.05, 1.0, 300)
    ids = rng.integers(0, 300, (2, 250))
    a = P10.run_streams(x, ids, 2, 0.0, 0.0, 3.0, np.zeros(2), False)[1]
    b = P10.run_streams_mix(x[None, :], ids, 3.0, np.zeros((2, 1)), False)[1]
    assert np.array_equal(a, b)


def test_max_of_pvalues_is_superuniform():
    rng = np.random.default_rng(4)
    p1 = rng.uniform(size=200_000)                       # valid
    p2 = rng.uniform(size=200_000) ** 3                  # invalid (anti-conservative)
    m = np.maximum(p1, p2)
    for u in (0.001, 0.01, 0.05, 0.2):
        assert np.mean(m <= u) <= u + 3 * np.sqrt(u / 200_000)
