# Organizational knowledge across applications

WARM can index normalized documents from multiple source systems without owning
their collection or normalization. The runnable adapter below targets the flat
curated JSON documents currently produced by
[the ToIP EGWG prototype](https://github.com/trustoverip/egwg-reporting-tf-prototype-mcp).
It is an integration example, not an agreed ToIP contract or an installed MCP
backend. The proposed nested model in issue #8 is not supported by this example.

## Import and retrieve

Run from the WARM checkout. Use a dedicated store directory; the example uses the
default unencrypted configuration. It performs local lexical retrieval without
model downloads, API keys, or paid services.

```sh
cargo run --locked --example organizational_knowledge -- import ./toip-example toip /absolute/path/to/curated/document.json
cargo run --locked --example organizational_knowledge -- search ./toip-example toip "governance reporting"
```

Import one file per invocation. Required fields are `id`, `source_system`,
`identifier`, `content`, and a string array `organizational_unit`. Other fields
are preserved in metadata. Input files are bounded to 8 MiB; engine limits still
apply to chunk count, document text, and metadata. This example is not a bulk
synchronizer: a multi-file import is not one transaction.
The adapter rejects upstream `hms_namespace` fields because that name is reserved
for query scoping. Identity components must be nonempty and contain no control
characters. Schema and chunking validation finish before the import opens a store.

| Upstream field | WARM representation |
|---|---|
| Namespace + source system + stable `id` | Collision-safe JSON tuple as document ID |
| `identifier` | Document version, preserved verbatim |
| `content` | Original text, chunked at 500 words with 50-word overlap |
| `source_url` | Source URI, when present |
| All fields except `content` | Metadata, including original IDs and provenance fields |

The adapter does not verify SAIDs or treat their presence as authentication.
Stable source identity is required separately from the content identifier, so a
new version replaces the same document instead of accumulating stale versions.
Different applications can reuse an ID without overwriting one another. Namespace
filtering scopes this example's queries; it is not an authorization boundary.

Retrieved passages include UTF-8 byte offsets into the exact imported `content`,
source URI, version, and metadata. These offsets refer to curated text, not the
original recording or pre-normalization artifact. Speaker attribution and
recording timestamps require upstream span mappings; the adapter does not infer
them. It does not treat copies or summaries as independent corroboration.

## Replace and forget

Reimport a document with the same namespace, source system, and stable ID to
replace it. The supplied version is retained; upstream is responsible for
delivering versions in the right order. This is current-state document indexing,
not the memory API's supersession history.

```sh
cargo run --locked --example organizational_knowledge -- forget ./toip-example toip Zoom meeting-1
cargo run --locked --example organizational_knowledge -- forget ./toip-example toip Zoom meeting-1 --apply
```

The first command previews the selected ID without opening the store. `--apply`
removes its chunks from WARM retrieval; repeating it is safe. Remove or suppress
the upstream document as well: importing it again intentionally restores it.
This operation does not erase upstream artifacts, backups, model inferences, or
filesystem snapshots, and is not a physical-erasure guarantee. See the memory
API's [forgetting and purge contract](../memory-api/README.md#forgetting) for the
separate fact-store operations and their limits. Use one writer per store.

## JavaScript integration

The [JavaScript adapter](../../integrations/organizational-knowledge/README.md)
wraps the released `DocumentMemory` API. With the Node native bindings built as
described in [Contributing](../../CONTRIBUTING.md#set-up), run from this checkout:

```sh
node integrations/organizational-knowledge/example/cli.cjs import ./toip-example toip integrations/organizational-knowledge/example/fixtures
node integrations/organizational-knowledge/example/cli.cjs search ./toip-example toip "quartzmarker"
node integrations/organizational-knowledge/example/cli.cjs forget ./toip-example toip Zoom zoom-example-project-chat-GMT20260101-100000
node integrations/organizational-knowledge/example/cli.cjs forget-all ./toip-example toip Zoom
node integrations/organizational-knowledge/example/cli.cjs prune ./toip-example toip Zoom /absolute/path/to/data/curated
```

`forget-all` removes one source system's documents, or the whole namespace with
`--all`; `prune` keeps the source system's documents found in the given files and
removes the rest. Both preview unless `--apply` is given, and a run handles at
most `--limit` documents (10,000 by default). They list the store through
`listDocuments`, which a binding built before it was added lacks; rebuild with
`npm run build`. A prune is only as complete as the files it is given. The Rust
example forgets one document at a time.

The CLI is lexical by default; programmatic use can pass a local embedder and reranker through `DocumentMemory` (the embedder must match the store's embedding space). The adapter is imported with `require('./integrations/organizational-knowledge/index.cjs')`; it is not part of the released npm package's exports. Metadata filters use exact top-level equality, so filtering on `organizational_unit` must match the whole array. This differs from the prototype's working-group substring filter and needs an explicit translation in a prototype-side adapter.

## JavaScript adapter reference

Mapping is the table above, except the document ID is `JSON.stringify([namespace, source_system, id])` (at most 1024 bytes) and the namespace is also stored as reserved metadata `hms_namespace`.

The stable identity uses the curated `id`, not `source_identifier`: one Zoom recording
yields a Transcript, Chat, ClosedCaptioning, and AI Summary that share `source_identifier`.
The identity does not depend on the SAID, so a revised document replaces the earlier one
instead of accumulating. Hit offsets are UTF-8 byte offsets into the exact curated `content`.

### Behavior

- **Validation before writes.** Every document is checked, and duplicate identities in one
  import are rejected (naming both sources), before the first write. Rejected: missing or
  blank `id`, `source_system`, `identifier`; non-string `content`; whitespace-only content;
  `organizational_unit` that is not an array of strings; non-string optional fields;
  control characters in identity parts; lone surrogates anywhere (the engine would silently
  rewrite them); a `__proto__` key anywhere (the binding returns it as a prototype, not data);
  `source_url` that is not an absolute http(s) URL without credentials, whitespace, or control
  characters; `hms_namespace` in the input; metadata over 64 KiB; the nested model; and the
  engine's chunking limits (4096 chunks, 64 KiB per chunk, and with an `embedder` 1,048,576
  embedding values per document). The CLI validates everything, including the engine's chunking
  limits on a throwaway store in the system temp directory, before it opens STORE, so rejected
  input does not create it. A library caller's `importDocuments` checks the same limits on its
  own open store before the first write.
- **Bounded input.** At most 10,000 documents per import; files are at most 16 MiB each and
  512 MiB in total. Split larger syncs; identities are independent, so this is safe.
- **Overlapping calls.** Writes (`importDocuments`, `forget`) on one instance run one after
  another in call order, so the last call for an identity wins.
- **Replacement.** Importing the same namespace, `source_system`, and `id` replaces the
  document in one atomic commit. Order is the caller's: the last import wins.
- **Not one transaction.** Each document commits atomically, but an import is not atomic
  across documents. A write failure throws `partial_failure` listing `committed` IDs;
  re-running the import is idempotent.
- **Forget.** Explicit `{ sourceSystem, id }` targets inside the namespace; no wildcard.
  Without `apply: true` it only reports IDs. Repeating is safe (`absent` lists missing ones).
- **Forget by scope.** `forgetScope({ sourceSystem | all: true, keep? }, { apply, limit })` removes
  a source system's documents, or the namespace's, except an optional nonempty `keep` list of
  `{ sourceSystem, id }` (a prune: pass the identities the upstream still holds). It lists the store
  through `listDocuments`, matches only documents whose identity and `hms_namespace` both belong to
  this namespace, previews unless `apply: true`, and handles at most `limit` documents per call;
  `truncated: true` means more match, so apply and repeat (a preview shows the same first `limit`
  each time). Options other than `apply` and `limit` are rejected: `keep` belongs in the scope. It throws `unsupported_binding` when the loaded
  binding has no `listDocuments`. A prune is only as complete as the `keep` list: documents missing
  from it are removed, so a partial export of the upstream removes the rest.
- **Reimport restores.** Importing a forgotten document again makes it searchable again.
  Forgetting is not durable against a later sync from an upstream that still holds it.

### Limitations

- Namespace filtering is a query filter, not authorization. Anyone who can open the store or
  call the engine API can read every namespace. Use separate stores or encryption for isolation.
- Forget removes the document from WARM retrieval. It does not claim physical erasure of
  journals, page cache, backups, snapshots, or model inferences, and it does not remove
  anything upstream. Upstream deletion is not detected or propagated.
- Namespace-wide forget and prune need the binding's `listDocuments`, added alongside this adapter
  in `src/bindings/node`; a binding built before that has none, and `forgetScope` then fails with
  `unsupported_binding`. Rebuild with `npm run build`. Upstream deletions are still not detected:
  pruning needs a complete list of what the upstream holds.
- `identifier` is stored, not verified: SAIDs are not checked and are not authentication.
- Speaker identities and recording timestamps are not inferred; offsets refer to curated text.
- A `filter` is an exact match on a top-level metadata value: `organizational_unit` must
  equal the whole array.
- One writer per store directory.
- JSON numbers are IEEE doubles: integers above 2^53 in extra metadata fields are not
  preserved exactly. The curated schema has no numeric fields.
- No retrieval-quality, speed, or benchmark claim is made.

### Interoperability with the Rust example

The Rust example reads and deletes what this adapter wrote, and the reverse, one writer at a
time. Differences checked against the Rust example binary: this adapter rejects non-string
optional fields (`title: 12`, `title: null`) and a `javascript:` `source_url`, which the Rust
example imports; it reads files up to 16 MiB where the Rust example reads 8 MiB; and it stores
integers above 2^53 in extra metadata fields as rounded doubles where the Rust example keeps
them exactly. Both reject control characters in `id`, a reserved `hms_namespace` key, and
lone surrogates.

```sh
node integrations/organizational-knowledge/example/cli.cjs import ./toip-js-store toip integrations/organizational-knowledge/example/fixtures
cargo run --locked --example organizational_knowledge -- search ./toip-js-store toip quartzmarker
cargo run --locked --example organizational_knowledge -- forget ./toip-js-store toip Zoom zoom-example-project-chat-GMT20260101-100000 --apply
node integrations/organizational-knowledge/example/cli.cjs search ./toip-js-store toip "reporting profile"
```

This sequence was run against a debug build and the synthetic fixtures. The automated
tests do not call cargo; `tests/organizational_knowledge_cli.test.cjs` covers the cross-tool path.

## Optional backend boundary

The current examples consume flat curated documents and use WARM chunking. They
are not wired into the prototype's MCP server. An optional backend should
preserve the workstream boundaries in
[issue #8](https://github.com/trustoverip/egwg-reporting-tf-prototype-mcp/issues/8):

| Prototype contract | Integration responsibility |
|---|---|
| Raw Artifact and Normalized Document | Keep collection, normalization, SAID rules, and authoritative provenance upstream |
| Embedded Chunk | Preserve the agreed chunk identity, text, metadata, and parent document reference when adding an indexing adapter |
| Vector Index Entry | Treat WARM as a rebuildable derived index; retain the existing backend as an option |
| Search Result | Join authoritative metadata at retrieval and preserve the existing MCP tools and response contract |

WARM's internal document ID is the namespaced stable source identity; `version`
and `metadata.identifier` retain the upstream content identifier. Internal WARM
chunk IDs are not the proposed SAID-based chunk IDs. Mapping those identities,
implementing the nested schema, matching working-group filter semantics, and
wiring the retrieval-time provenance join remain prototype integration work.
These examples neither verify SAIDs nor implement the proposed Embedded Chunk
or Search Result schemas.

The prototype already replaces changed documents transactionally, supports
`--prune`, and filters working groups before vector ranking. Its lexical scorer
reranks vector-shortlisted candidates. WARM provides an alternative lexical or
hybrid document search path; whether that improves results needs a comparison.
See the prototype's
[indexer](https://github.com/trustoverip/egwg-reporting-tf-prototype-mcp/blob/main/toip-mcp-server/src/ingest.ts)
and [retriever](https://github.com/trustoverip/egwg-reporting-tf-prototype-mcp/blob/main/toip-mcp-server/src/search.ts).

For retention or source retraction, coordinate upstream suppression with removal
from every derived index and any separately created facts or summaries. Document
deletion does not cascade into independent memory facts. The memory API can
retain supersession history and explicitly forget or purge facts; adopting it is
a separate choice from indexing normalized documents.

## Reproducible local checks

```sh
cargo test --locked --example organizational_knowledge
node --test integrations/organizational-knowledge/test/*.test.cjs
node --test tests/organizational_knowledge_cli.test.cjs
./node_modules/.bin/tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --types node tests/organizational_knowledge_types.test.cts
```

The tests exercise overlapping IDs from different applications and namespaces,
original Unicode source spans, provenance metadata, replacement, deletion,
idempotence, restart persistence, malformed inputs, and input-size boundaries.
The CLI check builds the Rust example offline and exercises both languages
against the same persistent store, including rejection before store creation,
deletion preview, replacement, reimport after deletion, and namespace isolation.
These checks use synthetic text and local storage. They establish adapter correctness,
not retrieval quality, benchmark standing, or a speed advantage.

Local verification on 2026-10-28 used macOS arm64, Rust 1.96, and Node 26.8.1:

| Check | Result |
|---|---|
| Rust example tests, default and all features | 4 passed in each configuration |
| Example Clippy, default and all features | Passed with `-D warnings` |
| Rust 1.89, no default features | Example check passed |
| JavaScript adapter tests | 41 tests, 40 passed, 1 skipped (re-run 2026-11-18, Node 26.8.1) |
| Rust and JavaScript CLI interoperability | 2 passed |
| Strict TypeScript file-reader/import composition | Passed |
| Strict MkDocs build | Passed; Rust API reference generation excluded |

These are focused integration checks; the full repository test matrix was not
rerun for this example. No paid services or model downloads were used.

Before proposing production adoption, compare identical corpus snapshots,
queries, chunk boundaries, embeddings, filters, and relevance judgments against the prototype's
existing backend. Measure source coverage and ranking quality separately from
latency. Associative/holographic retrieval needs its own evaluation; this adapter
does not establish a benefit for splatter or superposition.
