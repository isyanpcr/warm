# Retrieval contracts

| Mode | Selects and ranks with |
|---|---|
| `exact` | The same sequential `f64` cosine as document search; stored embeddings remain normalized `f32`. Always keeps the full-dimensional ranking contract. |
| `graph` | Approximate candidates, then canonical scores. Requires an available graph. |
| `auto` | Graph when available; can build or use an exact snapshot. |

Equal scores use document ID and chunk index order.

## Optional Matryoshka candidates

Experimental opt-in. The [fresh native SciFact evaluation](../research/technical-audit-20261029/matryoshka-native-20261102/README.md) qualified neither tested configuration (256 dimensions with 100 candidates; 512 dimensions with 50 candidates): both lost more recall than the preset limits, and host load prevented query timing. Neither is recommended as a default and no latency advantage is established.

For a model trained to keep information in vector prefixes (Qwen3-Embedding-0.6B supports prefixes of 32 through 1024 dimensions per its pinned model card), `WarmConfig::vector_candidates` builds the graph from a normalized prefix and keeps full embeddings for final cosine ranking. This changes retrieval work, not embedding inference cost (inference still generates the full vector once), and is separate from the default BERT-family local embedder.

| `VectorCandidateConfig` field | Range |
|---|---|
| `dimensions` (prefix width) | 1 to the configured embedding width; a full-width prefix is a control with the same shortlist size |
| `rerank_candidates` (shortlist) | 1 to 4,096; when the graph selects candidates, `k` must fit the shortlist |

Set both fields; leaving the option absent keeps the full-width graph. The graph selects candidate chunks on separately L2-normalized prefixes, then WARM reranks them with the original full vectors and canonical scores. Reranking cannot recover a relevant item missing from the shortlist: measure recall against exact search on representative queries before choosing a width or shortlist; truncating a model not trained for prefixes has no quality contract.

The Node API accepts the same policy in the constructor:

```js
const warm = new WarmMemorySystem(4096, storePath, {
  ...fullEmbeddingConfig,
  vectorCandidateDimensions: candidateWidth,
  vectorRerankCandidates: shortlistSize,
})
await warm.memorizeDocuments(documentsWithFullEmbeddings)
await warm.maintainIndices()
const hits = await warm.searchVectors(fullQueryEmbedding, 10, { mode: 'auto', ef: 128 })
const exact = await warm.searchVectors(fullQueryEmbedding, 10, { mode: 'exact' })
```

`fullEmbeddingConfig` supplies the full model, revision and embedding dimensions; the candidate width never replaces that identity, and all supplied document and query vectors must have the full width. The constructor's first argument is WARM's sparse memory dimension, independent of the embedding dimension. Node maintenance builds a graph at 4,096 embedded chunks (smaller stores use exact search in `auto` mode); Rust callers can set another threshold with `rebuild_vector_index`.

Routing and fallbacks:

- `filter`, `sourceUri` and `documentIds` use exact eligibility before full-dimensional top-k selection.
- Projected snapshots with updates or deletions use full exact search until rebuilt; a zero-norm prefix in a stored row or query also falls back to exact search. These routes keep correctness but not projected-search speed.

Rust `search_vectors_with_report` reports the route actually used, candidate width and effective shortlist. `vector_index_status` separates the full embedding identity from prefix normalization and shortlist policy; its graph byte counts cover retained graph buffers (including the separately reported residual subset) and exclude stored full embeddings, text, allocator overhead, build scratch and other snapshots in use. Shorter candidates do not shrink retained full vectors or the model. The candidate policy is runtime configuration to reapply on reopen; changing it rebuilds derived state without changing the stored embedding schema. It applies to vector graph search, not ordinary hybrid document search.

## Other retrieval paths

