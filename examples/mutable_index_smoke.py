# Copyright 2024-2026 WritersLogic Contributors
# SPDX-License-Identifier: Apache-2.0
"""Smoke run of MutableIndex: insert, delete, refill (forcing repair scans) and score recall
against brute force over the live rows. Observational only: one seed, one run, no threshold
beyond a sanity floor. Usage: mutable_index_smoke.py [n=20000] [dim=32] [metric=euclidean]."""

import sys
import time

import numpy as np

from writerslogic_warm import MutableIndex

K = 10


def brute_force(rows, ids, queries, metric):
    if metric == "euclidean":
        d = (queries**2).sum(1)[:, None] - 2.0 * queries @ rows.T + (rows**2).sum(1)[None, :]
    else:
        r = rows / np.linalg.norm(rows, axis=1, keepdims=True)
        q = queries / np.linalg.norm(queries, axis=1, keepdims=True)
        d = 1.0 - q @ r.T
    return ids[np.argsort(d, axis=1)[:, :K]], np.sort(d, axis=1)[:, :K]


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20_000
    dim = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    metric = sys.argv[3] if len(sys.argv) > 3 else "euclidean"
    rng = np.random.default_rng(7)
    pool = rng.normal(size=(2 * n, dim)).astype(np.float32)  # rows 0..n first, the rest refill
    queries = rng.normal(size=(500, dim)).astype(np.float32)
    index = MutableIndex.create(n, dim, metric=metric, degree=32, build_ef=64, threads=4)
    live = {}  # id -> row index in pool

    def insert(lo, hi):
        ids = np.arange(lo, hi, dtype=np.uint32)
        index.insert(ids, pool[lo:hi])
        live.update((int(i), int(i)) for i in ids)

    def delete(count):
        victims = rng.choice(np.fromiter(live, dtype=np.int64), size=count, replace=False)
        index.delete(victims.astype(np.uint32))
        for v in victims:
            del live[int(v)]

    t0 = time.perf_counter()
    step = n // 10
    for lo in range(0, n, step):
        insert(lo, lo + step)
    t_build = time.perf_counter() - t0
    assert len(index) == n and index.stats()["free"] == 0
    t0 = time.perf_counter()
    nxt = n
    for _ in range(4):  # churn: delete a quarter, then refill it from the unseen rows
        delete(n // 4)
        insert(nxt, nxt + n // 4)  # no free slot is left, so this runs a repair scan first
        nxt += n // 4
    t_churn = time.perf_counter() - t0
    stats = index.stats()
    assert len(index) == n and stats["scans"] >= 4, stats

    ids = np.fromiter(live, dtype=np.int64)
    rows = pool[np.fromiter(live.values(), dtype=np.int64)]
    truth, truth_d = brute_force(rows, ids, queries, metric)
    print(f"n={n} dim={dim} metric={metric} build {t_build:.1f}s churn {t_churn:.1f}s stats={stats}")
    for ef in (32, 64, 128, 256):
        t0 = time.perf_counter()
        got, d = index.search(queries, K, ef)
        qt = time.perf_counter() - t0
        assert got.shape == (len(queries), K) and d.shape == got.shape
        assert all(int(i) in live for i in got.ravel()), "search returned a deleted id"
        recall = np.mean([len(set(g) & set(t)) / K for g, t in zip(got, truth)])
        # the reported distance of the true top-1 hit must match brute force
        top = got[:, 0] == truth[:, 0]
        err = np.abs(d[top, 0] - truth_d[top, 0]).max() if top.any() else float("nan")
        print(f"ef={ef:4d} recall@{K}={recall:.4f} search {qt * 1e3:.0f} ms/500q max|d-d_bf| {err:.2e}")
    index.delete(np.fromiter(live, dtype=np.uint32))
    assert len(index) == 0 and (index.search(queries[:1], K)[0] == -1).all()
    print("empty after deleting everything:", index.stats())
    print("OK")


if __name__ == "__main__":
    main()
