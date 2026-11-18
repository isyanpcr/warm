# Privacy limits

WARM processes everything locally: the core engine makes no network calls and the model adapters only read local directories. The `offline` job in [ci.yml](https://github.com/writerslogic/warm/blob/main/.github/workflows/ci.yml) checks this on every change: the default dependency tree has no HTTP, TLS or socket client crate, and the default-feature test suite passes in a network namespace with no external interface. That removes the cloud as a threat; it does not make the stored representation private. [Privacy and security boundaries](../PRIVACY.md) is the complete statement and wins on any difference.

| Claim | Reality | Detail |
|---|---|---|
| Hypervector sketches and term counts protect text | They are not encryption: the encoder is deterministic and public, so anyone with a store can test candidate texts. The number of bit patterns is not a defence. | [PRIVACY.md](../PRIVACY.md#local-processing-and-retained-data) |
| `storeText: false` is private | It drops passages but keeps term counts, metadata, source URIs, IDs and supplied embeddings. | same |
| Embeddings are safe to share | A dense embedding is a function of the text and inversion attacks exist; treat embeddings as sensitive as the text. | same |
| Queries are protected | Queries and model inference run in plaintext in process memory. | same |
| Encryption covers everything | AES-256-GCM (Argon2id key) covers arena payloads, persisted index caches and the passage text segment (`documents.text`). Not covered: schema metadata, file names, sizes, topology, salts, access patterns, process memory, swap and crash dumps. A wrong passphrase fails authenticated decryption and the store does not open ([quickstart](../quickstart/index.md)). | [PRIVACY.md](../PRIVACY.md#encryption-and-signing), [file-format/ENCRYPTION.md](../file-format/ENCRYPTION.md) |
| Deleting erases | Removed records can persist in obsolete segments, snapshots and backups; compaction is not secure erasure. CRC32 detects accidents only. | [ERASURE.md](../memory-api/ERASURE.md) |
| Vector masking hides vectors from a remote store | `VectorMask` (Python SDK `zero_trust_key`) is obfuscation: pairwise similarity is preserved, so the store learns the similarity graph, and known plaintext/masked pairs reveal the permutation progressively. | [PRIVACY.md](../PRIVACY.md#client-side-vector-masking) |
| Differential privacy covers the engine | It applies only to the configured **bundle** operation, is not audited as a finite-precision mechanism, and WARM keeps no persistent budget accountant. | [PRIVACY.md](../PRIVACY.md#differentially-private-bundling) |

Not implemented: search over encrypted data, query privacy against the server, PoSME receipts, RATS attestation verification and `did:web` resolution for access credentials. The experimental [private search](../PRIVATE-SEARCH.md) scoring hides the query vector from the scoring server only, under the limits stated there.
