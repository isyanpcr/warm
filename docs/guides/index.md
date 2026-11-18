---
description: Decision tables for choosing a search path, a vector search mode and a build profile, with links to the guide for each task.
---

# Guides

## Which search do I use?

| You want | Call | Ranks with | Page |
|---|---|---|---|
| Passages from text, with byte offsets | `search_documents` | Stemmed BM25; plus exact cosine over embeddings you supply (hybrid). Scans eligible chunks | [Quickstart](../quickstart/index.md) |
| Facts that change over time | `remember`, `recall`, `forget`, `explain` | Document search, then a validity and supersession filter | [Memory API](../memory-api/README.md) |
| Nearest neighbours of a dense vector | `search_vectors` | `exact`: sequential `f64` cosine. `graph`: approximate candidates, canonical scores. `auto`: the engine picks the route | [Retrieval contracts](retrieval-contracts.md) |
| Learned-sparse vectors you encode yourself | `search_documents_ranked` | `lexical`, `sparse` or `fused` | [Learned-sparse ranking](sparse-ranking.md) |
| Relational and multi-hop queries over triples | Meaning memory | Bound hypervectors and Hopfield cleanup | [Holographic](../concepts/holographic.md) |

## Which vector-index build profile?

`BuildParams::profile` selects the insertion passes. Times are relative to `max-recall`; the
measurements are in [Build profiles](../benchmarks/BUILD-PROFILES.md).

| Profile | Build time | Pick it when |
|---|---|---|
| `standard` (default) | about 0.3x | Unsure |
| `max-recall` | 1x | Highest recall matters more than build time (the schedule of releases up to 0.6.8) |
| `high` | about 0.58x | |
| `balanced` | about 0.45x | |
| `fast` | about 0.20x | Build time matters most |

## Task guides

| Task | Page |
|---|---|
| Check search quality on your own questions | [Evaluate search](evaluate-search.md) |
| Encode DNA and RNA k-mers (experimental) | [K-mer encoder](kmer-encoder.md) |
| Check compatibility after the October 2026 audit fixes | [Audit-fix migrations](audit-fix-migrations.md) |
| Use local embeddings | [Embeddings](../embeddings/README.md) |
