"""Phase 10: host-level evidence accumulation for sparse attacks.

Everything upstream is unchanged: the benign-only autoencoder, its benign_cal conformal p-values and the
alpha/beta three-way decision. Phase 10 only replaces the host-level rule ("Rung 2") that turns the flow
p-values of one host into an escalation decision.

Per-flow evidence (all functions of the existing conformal p-value p):
  * flag counts           1{p <= alpha + beta}, 1{p <= alpha}                     (existing counter)
  * Fisher                -log p
  * truncated product     log(tau / p) 1{p <= tau}, tau = alpha + beta
  * binned LR e-value     e(p) = 1 - rho0 + rho0 * r(p)
        r(p) = q(p) / f0(p) is a non-increasing likelihood ratio on fixed p-bins: f0 is the exact null mass of
        each bin for a conformal p-value (uniform on {1/(n+1), ..., 1}); q is the p-value distribution of
        KNOWN attack families on dev_val (validation split; held-out families never used), averaged with
        equal family weights and made monotone by weighted isotonic regression. Because r is non-increasing
        and sum_b f0_b r_b = 1, E[e(p)] <= 1 for any super-uniform p: e is a valid e-value under the
        conformal null. 1 - rho0 + rho0 r(p) is the likelihood ratio of a sparse mixture alternative in which
        a share rho0 of the host's flows are attack flows (Neyman-Pearson optimal per flow for that mixture).
  * mixture calibrator    e(p) = 1 - rho0 + rho0 * f(p), f(p) = (1 - p + p ln p) / (p ln^2 p)
        (Vovk & Wang 2021), a benign-only e-value that uses no attack data at all.

Host-level accumulators:
  window (fixed W flows, decision at the end of the window): count, Fisher, truncated product, min-p (Tippett),
      Higher Criticism (Donoho & Jin 2004), sum of log e-values;
  sequential (decision after every flow, reset after an alarm): Bernoulli CUSUM on the flag, EWMA on the flag
      and on -log p, CUSUM on log e (e-CUSUM), Shiryaev-Roberts on e (e-SR), leaky e-CUSUM (evidence decay),
      and an adaptive mixture of e-SR procedures over a grid of rho0 values.

These are established techniques (Page 1954; Roberts 1966; Shiryaev 1963; Vovk et al. conformal martingales;
Shin, Ramdas & Rinaldo e-detectors). Phase 10 applies and evaluates them on the existing conformal p-values;
it does not claim a new detector.

Calibration: every threshold is set on benign_val only, for the same operational budget B false escalations per
host per week at F flows/day. Window rules: split-conformal quantile on benign windows at alpha_w = B W/(7F)
(as in F5). Sequential rules: smallest threshold whose estimated false-alarm rate per benign flow is
<= B/(7F) on simulated benign_val streams. Theory thresholds (e-detector bound ARL >= 1/a) are also reported.

Version B of TON_IoT has no timestamps: host streams are random draws of a host's flows (a SIMULATION).
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit

# ------------------------------------------------------------------ p-value bins for the likelihood ratio
BIN_EDGES = (0.001, 0.002, 0.005, 0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.5, 1.0)   # upper edges; bin 0 is p = 1/(n+1)
FLAG_EDGES = (0.05, 1.0)                                                       # the existing flag, as two bins


def bin_edges(n_cal: int, edges=BIN_EDGES) -> np.ndarray:
    return np.r_[1.0 / (n_cal + 1), np.asarray(edges, dtype=float)]


def null_mass(n_cal: int, edges: np.ndarray) -> np.ndarray:
    """Exact null probability of each bin for a conformal p-value with n_cal calibration points:
    P(p <= t) = floor(t (n+1)) / (n+1) under exchangeability without ties."""
    F = np.floor(edges * (n_cal + 1) + 1e-9) / (n_cal + 1)
    F[-1] = 1.0
    return np.diff(np.r_[0.0, F])


def bin_index(p: np.ndarray, edges: np.ndarray) -> np.ndarray:
    return np.minimum(np.searchsorted(edges, p - 1e-12, side="left"), len(edges) - 1)


def _pava_decreasing(y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Weighted isotonic regression, non-increasing (pool adjacent violators). Preserves sum(w * y)."""
    vals, wts, cnt = [], [], []
    for yi, wi in zip(y, w):
        vals.append(yi); wts.append(wi); cnt.append(1)
        while len(vals) > 1 and vals[-2] < vals[-1]:
            v2, w2, c2 = vals.pop(), wts.pop(), cnt.pop()
            v1, w1, c1 = vals.pop(), wts.pop(), cnt.pop()
            vals.append((v1 * w1 + v2 * w2) / (w1 + w2)); wts.append(w1 + w2); cnt.append(c1 + c2)
    return np.repeat(vals, cnt)


