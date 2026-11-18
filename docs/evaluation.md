# Retrieval and workload evaluation

## LongMemEval memory quality

The objective is the strongest defensible end-to-end memory quality: retrieving necessary evidence, reasoning over time and entity identity, resolving facts that change, and abstaining when the history cannot answer. Retrieval recall, quotation validity, latency and answer accuracy are separate measurements. A perfect score on repeatedly tuned development questions does not establish general memory capability.

Rules for a promoted memory pipeline:

- It runs from source history and a new query through ordinary indexing and retrieval. Benchmark identifiers, question-type labels, expected answers and labeled support cannot direct retrieval or generation; saved development answers or citations cannot substitute for query-time retrieval.
- An online multi-stage reader charges and reports every upstream stage's context and cost.
- Freeze the complete policy before the final evaluation, keep every question and failure in the denominator, and preserve failed experiments.
- Tune only on the frozen 100 dev questions in [the shared S/M split](../benchmarks/public/longmemeval_split.json). The 400 held-out questions stay sealed until pipeline, models, prompts, budgets, abstention rule and scoring are frozen for the single final M run, which cannot select another variant.
- Historical protocols below keep their original 100/100 dev target fields; those fields are not a generalization claim or the acceptance rule for a promoted engine.

### LongMemEval_S 500-question held-out run (final, spent)

The single sealed held-out run was made under [the frozen config](../benchmarks/public/longmemeval_500_frozen_config.json) (pinned revision `02468f57`; engine code identical to main `12611a9f`, the branch adds benchmark files only). Result file: [`longmemeval_500_official_v1.json`](../benchmarks/results/longmemeval_500_official_v1.json).

| Stage | Setting |
|---|---|
| Retrieval | Modal; pinned Qwen3 models (Qwen3-4B-Instruct-2507 facts and query rewrites on an L4; Qwen3-Embedding-0.6B and Qwen3-Reranker-0.6B on a T4); WARM document API BM25 + exact-cosine scores (`public-bench lme-scores`) fused by `longmemeval_pipeline.py`; rankings exported label-blind (top 50 turns per question) |
| Reader | `gpt-4o-2024-08-06`, official prompt, k=10 retrieved rounds, one sample at temperature 0 |
| Calls | All reader and judge calls through OpenRouter with the provider pinned to OpenAI (2,500 calls, all served by OpenAI with the pinned snapshots) |
| Headline judge | Unchanged official `evaluate_qa.py` (commit `9e0b455f`) |
| Spend | $4.02 Modal GPU (four launches under one tag, cached stages reused) and $9.13 OpenRouter, for the reader and both judges, each under a $30 cap |

| Judge (official `evaluate_qa.py`) | n=500 | dev100 | heldout400 |
|---|---|---|---|
| gpt-4o-mini-2024-07-18 | **84.4%** (422/500) | 88/100 | 334/400 (83.5%) |
| gpt-4o-2024-08-06 | 85.0% (425/500) | 89/100 | 336/400 (84.0%) |

- Per type (gpt-4o-mini judge): single-session-user 68/70, single-session-assistant 52/56, knowledge-update 68/78, temporal-reasoning 113/133, single-session-preference 24/30, multi-session 97/133; abstention 27/30.
- Retrieval alone (official `eval_utils.py`, 419 scorable questions): session recall@10 0.988, turn recall@10 0.919.
- dev100 was used for tuning, so n=500 mixes tuned and untouched questions; heldout400 is the generalization figure.
- The 400 held-out questions are spent for this pipeline; a later variant cannot be evaluated on them.

### Development experiments (exploratory, repeatedly used dev set)

Failures stay in the 100-question denominator in every row. None is a held-out or production-engine result, and larger-context rows are not equal-budget comparisons.

