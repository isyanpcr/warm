# Framework adapter matrix

Every adapter was run against a real `warm-server` (Python) or the native Node addon (JS). Python 3.12, one isolated environment per framework (`integrations/python/run-matrix.sh`). Framework dependency trees conflict, so install exactly one framework extra per environment.

## Python (`pip install "warm-integrations[<extra>]"`)

Host versions and install lines are on the [integrations overview](../index.md). Each row is the verification behind its adapter page.

| Extra | Verification |
|---|---|
| `langchain` ([page](langchain.md)) | `langchain-tests` VectorStore (sync+async) and Retriever suites |
| `langgraph` ([page](langgraph.md)) | `langgraph-checkpoint-conformance` 0.0.2, level FULL (81 passed); store checked against `InMemoryStore` |
| `llamaindex` ([page](llamaindex.md)) | 21 filter cases against `SimpleVectorStore`; index, retriever, storage-context, memory round trips |
| `haystack` ([page](haystack.md)) | `haystack.testing.document_store` mixins (81 passed, 2 upstream-only skips) |
| `dspy` ([page](dspy.md)) | real `ChainOfThought` and `ReAct` programs on `DummyLM` |
| `openai-agents` ([page](openai-agents.md)) | real `Runner` with a scripted model |
| `pydantic-ai` ([page](pydantic-ai.md)) | `Agent.run` with `FunctionModel` / `TestModel` |
| `smolagents` ([page](smolagents.md)) | `CodeAgent` and `ToolCallingAgent` with a scripted model |
| `litellm` ([page](litellm.md)) | LiteLLM `mock_response` / `mock_tool_calls` loops |
| `crewai` ([page](crewai.md)) | real `Crew.kickoff()` with a scripted LLM |
| `autogen` ([page](autogen.md)) | real `AssistantAgent` with a replay client |
| `ag2` ([page](autogen.md)) | tool toolkit (AG2 1.x has no memory interface WARM can back) |
| `semantic-kernel` ([page](semantic-kernel.md)) | real `Kernel.invoke` of a search function |
| `mem0` ([page](mem0.md)) | one scenario through real mem0 and the shim; result shapes compared |
| `letta` ([page](letta.md)) | `PassagesResource` signatures; tool source executed against the real server |

Not verified anywhere: `text_queries=True` (the service embeds text itself) needs a server built with `--features local-models` and model directories; it is covered at the wire level with a mock transport only. A running Letta server was not used.

## Limits common to all adapters

They come from `warm-server` (see `docs/SERVER.md`), and each adapter's page lists how it surfaces them:

- The framework core scans the service's metadata cursor in tenant/collection scope. `list` returns at most `max_fetch` matching records and accurately reports more matches; `forget_where` scans every page. Text retrieval still uses exact id-filtered queries. Framework-specific public enumeration limits remain documented on each adapter page.
- Top-level equality filters run in the service. Other operators select document ids from paginated metadata before ranking. Vector-mode recall merges exact cosine results across bounded id groups. Fused text-mode residual queries require at most 1000 eligible records and raise `WarmError(code="filter_limit")` beyond that bound; independently normalized fused scores cannot be merged safely. `overfetch` remains accepted for configuration compatibility.
- Residual queries verify `QueryIn.document_ids` support once from OpenAPI and fail with `unsupported_capability` on older servers. Returned rows must belong to the selected ids and collection, or the adapter raises `invalid_response`. Direct equality-only queries retain their existing compatibility.
- `k` greater than `max_fetch` raises `ValueError` instead of silently truncating.
- Scores are cosine similarity in vector mode and a fused rank score in text mode.
- Metadata keys beginning `_warm_` are reserved.

## JavaScript / TypeScript (`integrations/js`, npm workspace; Node 26.8, TypeScript 5.9)

All packages run against the real native addon (`writerslogic-warm`), no mocks of WARM. Host versions: [overview](../index.md).

| Package | Verification |
|---|---|
| `warm-core` | 62 tests |
| `warm-vercel-ai` | 5 tests: SDK mock models, real tool loop, `streamText` |
| `warm-mastra` | 15 contract tests plus a real `Agent` with semantic recall (Mastra publishes no vector-store test suite) |
| `warm-langchain` | 27 tests mirroring the standard VectorStore behaviors (`@langchain/standard-tests` is not published on npm) and a real `RunnableWithMessageHistory` run |
| `warm-llamaindex` | 20 tests: `VectorStoreIndex`, all 13 `FilterOperator`s, KV store vs `SimpleKVStore` |
| `warm-openai-agents` | 15 tests: `WarmSession` vs `MemorySession`, real `Runner`; ordering at 99/100/101/200+ items |
