# L10 stage 1: in-place mutable base

Stage 1 of the streaming "in-place mutable base" (design note sections 2.3, 2.7 and 2.8). It is an in-RAM prototype that sits beside the generational path (`UpdatableVGraph`), which it does not touch. Code: `src/core/qgraph/update/mutable.rs`, tests in `src/core/qgraph/update/mutable/tests.rs`.

## What exists

`MutableBase` (re-exported from `qgraph` with `MutableOptions`, `MutableStats`, `ScanStats`):

- `MutableBase::new(dim, &BuildParams, &MutableOptions)`; `BuildParams` supplies `degree` (R), `build_ef`, `alpha` and `metric`.
- Slot arrays sized to capacity `C = ceil(max_pts * (1 + slack))`: `Adjacency` (len word + R x u32), f32 rows, squared norms (Euclidean), optional 8-bit `BuildCodes` with scale (`build_codes`), `slot_to_id`, tombstone bitset, routing tree (`first_child`, `next_sibling`).
- `id_to_slot`: two-level direct table, 2^16-entry pages allocated on first use.
- Free list: slots freed by a scan in a min-heap plus a high-water mark for never-used slots, so the lowest free slot is always taken first and slot choice is a function of the op sequence.
- `insert_batch(ids, vectors)`: all or none. Takes free slots in ascending order; if there are too few it runs a repair scan first, and returns `Capacity` (state unchanged) when `free + dead` is still short. Then `Rows::insert_pass` runs over the live and dead graph (frozen batches, reverse edges pruned once per target), and each new slot is linked into the routing tree under an earlier neighbour.
- `delete_batch(ids)` / `delete(id)`: tombstone the slot, clear `id_to_slot` and `slot_to_id`. The slot keeps routing.
- `search(query, k, ef)`: best-first from the entry over list and routing-tree edges. Dead slots are traversed and expanded; only live slots are admitted to the result set (`ef` best live). Scores are exact f32 (angular `-<q,x>`, Euclidean `|x|^2/2 - <q,x>`), so no separate rescore step is needed in this slice.
- `repair_scan()`: for every live slot whose list names a dead slot, candidates are its live neighbours plus the live out-neighbours of its dead neighbours, pruned once with `alpha` (no second pass, no `again[]`). Only after every list is repaired are the dead slots cleared and pushed to the free list (I2). Then the entry is re-elected if dead, and the routing tree is rebuilt as a BFS spanning tree of the lists; a live slot the lists no longer reach is searched for and attached under its nearest reachable slot.
- `verify(after_scan)`: I1, I2, I3, I4, I6 checks (see tests). `repair_scan` runs it under `debug_assertions`.

## Knob names (design note 2.7)

| Knob | Where | Stage 1 |
|---|---|---|
| `capacity` from `max_pts`, `slack` | `MutableOptions::max_pts`, `slack` | implemented, slack default 0.0 |
| `dead_trigger` | `MutableOptions::dead_trigger` | implemented: scan after a delete when dead / (live + dead) reaches it; 0 means scan only when an insert needs slots |
| `repair_ld`, `repair_c` | `MutableOptions` | present; `repair_ld` default 0, nonzero is rejected at construction |
| `build_codes` | `MutableOptions::build_codes` | `None` follows the build gate (on from 128 dims) |
| `stats()` | `MutableBase::stats` | slots by state, scans, repaired rows, freed slots, orphans |

## Deferred

- Persistence: `updates.log` replay, `checkpoint()`, mmap-backed rows, I5 fingerprint after replay from a checkpoint. A plain determinism check (same ops, same state) is in the tests.
- Wiring into `UpdatableVGraph` (`ConsolidationMode::Repair`, `ConsolidationPolicy::dead_trigger`), the Python binding and the harness adapter.
- Bounded delete-time in-neighbour recovery (`repair_ld`).
- Production search kernels over writable slabs (this slice searches the f32 rows), residual codes, 3-byte packed adjacency, R64 code-distance prune.
- Concurrent readers and versioned edges (stage 4); the type needs `&mut self` for every write.
- Re-computing quantization state at a scan (the codes are per-row scaled here, so there is no fixed mean to drift).
- Dead candidates are not filtered from the insert pass, so a new row's list can name dead slots until the next scan.
- Allocation per repaired list in the scan, and an O(C) `closed` array per `insert_pass` call; neither is tuned.
- Id table hash fallback when pages would exceed a budget.

## Running the tests

```sh
export CARGO_TARGET_DIR=/Volumes/A/.hms-wt-levers/.target
cargo test --lib mutable                              # all stage 1 tests
cargo test --lib mutable -- --nocapture --test-threads=1   # also prints recall and scan stats
cargo build && cargo build --all-features
cargo clippy --all-targets -- -D warnings
```

Tests: random op sequences at N about 5k (Euclidean dim 16, angular dim 32) checking I1, I2, I6 after every op, I2 strict and I3 connectivity after every scan, an exhaustive-ef search equal to brute force while dead slots exist, and a recall report against brute force on the final state (printed, with no threshold); determinism and codes-on/off graph equality; lowest-free-slot reuse after a scan; capacity limit-1, limit, limit+1 with unchanged state on refusal; delete-everything; `dead_trigger`; input refusals.

## Measured

Base `af8d4017`, debug test profile, Apple silicon, one 100-query set per run scored at every ef, k = 10, random op sequence (seeded, capacity 5000, R 16, build_ef 48, alpha 1.0, build codes off). Recall is against brute force over the live set on the final state. Single seed and single run each: these are data points, not a claim about other N, dims or op mixes. Source: `cargo test --lib mutable -- --nocapture --test-threads=1`.

| Metric, dim | live at end | scans | repaired lists | freed slots | orphans attached | recall@10 ef 32 / 64 / 128 |
|---|---|---|---|---|---|---|
| Euclidean, 16 | 4,891 | 22 | 36,289 | 8,693 | 34 | 0.9930 / 1.0000 / 1.0000 |
| Angular, 32 | 2,929 | 23 | 45,620 | 9,784 | 194 | 0.9910 / 0.9960 / 0.9970 |

After a final explicit scan on the same queries: Euclidean 0.9920 / 1.0000 / 1.0000, angular 0.9900 / 0.9970 / 0.9970. A search with ef equal to capacity returns the exact top 10 at every checkpoint, including with dead slots present.

Not measured: build or search speed, memory, dim 100, N above 5k, any streaming runbook. This slice is not evidence for the kill test in design note 2.9.
