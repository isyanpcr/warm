# Cargo features

`default = []`: the default build is a local, offline library with no network code, no bindings
and no research modules. Every capability is off until you turn it on. Dependencies per feature:
[`Cargo.toml`](https://github.com/writerslogic/warm/blob/main/Cargo.toml). "Stable" features are
covered by the [stability policy](../STABILITY.md); "experimental" ones can change in any release.

## Common builds

| You want | Build |
|---|---|
| Encrypted stores and signed audit logs | `cargo add warm-rust --features security` |
| A self-hosted HTTP service | `cargo install --locked --features server,security --bin warm-server warm-rust` |
| An MCP server | `cargo build --release --features mcp,security --bin warm-mcp` (add `local-models` for semantic recall) |
| Local embeddings without an API | `local-embed` ([embeddings](../embeddings/README.md)) |

## All features

| Feature | What it turns on | Status | Network code | Docs |
|---|---|---|---|---|
| `security` | AES-256-GCM encrypted stores (the default for new stores when compiled in; plaintext is an explicit opt-out), Argon2 passphrase keys, Ed25519-signed audit logs | stable | no | [Security](../SECURITY.md), [Encryption format](../file-format/ENCRYPTION.md) |
| `keychain` | macOS login-keychain provider for the sealed container master key; implies `security` | experimental | no | `core::sealed` |
| `provenance` | COSE_Sign1 signed statements and DID identities; implies `security` | experimental | no | [Privacy](../PRIVACY.md) |
| `provenance-scitt` | Experimental statement submission returning unverified receipt bytes; no VDS inclusion/trust verification; implies `provenance` | experimental | yes (`ureq`), only when you call it | [FAQ](faq.md) |
| `server` | `warm-server`, a self-hosted HTTP service for the Python SDK and multi-process access | stable | listens only on the address you give it | [Server](../SERVER.md) |
| `mcp` | `warm-mcp`, a Model Context Protocol server over stdio or HTTP | stable | listens only when run over HTTP | [MCP](../integrations/mcp/README.md) |
| `local-embed` | Pure-Rust text embeddings from a pinned, sha256-checked model pack on disk | stable | no | [Embeddings](../embeddings/README.md) |
| `local-embed-download` | First-use download of the pinned model pack into the cache; implies `local-embed` | stable | yes, the one download | [Embeddings](../embeddings/README.md) |
| `local-models` | On-device embedding, re-ranking, fact extraction and query rewriting (candle, Qwen3); weights load from local directories only | experimental | no | [Embeddings](../embeddings/README.md) |
| `conversation-memory` | Immutable original conversation turns, role-aware recall and bounded source premises | experimental | no | [Conversation evidence](../memory-api/README.md) |
| `experience` | Accepted and ignored: the [experience core](../concepts/experience-core.md) is always built. `remember` routes an observation by shape; `recall`, `explain` and `forget` cover it | stable | no | [Experience core](../concepts/experience-core.md), [Format](../file-format/EXPERIENCE.md), [Memory API](../memory-api/README.md) |
| `cli` | `clap` argument parsing for the command-line binaries and examples (`warm-admin`, `warm-format`, `public-bench`, the benchmark drivers); implied by `server` and `mcp` | stable | no | [Evaluation](../evaluation.md) |
| `failpoints` | Fault injection at the durability points, inert unless armed; used by the crash and disk-fault tests | test-only | no | [Crash consistency](../file-format/CRASH-CONSISTENCY.md) |
| `mimalloc` | `allocator::Tuned`: mimalloc with arenas committed on demand and an immediate purge, the global allocator of `warm-server`, `warm-mcp`, `warm-admin`, `public-bench` and the Python wheel (their release builds enable it; the library never sets one). Ingest is about 17% faster at 250k documents than with the system allocator at the same peak resident size | stable | no | [Server](../SERVER.md) |
| `node-api` | The Node.js bindings published to npm | stable | no | [Node API](../api/node/index.md) |
| `python` | The `warm-python` Python wheel (vector search and phase vectors) | experimental | no | [Python API](../api/python/vsa.md) |
| `private-search` | Query-private similarity scoring over an index held by someone else (LWE, SimplePIR-style): the index holder ranks an encrypted query and learns nothing about it | experimental, research | no (you transport the messages) | [Private search](../PRIVATE-SEARCH.md) |
| `experimental` | VSA research modules (block codes, Bloom memories, algebraic codebooks, operand retriever, connection and phase graphs) and the experiment binaries | experimental, research | no | [Research](../RESEARCH.md) |
| `experimental-batch-pool`, `experimental-neighbor-admission`, `experimental-query-x4`, `experimental-build-search` | Individual build and query variants of the vector index; each implies `experimental` | experimental, research | no | [Research](../RESEARCH.md) |
| `base64`, `ciborium` | Accepted for builds that name them; the dependencies are always present, so they turn nothing on | stable | no | |

## Which features need a server

None. Search, storage, encryption, deletion and provenance run in your process; `server` and `mcp`
run that process as a service you host. `private-search` is for an index someone else holds and does
nothing for a local store.
