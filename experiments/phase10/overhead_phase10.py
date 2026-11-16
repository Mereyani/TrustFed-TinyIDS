"""Phase 10 computational and memory overhead of the host-level rules.

Measures the per-flow update time of each rule on THIS machine (numba-compiled scalar loop over one host
stream; not a microcontroller measurement) and reports the per-host state and lookup-table sizes as they would
be stored in a C implementation (float32 state, uint8 bin indices). Output: results/overhead.csv
"""
from __future__ import annotations

import platform
import sys
import time
from pathlib import Path

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "TrustFed-TinyIDS-Final"))
from trustids import phase10 as P10  # noqa: E402

N_FLOWS = 2_000_000
N_BINS = len(P10.BIN_EDGES) + 1           # 12 bins


@njit(cache=True)
def window_count(flag, W, k):
    buf = np.zeros(W, np.uint8)
    c = 0
    al = 0
    for t in range(len(flag)):
        j = t % W
        c += flag[t] - buf[j]
        buf[j] = flag[t]
        if j == W - 1 and c >= k:
            al += 1
    return al


@njit(cache=True)
def window_evid(b, lut, W, h):
    buf = np.zeros(W, np.uint8)
    s = 0.0
    al = 0
    for t in range(len(b)):
        j = t % W
        s += lut[b[t]] - lut[buf[j]]
        buf[j] = b[t]
        if j == W - 1 and s >= h:
            al += 1
    return al


@njit(cache=True)
def window_hc(p, W, h):
    buf = np.zeros(W)
    al = 0
    for t in range(len(p)):
        j = t % W
        buf[j] = p[t]
        if j == W - 1:
            s = np.sort(buf)
            m = -1e9
            for i in range(W // 2):
                if s[i] > 1.0 / W:
                    v = np.sqrt(W) * ((i + 1) / W - s[i]) / np.sqrt(s[i] * (1 - s[i]))
                    if v > m:
                        m = v
            if m >= h:
                al += 1
    return al


@njit(cache=True)
def seq_cusum(b, lut, h):
    s = 0.0
    al = 0
    for t in range(len(b)):
        s = s + lut[b[t]]
        if s < 0.0:
            s = 0.0
        if s >= h:
            al += 1
            s = 0.0
    return al


@njit(cache=True)
def seq_sr(b, elut, h):
    r = 0.0
    al = 0
    for t in range(len(b)):
        r = (1.0 + r) * elut[b[t]]
        if r >= h:
            al += 1
            r = 0.0
    return al


@njit(cache=True)
def seq_sr_adapt(b, elut2d, h):
    J = elut2d.shape[0]
    r = np.zeros(J)
    al = 0
    for t in range(len(b)):
        m = 0.0
        for j in range(J):
            r[j] = (1.0 + r[j]) * elut2d[j, b[t]]
            m += r[j]
        if m / J >= h:
            al += 1
            r[:] = 0.0
    return al


@njit(cache=True)
def seq_ewma(x, lam, s0, h):
    s = s0
    al = 0
    for t in range(len(x)):
        s = (1 - lam) * s + lam * x[t]
        if s >= h:
            al += 1
            s = s0
    return al


@njit(cache=True)
def binning(p, edges):
    out = np.empty(len(p), np.uint8)
    for t in range(len(p)):
        lo, hi = 0, len(edges) - 1
        while lo < hi:                       # binary search over 12 edges
            mid = (lo + hi) // 2
            if p[t] <= edges[mid]:
                hi = mid
            else:
                lo = mid + 1
        out[t] = lo
    return out


def timeit(fn, *a, rep=5):
    fn(*a)                                   # compile
    best = 1e9
    for _ in range(rep):
        t = time.perf_counter()
        fn(*a)
        best = min(best, time.perf_counter() - t)
    return best / N_FLOWS * 1e9


def main():
    rng = np.random.default_rng(0)
    p = rng.uniform(1 / 3349, 1, N_FLOWS)
    edges = P10.bin_edges(3348)
    b = binning(p, edges)
    lut = rng.normal(-0.02, 0.5, N_BINS)
    elut = np.exp(lut)
    flag = (p <= 0.05).astype(np.uint8)
    rows = []
    t_bin = timeit(binning, p, edges)
    rows.append(("p-value -> bin (binary search, 12 edges)", "shared", t_bin, 0, 4 * N_BINS))
    for W in [20, 200]:
        rows.append((f"W_COUNT_AU, W={W}", "window", timeit(window_count, flag, W, 10), int(np.ceil(W / 8)) + 2, 0))
        rows.append((f"W_EVID, W={W}", "window", timeit(window_evid, b, lut, W, 5.0), W + 4, 4 * N_BINS))
        rows.append((f"W_HC, W={W}", "window", timeit(window_hc, p, W, 5.0), 4 * W, 0))
    rows.append(("BCUSUM / E_CUSUM", "sequential", timeit(seq_cusum, b, lut, 8.0), 4, 4 * N_BINS))
    rows.append(("E_SR", "sequential", timeit(seq_sr, b, elut, 3000.0), 4, 4 * N_BINS))
    rows.append(("E_SR_ADAPT (6 components)", "sequential",
                 timeit(seq_sr_adapt, b, np.exp(rng.normal(-0.02, 0.5, (6, N_BINS))), 3000.0), 4 * 6, 4 * 6 * N_BINS))
    rows.append(("EWMA_FLAG", "sequential", timeit(seq_ewma, flag.astype(float), 0.01, 0.05, 0.2), 4, 0))
    import pandas as pd
    df = pd.DataFrame(rows, columns=["rule", "type", "ns_per_flow_this_cpu", "state_bytes_per_host", "table_bytes"])
    df["host_reference_bytes_per_host"] = 4 * len(P10.BIN_EDGES)       # binned host CDF thresholds (ref=host)
    df["cpu"] = platform.processor()
    df["python"] = sys.version.split()[0]
    (HERE / "results").mkdir(exist_ok=True)
    df.to_csv(HERE / "results" / "overhead.csv", index=False)
    sys.stdout.reconfigure(encoding="utf-8")
    print(df.round(2).to_string())


if __name__ == "__main__":
    main()
