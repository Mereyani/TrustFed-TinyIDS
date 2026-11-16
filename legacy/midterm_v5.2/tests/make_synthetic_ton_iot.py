"""Generate a small SYNTHETIC file with the TON_IoT network schema, for smoke tests only.

It is NOT TON_IoT. It exists so the notebooks can be executed end-to-end before the real
file is available. Never report numbers obtained on this file.

Usage: python tests/make_synthetic_ton_iot.py OUT.csv [n_normal] [n_per_attack]
"""
import sys

import numpy as np
import pandas as pd

ATTACKS = ["backdoor", "ddos", "dos", "injection", "password", "scanning", "ransomware", "xss", "mitm"]


def make(n_normal=6000, n_attack=800, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    services = ["-", "dns", "http", "ssl", "ftp"]
    protos = ["tcp", "udp", "icmp"]
    states = ["SF", "S0", "REJ", "RSTO", "OTH", "SH"]

    def block(kind, n, shift):
        k = n if kind != "mitm" else max(60, n // 8)
        df = pd.DataFrame({
            "ts": np.sort(rng.integers(1_554_000_000, 1_556_000_000, k)),
            "src_ip": rng.choice([f"192.168.1.{i}" for i in range(1, 60)], k),
            "src_port": rng.integers(1024, 65535, k),
            "dst_ip": rng.choice([f"10.0.0.{i}" for i in range(1, 30)], k),
            "dst_port": rng.choice([53, 80, 443, 21, 8080, 22], k),
            "proto": rng.choice(protos, k, p=[0.6, 0.35, 0.05]),
            "service": rng.choice(services, k),
            "duration": np.abs(rng.lognormal(-2 + shift, 1.0, k)),
            "src_bytes": rng.lognormal(5 + shift, 1.2, k).astype(int),
            "dst_bytes": rng.lognormal(6 - shift, 1.2, k).astype(int),
            "conn_state": rng.choice(states, k, p=[0.5, 0.2, 0.1, 0.1, 0.05, 0.05] if shift == 0 else None),
            "missed_bytes": (rng.random(k) < 0.02).astype(int) * rng.integers(1, 500, k),
            "src_pkts": rng.poisson(5 + 3 * shift, k),
            "src_ip_bytes": rng.lognormal(6 + shift, 1.0, k).astype(int),
            "dst_pkts": rng.poisson(4, k),
            "dst_ip_bytes": rng.lognormal(6, 1.0, k).astype(int),
            "dns_query": rng.choice(["-", "example.com", "iot.local", "api.vendor.net"], k),
            "dns_qclass": rng.choice([0, 1], k),
            "dns_qtype": rng.choice([0, 1, 28], k),
            "dns_rcode": rng.choice([0, 3], k),
            "dns_AA": rng.choice(["-", "T", "F"], k),
            "dns_RD": rng.choice(["-", "T", "F"], k),
            "dns_RA": rng.choice(["-", "T", "F"], k),
            "dns_rejected": rng.choice(["-", "T", "F"], k),
            "ssl_version": rng.choice(["-", "TLSv12", "TLSv13"], k),
            "ssl_cipher": rng.choice(["-", "TLS_AES_128_GCM_SHA256"], k),
            "ssl_resumed": rng.choice(["-", "T", "F"], k),
            "ssl_established": rng.choice(["-", "T", "F"], k),
            "ssl_subject": "-", "ssl_issuer": "-",
            "http_trans_depth": rng.choice(["-", "1", "2"], k),
            "http_method": rng.choice(["-", "GET", "POST"], k),
            "http_uri": rng.choice(["-", "/", "/index.php", "/login"], k),
            "http_version": rng.choice(["-", "1.1"], k),
            "http_request_body_len": rng.integers(0, 2000, k),
            "http_response_body_len": rng.integers(0, 5000, k),
            "http_status_code": rng.choice([0, 200, 404], k),
            "http_user_agent": "-", "http_orig_mime_types": "-", "http_resp_mime_types": "-",
            "weird_name": "-", "weird_addl": "-", "weird_notice": rng.choice(["-", "F"], k),
            "label": 0 if kind == "normal" else 1,
            "type": kind,
        })
        return df

    rows.append(block("normal", n_normal, 0.0))
    for i, a in enumerate(ATTACKS):
        rows.append(block(a, n_attack, 0.4 + 0.15 * i))
    df = pd.concat(rows, ignore_index=True)
    dup = df.sample(frac=0.03, random_state=seed)
    # label collisions so the collision code paths are exercised: copy some benign rows and
    # relabel them as an attack (dev) and as a held-out family
    coll = []
    for fam in ["scanning", "xss"]:
        c = df[df["type"] == "normal"].sample(25, random_state=seed + len(fam)).copy()
        c["type"], c["label"] = fam, 1
        coll.append(c)
    return pd.concat([df, dup] + coll, ignore_index=True).sample(frac=1.0, random_state=seed)


if __name__ == "__main__":
    out = sys.argv[1]
    n_normal = int(sys.argv[2]) if len(sys.argv) > 2 else 6000
    n_attack = int(sys.argv[3]) if len(sys.argv) > 3 else 800
    make(n_normal, n_attack).to_csv(out, index=False)
    print("wrote", out)
