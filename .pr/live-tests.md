# Live test artifacts for issue #3540

These artifacts were generated against this branch's OpenAI-compatible agent-server gateway.

## Server setup

- Started a real local `openhands.agent_server` process with:
  - `OH_SESSION_API_KEYS_0=live-test-session-key`
  - isolated temporary `HOME`, conversation directory, bash-events directory, and `TMUX_TMPDIR`
  - `OH_WEBHOOKS=[]`, `OH_ENABLE_VSCODE=0`, `OH_ENABLE_VNC=0`, `OH_PRELOAD_TOOLS=0`
- Saved two LLM profiles through `POST /api/profiles/{name}` using `X-Session-API-Key`.
- Called OpenAI-compatible endpoints using `Authorization: Bearer live-test-session-key`.

## Profiles exercised

| Gateway model | Backing profile | Backing LLM config |
| --- | --- | --- |
| `openhands_openai_nano` | `openai_nano` | `model=gpt-5-nano`, OpenAI API key |
| `openhands_haiku_eval_proxy` | `haiku_eval_proxy` | `model=litellm_proxy/anthropic/claude-haiku-4-5-20251001`, `base_url=https://llm-proxy.eval.all-hands.dev`, LiteLLM proxy API key |

## Results

| Artifact | Request | Result |
| --- | --- | --- |
| `live-models.json` | `GET /v1/models` | Returned both profile-backed OpenAI model IDs. |
| `live-openai-nano.json` | `POST /v1/chat/completions` with `model=openhands_openai_nano` | HTTP 200, OpenAI-shaped `chat.completion`, assistant content `OPENAI_GATEWAY_OK`, conversation ID response header present. |
| `live-litellm-haiku.json` | `POST /v1/chat/completions` with `model=openhands_haiku_eval_proxy` | HTTP 200, OpenAI-shaped `chat.completion`, assistant content `LITELLM_HAIKU_GATEWAY_OK`, conversation ID response header present. |
| `live-server.log` | Server stdout/stderr | Shows server startup, profile creation, `/v1/models`, both `/v1/chat/completions` calls, and background cleanup of ephemeral conversations. |

No API keys or bearer tokens are written into these artifacts.
