# Integrations

Adapters that put WARM behind the interfaces of agent frameworks, editors and Claude. Each row links to its canonical page; the package README only carries install, a short quickstart and an options table.

Python frameworks reach `warm-server` through `warm-sdk`; JS frameworks run the native engine in process; editors and the Claude memory tool speak MCP to `warm-mcp`.
Python install is always `pip install "writerslogic-warm-integrations[<extra>]"` against a running `warm-server`; install one framework extra per environment, because their dependency trees conflict. JS packages are not published yet; build them from the [source workspace](frameworks/js-core.md#source-setup).

## Python frameworks

Python 3.11+ (tested on 3.12), `warm-sdk` >= 0.1.3.

| Adapter | Host and tested version | Install extra | Status |
|---|---|---|---|
| [LangChain](frameworks/langchain.md) | langchain-core 1.6.12 | `langchain` | tested |
| [LangGraph](frameworks/langgraph.md) | langgraph 1.2.16 | `langgraph` | tested |
| [LlamaIndex](frameworks/llamaindex.md) | llama-index-core 0.14.25 | `llamaindex` | tested |
| [Haystack](frameworks/haystack.md) | haystack-ai 3.4.0 | `haystack` | tested |
| [DSPy](frameworks/dspy.md) | dspy 3.4.1 and 3.5.0 | `dspy` | tested |
| [OpenAI Agents](frameworks/openai-agents.md) | openai-agents 0.24.0 | `openai-agents` | tested |
| [Pydantic AI](frameworks/pydantic-ai.md) | pydantic-ai-slim 2.58.0 | `pydantic-ai` | tested |
| [smolagents](frameworks/smolagents.md) | smolagents 1.26.0 | `smolagents` | tested |
| [LiteLLM](frameworks/litellm.md) | litellm 1.103.10 | `litellm` | tested |
| [CrewAI](frameworks/crewai.md) | crewai 1.15.28 | `crewai` | tested |
| [AutoGen](frameworks/autogen.md) | autogen 0.7.5 | `autogen` | tested |
| [AG2](frameworks/autogen.md) | ag2 1.1.2 | `ag2` | tested (tools only) |
| [Semantic Kernel](frameworks/semantic-kernel.md) | semantic-kernel 1.45.0 | `semantic-kernel` | tested |
| [mem0](frameworks/mem0.md) | mem0ai 2.2.1 | `mem0` | tested (shim) |
| [Letta](frameworks/letta.md) | letta-client 1.12.1 | `letta` | tested (no live Letta server) |

How each was verified, and the limits they share: [matrix](frameworks/MATRIX.md).

## JavaScript and TypeScript

Native engine in process; Node 20+ (tested 26.8), `writerslogic-warm` >= 0.6.5.

| Adapter | Host and tested version | Package | Status |
|---|---|---|---|
| [Core](frameworks/js-core.md) | none | `@writerslogic/warm-core` | tested |
| [LangChain.js](frameworks/langchainjs.md) | @langchain/core 1.2.19 | `@writerslogic/warm-langchain` | tested |
| [LlamaIndex.TS](frameworks/llamaindex-ts.md) | llamaindex 0.12.1 | `@writerslogic/warm-llamaindex` | tested |
| [Mastra](frameworks/mastra.md) | @mastra/core 1.78.0 | `@writerslogic/warm-mastra` | tested |
| [OpenAI Agents JS](frameworks/openai-agents-js.md) | @openai/agents 0.20.0 | `@writerslogic/warm-openai-agents` | tested |
| [Vercel AI SDK](frameworks/vercel-ai.md) | ai 7.0.146 | `@writerslogic/warm-vercel-ai` | tested |

## MCP, editors and Claude

All of these speak to [`warm-mcp`](mcp/README.md).

| Adapter | Host | Install | Status |
|---|---|---|---|
| [warm-mcp launcher](mcp/README.md) | any MCP client | `npx -y writerslogic-warm-mcp` or `uvx warm-mcp` | tested |
| [Claude memory tool](mcp/memory-tool.md) | Anthropic `memory_20250818` (Python, TypeScript) | `pip install writerslogic-warm-claude-tool` or `npm install writerslogic-warm-claude-tool` | tested |
| [Claude Code](editors/README.md#claude-code) | plugin | `claude plugin install` from the repo marketplace | plugin validated, headless session run |
| [Codex CLI](editors/README.md) | 0.163.0 | `codex mcp add` | CLI verified, no model session |
| [Gemini CLI](editors/README.md) | 0.64.0 | `gemini mcp add` or extension | CLI verified, no model session |
| [VS Code](editors/README.md) | 1.141.0 | `code --add-mcp` | config verified |
| [Cursor, Windsurf, Zed, Cline, Continue, Claude Desktop](editors/README.md) | current docs | copy the config from `integrations/editors/<host>/` | config-validated only |

## Other

| Page | Use |
|---|---|
| [Organizational knowledge](organizational-knowledge.md) | Import curated multi-application documents (Rust example and JavaScript adapter) |
| [Vectra migration](vectra-migration.md) | Move a Vectra index to WARM |