def fit_likelihood_ratio(p_att: np.ndarray, fam: np.ndarray, mult: np.ndarray, n_cal: int, edges=BIN_EDGES,
                         smooth: float = 0.01) -> dict:
    """r_b = q_b / f0_b on the bins, from known-attack validation p-values (equal weight per family)."""
    e = bin_edges(n_cal, edges)
    f0 = null_mass(n_cal, e)
    keep = f0 > 0                     # a bin without any conformal p-value value (small n_cal) is merged upward;
    e, f0 = e[keep], f0[keep]         # no p-value, benign or attack, can fall in it (all lie on k/(n+1))
    qs = []
    for f in np.unique(fam):
        m = fam == f
        b = bin_index(p_att[m], e)
        q = np.bincount(b, weights=mult[m], minlength=len(e)).astype(float)
        q = q / q.sum()
        qs.append((1 - smooth) * q + smooth * f0)          # never zero: r >= smooth
    q = np.mean(qs, axis=0)
    r = _pava_decreasing(q / f0, f0)
    return {"edges": e, "f0": f0, "q": q, "r": r, "check_sum_f0_r": float(np.sum(f0 * r))}


def lr_evalue(p: np.ndarray, lr: dict, rho0: float) -> np.ndarray:
    return 1.0 - rho0 + rho0 * lr["r"][bin_index(p, lr["edges"])]


def mixture_calibrator(p: np.ndarray) -> np.ndarray:
    """Vovk & Wang (2021) 'simple mixture' p-to-e calibrator: integral over kappa in (0,1) of kappa p^(kappa-1)."""
    p = np.clip(np.asarray(p, dtype=float), 1e-300, 1 - 1e-9)
    lp = np.log(p)
    return (1.0 - p + p * lp) / (p * lp * lp)


# ------------------------------------------------------------------ window statistics (larger = more anomalous)
def window_stat(name: str, P: np.ndarray, aux: dict) -> np.ndarray:
    """P: (n_windows, W) p-values."""
    W = P.shape[1]
    if name == "W_COUNT_AU":
        return (P <= aux["ab"]).sum(1).astype(float)
    if name == "W_COUNT_A":
        return (P <= aux["a"]).sum(1).astype(float)
    if name == "W_FISHER":
        return -np.log(P).sum(1)
    if name == "W_TPM":
        t = aux["ab"]
        return np.where(P <= t, np.log(t / P), 0.0).sum(1)
    if name == "W_MINP":
        return -np.log(P.min(1))
    if name == "W_HC":
        S = np.sort(P, axis=1)
        i = np.arange(1, W + 1)[None, :]
        ok = (i <= W / 2) & (S > 1.0 / W)
        hc = np.sqrt(W) * (i / W - S) / np.sqrt(S * (1 - S) + 1e-300)
        hc = np.where(ok, hc, -np.inf).max(1)
        return np.where(np.isfinite(hc), hc, -1e9)
    if name == "W_EVID":
        return np.log(aux["e_lr"](P)).sum(1)
    raise KeyError(name)


def conformal_threshold(T_cal: np.ndarray, a: float) -> float:
    """Smallest t with (1 + #{T_cal >= t}) / (n + 1) <= a; alarm iff T >= t (ties counted against us).
    Identical to resolution.k_threshold for integer counts."""
    T = np.sort(np.asarray(T_cal, dtype=float))[::-1]
    n = len(T)
    m = int(math.floor(a * (n + 1) + 1e-9)) - 1            # largest allowed #{T_cal >= t}
    if n == 0:
        return np.inf
    if m < 0:                                              # budget unattainable with n windows: alarm only above
        return float(np.nextafter(T[0], np.inf))          # every calibration value (as resolution.k_threshold)
    if m >= n:
        return -np.inf
    return float(np.nextafter(T[m], np.inf))


# ------------------------------------------------------------------ sequential kernels (numba)
# kind: 0 CUSUM  s = max(0, s + x)            alarm s >= h
#       1 LEAKY  s = max(0, g s + x)          alarm s >= h       (par = g, evidence decay)
#       2 SR     L = x + log(1 + exp(L))      alarm L >= h       (L = log R, Shiryaev-Roberts)
#       3 EWMA   s = (1 - lam) s + lam x      alarm s >= h       (par = lam, start = s0)
@njit(cache=True)
def _step(kind, s, x, par):
    if kind == 0:
        s = s + x
        return s if s > 0.0 else 0.0
    if kind == 1:
        s = par * s + x
        return s if s > 0.0 else 0.0
    if kind == 2:
        if s > 30.0:
            return x + s + math.log1p(math.exp(-s))
        return x + math.log1p(math.exp(s))
    return (1.0 - par) * s + par * x


