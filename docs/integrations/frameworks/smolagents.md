# smolagents

`writerslogic_warm_integrations.smolagents` provides `Tool` subclasses `RememberTool`, `RecallTool`, `ForgetTool` and `memory_tools()`.

Tested against `smolagents==1.26.0`, Python 3.12.

## Install

```sh
pip install "writerslogic-warm-integrations[smolagents]"
```

Needs a running `warm-server` whose `--input-dim` matches the embedder (default: 384).

## Use

<!-- quickstart-check: python smolagents -->
```python
from smolagents import CodeAgent, Model
from smolagents.models import ChatMessage
from writerslogic_warm_integrations.core import WarmConfig
from writerslogic_warm_integrations.smolagents import memory_tools

class Offline(Model):                  # scripted stand-in for the LLM; use InferenceClientModel() for a real one
    def generate(self, messages, **kwargs):
        code = 'final_answer(remember(text="Standup moved to 09:30"))'
        return ChatMessage(role="assistant", content=f"Thought: store it\n<code>\n{code}\n</code>")

config = WarmConfig(url="http://127.0.0.1:8080", tenant_id="acme")
agent = CodeAgent(tools=memory_tools(config, user_id="alice"), model=Offline(), add_base_tools=False)
print(agent.run("Remember the standup time."))
```

Runs offline as written against `warm-server --no-auth --input-dim 384`; checked by `scripts/check-readme-snippets.py docs`.

The tools follow smolagents' `Tool` contract: class attributes `name`, `description`, `inputs` (`type` and `description` per input; optional inputs have `nullable: True`) and `output_type`, with `forward` taking exactly those arguments. `CodeAgent` calls them as Python functions (`remember(text=...)`), `ToolCallingAgent` through JSON tool calls. `user_id` scopes `recall` and `forget` to one user (service-side equality filter); `k` is clamped to `max_k` (default 20).

## Sync only

smolagents tools are synchronous (`forward`), so the adapter uses `WarmBackend`; the framework has no async tool path.

## Knobs

All on `WarmConfig`: `url`, `api_key`, `tenant_id`, `collection`, `embedder`, `text_queries`, `zero_trust_key`, `max_fetch`, `overfetch`; or pass a ready `backend=`. BM25 and title weight are native-engine options and not available over HTTP.

## Filters

No filter argument; `user_id` is a top-level equality filter evaluated by the service.

## Conformance

Run through real `CodeAgent` and `ToolCallingAgent` loops with a scripted `Model` subclass (smolagents' own `generate` contract), a real `warm-server`, and the framework's class-level validation (`validate_after_init`): `pytest tests/smolagents`.

## Limitations

- `Tool.to_dict()`/`save()`/`push_to_hub()` are not supported: smolagents requires serializable tools with literal `__init__` defaults, and these tools hold a live backend connection.
- The default `HashingEmbedder` is lexical; supply an `embedder` for semantic recall.