- **Similarity meaning.** Sparse `query` results report Jaccard similarity for every route. Hopfield attention (`query_hopfield`) has separate weights and its own contract. Index training can affect approximate candidate membership but not the meaning of `similarity`.
- **Trained exact tree.** After `train_document_index`, broad metadata-filtered hybrid queries reuse the bounding-box tree and keep at most `candidateLimit` lexical owners before semantic fusion; the tree checks document filters before scoring a row, and small filtered sets scan directly. Both keep the filtered corpus's BM25 statistics and canonical scores: the execution plan changes, not the search or filtering contract.
- **Filtered postings.** Filtered lexical and trained hybrid queries use filtered postings when that is less work than scanning every eligible chunk for every term; dense traversal reuses the captured eligibility. Posting acceleration is capped at 524,288 store slots and the dense eligibility set at that many matching documents; beyond them the scan or predicate path applies. BM25 normalization belongs to the captured filter and generation, including legacy zero-frequency terms.
- **Changed-document delta.** The trained tree stays usable after mutations through a bounded delta: changed base documents are excluded before top-k selection, and current changed chunks join canonical scoring and fusion.

  | Delta bound | Limit |
  |---|---|
  | document IDs | 128 |
  | live chunks | 1,024 |
  | ID bytes | 64 KiB |

  Exceeding a bound drops the acceleration (queries keep their exact fallback; maintenance can rebuild). Replacing the same ID updates its entry. Explicit training publishes only at its captured generation and resets the delta; `trained` still means the base is current.
- **Admission.** Dense training shares the vector-build admission gate and returns a retryable maintenance error when occupied. Queries add no background workers or queues. Server admission keeps its bounded queue and busy response; cancelling a waiting request releases its queue entry, while a running blocking query owns its permit until completion. These bound additional search state, not process RSS.
- **Phrase queries.** They use persisted positions where available; for a candidate chunk without positions the engine reconstructs them from retained text with that chunk's analyzer, and an unrelated chunk without positions does not disable phrase search. A candidate with neither positions nor text returns an error and is never silently excluded. Persisting positions avoids the reconstruction work.
- **Whole-document lexical ingest.** It still requires positions but can also take one dense embedding in the configured space, supporting phrase matching across chunk boundaries and vector/hybrid retrieval of the same article. It creates no sparse text hypervector in lexical ingest mode.
- **Standalone `FilteredIndex`.** Dimensions 1 through 66,051 (so every squared u8 Euclidean distance fits its `u32` result); at most 1,048,576 labels in its dense label tables; training and CSR shapes are validated and result capacity is bounded by the live candidate count. Use a compact label mapping for sparse external label identifiers.

## Reasoning budgets

Use `multi_hop_with_limits` and `synthesize_concepts_with_limits` with
`writerslogic_warm::core::query_limits::QueryLimits` to handle resource limits explicitly.
Their defaults are 10,000,000 work units, 16,384 frontier entries and 64 MiB of accounted
bytes. Work includes scanned triples, candidate visits, sorting and comparisons. Byte
accounting conservatively covers retained inputs, intermediate frontiers and working
buffers; it is not a process RSS measurement.

Budget exhaustion returns an error identifying the resource and limit. Results are
complete or absent because of the error; there are no silently truncated answers.
Multi-hop retrieval preserves distinct paths even when they reach the same endpoint.
Concept synthesis generates one candidate frontier per seed instead of retaining every
pair of neighbors. Common dimensions can still require quadratic work, so the work
limit remains necessary.

The legacy Rust `multi_hop` and `synthesize_concepts` signatures retain their `Vec` return
types and apply the default limits. They panic on budget exhaustion. Call the checked
companions in applications that must report or recover from an exhausted budget.


## Durable meaning governance

`WarmCore::govern_memory` returns `Result<GovernanceReport>` and uses the default
`QueryLimits`; `govern_memory_with_limits` accepts explicit limits. It captures a coherent
revision and bounded live snapshots, plans on isolated memories outside the mutation gate,
and publishes one journal transaction only if the revision is still current.
`GovernanceConflict` means another writer invalidated the plan; no governance change was
committed, and callers may retry. Work, frontier, byte, operation-count and serialized-size
exhaustion also fail before publication. The atomic transaction is capped at 4,096 operations
and 32 MiB; byte accounting is a conservative allocation budget, not an RSS measurement.

Live triple owners survive consolidation even when their vectors are identical. Scoped
atom/composite deletions preserve unrelated raw vectors with the same ID. Refinement
recomposes affected owned composites and their matching raw-vector mirrors; ambiguous or
missing ownership fails explicitly. Reopen and compaction retain these changes. The
standalone `MemoryGovernor` primitive operates only on the supplied in-memory stores;
applications persisting an `WarmCore` use its durable governance methods.

New stores use schema 5. Meaning-enabled stores with schemas 2–4 keep their writer format
and must first be explicitly copied with `warm-format upgrade <source> <destination>` before
durable governance. The source remains unchanged, and current arenas/checkpoints are copied
without re-encoding their existing journal frames.