| Experiment | Setup | Result |
|---|---|---|
| [v3 operand arm](../benchmarks/results/longmemeval_dev_answers_v3_summary.json) | Matched reader; larger evidence budgets than first-five or knapsack | 88/100 (Wilson 95% 80.19-93.00%) vs 83/100 first-five, 82/100 knapsack |
| [User-first](../benchmarks/results/longmemeval_user_first_v1/summary.json) ([protocol](../benchmarks/results/longmemeval_user_first_v1/protocol.json)) | Complete user turns first, then complete assistant continuations; existing dev candidate pool; 7,680-token local limit inside the 8,192-token reader cap; 24,391 verbatim user turns from saved dev archives (assistant continuations limited to existing v1/v3 snapshots); prepared packets cover all labeled user evidence for 82/84 scored questions (v3 reader inputs: 77/84) | **80/100**, a regression; all 100 readers and judges completed. Multi-session 19/27 to 20/27, assistant 10/11 to 5/11, preferences 6/6 to 3/6. More user turns alone is insufficient: the cap also removes assistant-origin facts. Kept as a failed experiment. |
| [Session closure](../benchmarks/public/longmemeval_session_closure.py) ([offline reproduction](../benchmarks/results/longmemeval_session_closure_v1.json)) | Adds the first two user turns from sessions touched by the top 20 retrieved turns before filling from the pool | Retained user support 82/84 to 83/84 at the same cap, no coverage regressions. Not scored end to end. |
| [Full history](../benchmarks/results/longmemeval_full_history_v1/summary.json) ([validation](../benchmarks/results/longmemeval_full_history_v1/validation.json), 199 paid calls verified) | All 24,391 dev user turns plus 781 saved assistant turns; 131,072-token input budget, 512-token framing reserve; median prepared input 44,014.5 tokens, max 51,275; extra generic entity, temporal and personalization instructions; all 84 scored user-evidence cases complete | **88/100**: five gains, five regressions vs v3. Knowledge updates 16/16, multi-session still 19/27, preferences 5/6. One otherwise supported abstention fails the strict JSON contract (nonempty claims). [Paired failure analysis](../benchmarks/results/longmemeval_role_failure_diagnostic_v1.json) separates missing assistant facts, relation and event identity errors, temporal scope errors, personalization drift and schema failure. |
| [Role-aware retrieval](../benchmarks/results/longmemeval_role_retrieval_v1/summary.json) ([validation](../benchmarks/results/longmemeval_role_retrieval_v1/validation.json)) | Searches complete original assistant replies alongside the cached user ranking, equal-weight RRF, first five user results preserved, at most 64 complete exchanges, same larger budget. Source loader verifies the pinned file hash and all 500 question identifiers but decodes only the 100 dev records (24,391 user turns, 24,784 assistant turns, incl. 18 assistant-only sessions omitted from the earlier archive); held-out bodies are streamed for framing and hashing only. Packets: 6,388 user and 6,400 assistant turns; labeled user support complete for 82/84; median input 44,400.5 tokens, max 50,698 | **93/100**, the best checked exploratory dev result (no held-out or production-engine claim); all 100 reader and judge calls succeeded. Knowledge updates 16/16, temporal 26/26, assistant 11/11, user 14/14, preference 6/6. All seven failures are multi-session (20/27): ownership counts, project identity and missing premises, order identity, wedding identity, habitual device use, payment versus event dates, one judge-rejected abstention. Increased assistant availability is useful but does not establish complete answer quality. |
| [History budget](../benchmarks/results/longmemeval_history_budget_dev_v1.json) (offline, no model calls) | Source retention under the prompt | Complete original conversations need 150,437-168,359 input tokens (median 158,135); none fit the 130,560-token local limit. Preserving every user turn plus a ranked prefix of complete assistant continuations retains 18,175 assistant turns and 84/84 labeled user-support cases within it. |
| [Complete original history](../benchmarks/results/longmemeval_complete_history_v1/summary.json) ([validation](../benchmarks/results/longmemeval_complete_history_v1/validation.json)) | All 49,175 original dev turns; 196,608-token input cap, 512-token framing reserve; prepared median 158,618, max 168,842; 84/84 user support complete; pinned GPT-5.4 snapshot, high reader reasoning, 8,192-token output limit; judge medium reasoning, 2,048-token output limit ([model docs](https://developers.openai.com/api/docs/models/gpt-5.4)); generic source-role, entity, relation, temporal and personalization instructions. Source, budget and reasoning change together, so no result is attributable to one change | **91/100** with one reader transport failure in the denominator (99 successful readers and judges, no retries or resampling). Own-call cost $42.118065 including the reservation for the failed response, inside its $50 cap and the unchanged $120 dev-reader/judge and $250 global caps. Did not beat the 93/100 retrieval run. |
| [Independent-reader prototype](../benchmarks/public/longmemeval_verifier.py) | Four-prior source packets citing four saved development readers, some given broad original history; probe: [API capability](../benchmarks/results/longmemeval_verifier_probe_v1/probe.json), no benchmark question | **Unpromoted and unscored.** Omitting answer text does not remove the upstream access or make its 32,768-token context the total query budget. Its source-preservation, premise-closure, token-accounting and transport mechanisms are reusable; its development-answer dependencies must become ordinary query-time retrieval before a general-memory claim. |

The [offline quality diagnostic](../benchmarks/results/longmemeval_dev_quality_v3.json) recomputes the v3 outcomes from saved reader and judge responses without opening the corpus or making model calls:

| Question type | Correct / total |
|---|---|
| Multi-session | 19/27 |
| Temporal reasoning | 24/26 |
| Knowledge update | 15/16 |
| Single-session assistant | 10/11 |
| Single-session user | 14/14 |
| Single-session preference | 6/6 |

- The twelve v3 failures: six judge-rejected abstentions, five incorrect generated answers, one reader failure; eight are multi-session.
- All six labeled unanswerable questions receive abstentions; seven answerable-labeled questions also do, including one the judge accepts. Label-based abstention and judge acceptance are reported separately. Exact quotation validity does not establish that a claim follows from its citation.
- Next experiment: distinguish missing evidence, evidence removed by the reader token cap, and incorrect use of retained evidence in the multi-session failures. Existing completeness labels apply before the cap and only to scored user turns, so they cannot show the reader had sufficient support. Temporal and fact-update changes need source-backed cases that distinguish observation time, event time, validity, entity identity, and plans from completed events; abstention changes need answerable and unanswerable cases.
- These experiments change the benchmark harness, not the production engine's fact-update implementation; their measured results do not establish production retrieval quality.

### Conversation memory production validation

The opt-in [conversation memory API](memory-api/README.md#original-conversation-evidence-rust-opt-in) stores immutable original user and assistant turns and retrieves through `Memory::recall`, with no saved-answer, question-ID, question-category or benchmark-rank dependency.

| Record | Result |
|---|---|
| [Historical production validation](../benchmarks/results/conversation_quality_validation_2026-10-21.json) | 788 passing tests |
| [Completed production proof](../benchmarks/results/conversation_production_validation_v1.json) | **823**: 527 native tests, 3 bridge unit tests, 293 current Python tests. Native checks cover original-role evidence, confirmation premises, whole-source budgets, immutable writes and restart, concurrency, long-turn hydration. |
| [Metal smoke test](../benchmarks/results/conversation_bridge_model_smoke_v1/validation.json) | All three pinned local models passed ([raw JSONL receipts](../benchmarks/results/conversation_bridge_model_smoke_v1/responses.jsonl)) |
| Frozen source | [Isolated source snapshot](../benchmarks/results/conversation_production_source_snapshot_v1.json); [release build receipt](../benchmarks/results/conversation_bridge_release_build_receipt_v1.json) |

Frozen pipeline: complete original conversations in the ordinary memory index; 64 distinct sources per role from a pool of 256 returned chunks per role; premises admitted under 128 sources and 65,536 serialized bytes; original query weight 1, rewrite weight 1, all subqueries combined weight 1; no earlier answers or cached rankings. Reader GPT-6.1 Sol, high reasoning, 4,096-token output limit, exact 32,256-token input gate plus a 512-token reserve; judge is the official LongMemEval prompt on pinned GPT-5.4-2026-03-05; $14 cap, no held-out run.

**[Production dev evaluation stopped before QA](../benchmarks/results/longmemeval_production_closeout_v1.json); no production QA score is claimed.** The tests and smoke checks do not establish QA accuracy or generalization. The earlier harness's 93/100 remains separate evidence; the only held-out evaluation is the [500-question run](#longmemeval_s-500-question-held-out-run-final-spent).

### External headline scores

Headline scores need matching metrics. OpenExp's reported 98.6% is session Recall@10 without generated answers; OMEGA's 466/500 correct answers equal 93.2% per-question accuracy, and its 95.4% headline uses task averaging. They do not form a comparable QA leaderboard. The [primary-source integrity record](../benchmarks/results/longmemeval_external_integrity_research_2026-10-21.json) links the reports, evaluation code, development accounts and unresolved methodological questions; it established no independent untouched-split reproduction.

Reproduce the diagnostic and its synthetic regression checks:

```sh
uv run --no-project python benchmarks/public/longmemeval_quality.py
uv run --no-project python -m unittest discover -s benchmarks/public -p 'test_longmemeval_quality.py'
```

## Candidate improvements to memory quality

These designs are hypotheses, not measured improvements. They extend the [evidence-ledger proposal](../benchmarks/results/longmemeval_role_failure_diagnostic_v1.json), use recorded failures to identify mechanisms rather than question-specific rules, and the 93/100 result is not a native production score or evidence that only seven general failures remain.

A standalone [local research prototype](../benchmarks/research/evidence/RUN.md) implements source-checked claims, distinct counts/sums/comparisons, bounded evidence repair and deletion planning over declared proofs. It uses supplied annotations and typed queries, does not extract assertions from natural-language questions and does not change the production engine. The optional revision-pinned `narrative-lens` bridge uses its entity resolver with explicit corrections, without model inference. The [synthetic development receipt](../benchmarks/results/evidence_program_v1/README.md) records reproducible examples and deletion/replay checks and reports no benchmark score or extraction-quality measurement.

### Execute answers over attributed claims and events

- Keep a query-specific table of assertions: entity and event identity, predicate and argument roles, value/unit, polarity/modality, event-time interval, observation time, validity, original source/version/span. Preserve alternative identity assignments. Distinguish payment from attendance, participation from leadership, plans from completed events, a new observation from a new event.
- Compile supported questions into bounded typed operations (distinct count, sum, comparison, temporal selection, relation joins), execute them deterministically and return operands and source references. If all admissible identity/time interpretations give the same result, their uncertainty need not force abstention; otherwise keep the conditional result or unresolved operands.
- Exhausting a retrieval pool does not prove complete enumeration; bounds over observed candidates are not bounds over all events. Incomplete solver search must stay explicit.
- WARM already has exact triple postings, multi-hop traversal, bitemporal facts and source/premise recovery. The new work is evidence-addressed event assertions and their executable relation semantics, not another generic graph. Exact execution cannot show that a model extracted the correct assertion. `narrative-lens` entity corrections, evidence ranges and uncertainty types are possible adapter inputs (some are uncommitted work; its fiction annotations are not automatic organizational truth extraction).

### Retrieve missing operands and counterevidence

- After initial retrieval, identify the missing binding or defeater (which event an alias names, whether an action happened, an unknown amount, an explicit cancellation or correction), issue bounded searches for those gaps, and pack complete premise groups by additional answer-relevant coverage within the same total context and round budgets. Keep the direct path for questions that need no structured operations.
- This extends static subqueries and premise expansion with feedback from the evidence found. The [challenge experiment](../benchmarks/research/challenge/src/lib.rs) already retrieves scoped counterevidence; use it as the baseline.
- A derivation record should link each output value to its source spans, interpretation and operation. Quote matching and NLI check parts of that record and do not prove factual truth; NLI must report model unavailability separately from a neutral result.
- Precedent: [IRCoT](https://aclanthology.org/2023.acl-long.557/) (iterative retrieval), [Zep](https://arxiv.org/abs/2501.13956) and [HippoRAG 2](https://arxiv.org/abs/2502.14802) (temporal graph memory, graph/passage integration). Their reported gains do not predict WARM gains.

### Forget scoped information across its derivations

- The Bemula adapter reviews truncated turn text in independent batches; the published run's zero purged IDs returned does not establish correct target selection or protection against inference.
- Compile a request into entity, attribute, temporal scope, exceptions, replacement information and future-retention intent. Select proposition occurrences and copies across turns, summaries and derived records, preserving unrelated information from mixed turns. Make deletion, residual replacement and invalidation one recoverable operation; use source and scope generations to reject stale replay while permitting explicitly allowed new learning; invalidate dependent postings, caches and evidence.
- For declared inference rules, represent alternative support as sets of required premises. Copies and summaries keep their underlying source dependencies and are not independent support. Seek a bounded deletion or coarsening plan that breaks every known proof of the forbidden target while respecting protected facts; if preservation constraints make that impossible, report the conflict. The checks cover only the recorded evidence and rule vocabulary, not arbitrary model inference or guessing.
- WARM already has exact forgetting scopes and research claim-family deletion; the new invariant spans alternative derivations and replay. The `narrative-lens` actor-forgetting action retains proposition/evidence history and must not be substituted for WARM privacy deletion.

### Compare mechanisms before a live benchmark

Local/free development checks, in order:

| Comparison | What it isolates |
|---|---|
| Same retained sources: reader, ledger-only reader, ledger plus typed operations | Extraction and evidence use, separate from retrieval |
| Supplied correct assertions versus extracted assertions | Reasoning/retrieval ceiling versus extraction errors |
| Static searches versus missing-operand searches at equal budgets | Evidence coverage after final packing |
| Bounded proof-aware forgetting versus current scope selection | Forgotten/preserved proposition sets and alternative support |

- Use independently generated cases with homonyms, reversed relations, repeated events, updates, ambiguous dates, mixed sensitive/unrelated facts and alternate proofs. Rename entities, reorder independent observations and split/merge turns without changing expected semantics.
- Measure unsupported answers, false merges, operand coverage, extraction failures, latency, memory and mutation cost. Test crash/retry/reopen, stale replay and sensitive-marker absence for deletion.
- Associative sketches are a later candidate-generation experiment. The [global phase sidecar](../benchmarks/results/holographic_context_v1/README.md) lost to exact intersection and [phase-routing screens](../benchmarks/results/holographic_router_synthetic_v1/README.md) failed their gates. A different scoped sketch must beat exact postings and conventional semantic expansion under matched memory/output budgets, resolve to exact current source IDs, and rebuild affected segments after deletion; it cannot establish absence, exact counts or erasure.
- No paid development calls or new live benchmark runs are authorized by this work, and no further held-out evaluation of a tuned variant is valid. A later authorized live comparison must use the native pipeline, freeze extraction/retrieval/reader policies and budgets, count every model stage, retain regressions, and separate retrieval coverage from end-to-end QA and forgetting metrics. These directions target memory quality; they do not establish SIFT/VIBE ANN improvements.

## Checked-in inputs and reports

The [2026-09-14 reports](../benchmarks/results/review-2026-09-14) were produced locally on an Apple M4, macOS arm64. The Node evaluation records Node version, model identity, preprocessing fingerprint, artifact revisions, dtype and dataset SHA-256; Rust reports record engine version, dimensions, corpus size, architecture and operating system.

- [Operational relevance fixture](../tests/fixtures/relevance.json): 12 documents and 12 distinct labeled queries.
- [Paraphrase fixture](../tests/fixtures/semantic-paraphrases.json): 10 documents and 10 queries with less direct lexical overlap.
- [Paraphrase results](../benchmarks/results/review-2026-09-14/paraphrase-relevance.json): lexical, hybrid, optional reranked relevance and latency, plus projection fidelity.
- Concurrent sparse query/update reports at [1,200](../benchmarks/results/review-2026-09-14/workload-1200.json) and [10,000](../benchmarks/results/review-2026-09-14/workload-10000.json) stored vectors.

These are small curated regression datasets, not externally validated benchmark collections. The queries are distinct from the stored passages, but this is not a blind evaluation; do not extrapolate semantic accuracy or capacity from them. Workload timings are short local runs with normal OS caching, not throughput guarantees or comparisons with the previous implementation. Training happens before the concurrent interval; updates invalidate the ANN cache, so the timed workload includes fallback retrieval.

## Run document relevance without a model

```sh
cargo run --release --bin warm-eval -- \
  --dataset tests/fixtures/relevance.json --dimensions 4096 --k 3 --assert-min-recall 0.90
```

### Dataset format

A dataset is a UTF-8 JSON object with nonempty `documents` and `queries` arrays. Queries are evaluation inputs, not documents to ingest. Use unique document IDs and independently worded queries; repeated labels count once. Unknown top-level fields such as `description` are ignored. Invalid JSON, missing fields, empty datasets and labels referencing absent IDs fail the run.

| Field | Required | Meaning |
|---|---|---|
| `documents[].id` | yes | Nonempty document identifier |
| `documents[].text` | yes | Original source text to index |
| `documents[].sourceUri` | no | Source reference retained with chunks |
| `documents[].version` | no | Application-defined source version |
| `documents[].metadata` | no | JSON metadata retained with the document |
| `documents[].chunkWords` | no | Target word count per chunk, 1-4096; defaults to 256 |
| `documents[].overlapWords` | no | Word overlap below `chunkWords`; defaults to the smaller of 32 and `chunkWords - 1` |
| `documents[].storeText` | no | Whether to retain chunk text; defaults to true |
| `documents[].embeddings` | no | One finite numeric vector per generated chunk |
| `documents[].titleWeight` | no | First-line term weighting in the first chunk, 1-16; 1 or absent leaves it unchanged |
| `queries[].text` | yes | Query text, used for lexical retrieval |
| `queries[].relevantIds` | yes | Nonempty array of existing document IDs judged relevant; binary labels, without grades |
| `queries[].embedding` | no | Query vector in the same embedding space as the documents |
| `embeddingSpace` | no | Object with required `model`, `revision`, `dimensions`, `normalization` and `metric`; see [embedding compatibility](production-readiness.md) |

For text-only lexical evaluation omit all embedding fields. Embedding evaluation needs compatible vectors and the embedding-space configuration of the document API; the harness does not generate vectors or load a model. Complete example, saved as `my.json`:

```json
{
  "documents": [
    {"id": "backup", "text": "Restore lost records from a verified backup on a separate disk."},
    {"id": "index", "text": "Schedule search index maintenance outside the ingestion path."}
  ],
  "queries": [
    {"text": "How can I restore lost records?", "relevantIds": ["backup"]}
  ]
}
```

```sh
cargo run --release --bin warm-eval -- --dataset my.json --dimensions 4096 --k 3
```

| Metric or flag | Definition |
|---|---|
| `--k` | Distinct document IDs scored per query, 1-1000, default 10. Retrieval collects at most 1,000 chunk candidates, keeps the first occurrence of each document ID, then scores the first `k`. |
| recall@k | Fraction of labeled documents retrieved, averaged across queries |
| MRR@k | First relevant rank |
| nDCG@k | Binary relevance |
| `--assert-min-recall 0.90` | Fails if average recall@k is below 0.90; no floor on every query or on MRR/nDCG. Omitting it sets a zero floor. |
| Latency | Microseconds; covers retrieval before document deduplication, excludes ingestion |

The JSON output holds document-deduplicated recall@k, MRR@k, nDCG@k and query latency. CI runs this fixture alongside the synthetic self-recall floor. Add domain documents and independent relevance labels to test application behavior; do not add exact copies of stored text as queries.

## Run real local model evaluation

Build the native module with `npm run build` and install `@huggingface/transformers` separately. Obtain model artifacts in explicit local directories. The recorded run used these ONNX q8 artifacts:

| Role | Model | Artifact revision |
|---|---|---|
| Embedding | Xenova/all-MiniLM-L6-v2 | 751bff37182d3f1213fa05d7196b954e230abad9 |
| Reranking | Xenova/ms-marco-MiniLM-L-6-v2 | a09144355adeed5f58c8ed011d209bf8ee5a1fec |

```sh
node scripts/evaluate-local-model.mjs \
  --model-dir /path/to/minilm \
  --revision 751bff37182d3f1213fa05d7196b954e230abad9 \
  --dataset tests/fixtures/semantic-paraphrases.json \
  --reranker-dir /path/to/reranker \
  --reranker-revision a09144355adeed5f58c8ed011d209bf8ee5a1fec \
  --output /tmp/paraphrase-results.json
```

- Omit both reranker options to evaluate embeddings alone.
- Inference uses mean-pooled, L2-normalized embeddings; query/document prefixes and dtype are part of the adapter's schema revision fingerprint. The application must configure the store from `embedder.space`.
- Reusing an artifact label after changing its files defeats revision checking; keep local artifacts immutable. See [Transformers.js local-model configuration](https://huggingface.co/docs/transformers.js/custom_usage).
- Reported: hit@1, hit@5, MRR@5 and p95 query latency for lexical and hybrid retrieval, plus a separate reranked result when enabled. Model loading and ingestion are excluded from query latency; the first query is not separately warmed up.
- It also embeds the corpus into the sparse signed projection and measures top-5 neighbor overlap against exact dense cosine on distinct queries. That is approximation fidelity, not semantic relevance; exact dense document retrieval avoids the projection loss.

## Concurrent workload

```sh
cargo run --release --features cli --bin warm-workload -- --vectors 1200 --operations 300 --dimensions 4096
cargo run --release --features cli --bin warm-workload -- --vectors 10000 --operations 1000 --dimensions 4096
```

One writer replaces vectors and deletes/reinserts every fifth ID while one reader queries top-10 neighbors. Reports: p95/p99 latency, elapsed time, final live count. For capacity planning, increase the corpus and duration, use real embeddings and metadata filters, monitor resident memory and disk, and include compaction and maintenance.

## Distribution checks

- `npm test` exercises the native public APIs across child-process restarts and checks queue backpressure.
- `npm run test:package` packs the built application, installs the tarball in a temporary project, and loads CJS, ESM, the native module and the document adapter.
- `npm run test:types` compiles a consumer of the generated native declarations and document adapter under strict TypeScript, including invalid-input type checks.
- CI runs native/package checks on Linux, macOS and Windows; local results establish only the current machine's behavior. Publishing is a separate release action.
