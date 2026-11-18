# WARM vs. Alternatives

**Hybrid search, graph indexing, and vector-symbolic memory.**

WARM combines several retrieval and memory paths in one local Rust engine, with different roles; the vector-symbolic layer does not rank ordinary document-search results.

| Need | WARM path | Useful comparison |
|------|----------|-------------------|
| Search exact words and phrases | Stemmed BM25 with Boolean and phrase queries | Full-text search engines |
| Search by meaning | Exact cosine over embeddings you supply, fused with lexical results for hybrid search | Embedding-based retrieval systems |
| Search a large vector collection | Graph index with quantized traversal and exact reranking | Approximate nearest-neighbor libraries |
| Store and query structured facts | Vector-symbolic bind, bundle and associative recall, plus a triple store | Symbolic and graph memory systems |

- Semantic matching in document search needs embeddings you supply. Its index can contain source text; enable the encrypted store when confidentiality matters ([privacy limits](privacy-limits.md)).
- The vector-symbolic layer supports composition and associative recall for facts; it does not replace a strong language embedding model for nuanced semantic search over prose. The older sparse-vector path is experimental and trails established ANN libraries: use the graph index for vector search.
- Measured wins and losses: [public benchmarks](../PUBLIC-BENCHMARKS.md). Boundary between document retrieval and holographic memory: [holographic](holographic.md), [architecture map](../ARCHITECTURE.md).