@njit(cache=True)
def _start(kind, s0):
    if kind == 2:
        return -1e9          # log R_0 = log 0
    if kind == 3:
        return s0
    return 0.0


@njit(cache=True)
def run_streams(x, ids, kind, par, s0, h, s_init, use_init):
    """Run detectors with reset after each alarm. ids: (n, L) row ids into x.
    Returns final state, number of alarms, first alarm time (1-based, 0 = none)."""
    n, L = ids.shape
    s_out = np.empty(n)
    n_al = np.zeros(n, dtype=np.int64)
    first = np.zeros(n, dtype=np.int64)
    st = _start(kind, s0)
    for i in range(n):
        s = s_init[i] if use_init else st
        for t in range(L):
            s = _step(kind, s, x[ids[i, t]], par)
            if s >= h:
                n_al[i] += 1
                if first[i] == 0:
                    first[i] = t + 1
                s = st
        s_out[i] = s
    return s_out, n_al, first


@njit(cache=True)
def max_stat(x, ids, kind, par, s0):
    n, L = ids.shape
    out = np.empty(n)
    st = _start(kind, s0)
    for i in range(n):
        s = st
        m = -1e18
        for t in range(L):
            s = _step(kind, s, x[ids[i, t]], par)
            if s > m:
                m = s
        out[i] = m
    return out


@njit(cache=True)
def first_passage(x, ids, kind, par, s0, grid):
    """First time the statistic (no reset) reaches each grid level; 0 = not reached within L."""
    n, L = ids.shape
    G = len(grid)
    T = np.zeros((n, G), dtype=np.int64)
    st = _start(kind, s0)
    for i in range(n):
        s = st
        j = 0
        for t in range(L):
            s = _step(kind, s, x[ids[i, t]], par)
            while j < G and s >= grid[j]:
                T[i, j] = t + 1
                j += 1
            if j == G:
                break
    return T


# --- adaptive mixture of SR procedures over a rho0 grid: R = mean_j R_j (an average of e-detectors)
@njit(cache=True)
def _mix_stat(L):
    m = L.max()
    acc = 0.0
    for j in range(len(L)):
        acc += math.exp(L[j] - m)
    return m + math.log(acc / len(L))


@njit(cache=True)
def run_streams_mix(X, ids, h, S_init, use_init):
    J = X.shape[0]
    n, L = ids.shape
    S_out = np.empty((n, J))
    n_al = np.zeros(n, dtype=np.int64)
    first = np.zeros(n, dtype=np.int64)
    for i in range(n):
        Ls = S_init[i].copy() if use_init else np.full(J, -1e9)
        for t in range(L):
            for j in range(J):
                Ls[j] = _step(2, Ls[j], X[j, ids[i, t]], 0.0)
            if _mix_stat(Ls) >= h:
                n_al[i] += 1
                if first[i] == 0:
                    first[i] = t + 1
                Ls[:] = -1e9
        S_out[i] = Ls
    return S_out, n_al, first


@njit(cache=True)
def max_stat_mix(X, ids):
    J = X.shape[0]
    n, L = ids.shape
    out = np.empty(n)
    for i in range(n):
        Ls = np.full(J, -1e9)
        m = -1e18
        for t in range(L):
            for j in range(J):
                Ls[j] = _step(2, Ls[j], X[j, ids[i, t]], 0.0)
            v = _mix_stat(Ls)
            if v > m:
                m = v
        out[i] = m
    return out


@njit(cache=True)
def first_passage_mix(X, ids, grid):
    J = X.shape[0]
    n, L = ids.shape
    G = len(grid)
    T = np.zeros((n, G), dtype=np.int64)
    for i in range(n):
        Ls = np.full(J, -1e9)
        j = 0
        for t in range(L):
            for k in range(J):
                Ls[k] = _step(2, Ls[k], X[k, ids[i, t]], 0.0)
            v = _mix_stat(Ls)
            while j < G and v >= grid[j]:
                T[i, j] = t + 1
                j += 1
            if j == G:
                break
    return T


def rate_from_passage(T: np.ndarray, L: int) -> tuple[np.ndarray, np.ndarray]:
    """Per grid level: number of first passages and exposure (flows observed until passage or censoring).
    Rate per flow = passages / exposure (exponential approximation of the run length; conservative +1 applied
    by the caller)."""
    hit = T > 0
    exposure = np.where(hit, T, L).sum(0).astype(float)
    return hit.sum(0).astype(float), exposure
