# OpenAI gateway client compatibility live test notes

Issue: #3540  
Stacked on: #3545

## Local gateway under test

- Branch: `openhands/openai-gateway-client-compat`
- Agent server: `uv run python -m openhands.agent_server --host 0.0.0.0 --port 12000`
- Gateway base URL used by clients: `http://127.0.0.1:12000/v1`
- Auth shape: `Authorization: Bearer compat-key`
- Profile/model: `compat` exposed as `openhands_compat`
- Backing live LLM: `gpt-5-nano` through the saved profile

## Findings that drove code changes

- LibreChat custom OpenAI endpoints default to `stream: true` and send a `user` field.
- Pipecat's OpenAI voice LLM service defaults to streaming and sends `stream_options: {"include_usage": true}`.
- Newer OpenAI-compatible clients can send `developer` messages.

PR changes made for those findings:

- Accept `stream: true` and return OpenAI-compatible `text/event-stream` chat completion chunks.
- Honor `stream_options.include_usage` by emitting a final usage chunk before `[DONE]`.
- Accept `developer` role messages and fold them into the same system-instruction suffix as `system` messages.

The stream currently emits the final agent answer once the agent run completes; it does not stream intermediate tool activity or token-by-token partial agent output.

## Live probes

### OpenAI Python SDK

Command artifact: `.agent_tmp/openai-gateway-live/openai-sdk-smoke.txt`

Result:

```text
models: ['openhands_Default', 'openhands_compat']
nonstream: OpenHands gateway live smoke OK.
stream: streamed OpenHands gateway OK.
stream_usage: {'completion_tokens': 515, 'prompt_tokens': 3905, 'total_tokens': 4420, 'completion_tokens_details': None, 'prompt_tokens_details': None}
```

### Open WebUI v0.9.6

Installed with:

```bash
uvx --python 3.11 open-webui
```

Started with:

```bash
OPENAI_API_BASE_URL=http://127.0.0.1:12000/v1 \
OPENAI_API_KEY=compat-key \
WEBUI_AUTH=False \
ENABLE_SIGNUP=False \
uvx --python 3.11 open-webui serve --host 0.0.0.0 --port 12001
```

Browser validation:

- Opened `https://work-2-lkplmondbvihpwxu.prod-runtime.all-hands.dev/`.
- Verified Open WebUI fetched `/v1/models` and listed `openhands_compat`.
- Selected `openhands_compat`.
- Sent: `Answer exactly: Open WebUI via OpenHands gateway works.`
- UI displayed: `Open WebUI via OpenHands gateway works.`

### LibreChat

Install attempt:

```bash
git clone --depth 1 https://github.com/danny-avila/LibreChat.git /tmp/LibreChat
cd /tmp/LibreChat
npm ci --ignore-scripts
```

Result:

- Dependencies installed successfully.
- Docker-based startup could not be used in this sandbox because the Docker daemon is unavailable and `dockerd` requires root privileges.
- A full LibreChat browser run was therefore blocked by runtime dependencies, but I exercised the documented LibreChat custom endpoint request shape directly against the gateway: `stream: true`, `user`, `temperature`, `top_p`, `presence_penalty`, and `frequency_penalty`.

Command artifact: `.agent_tmp/openai-gateway-live/librechat-shape-smoke.txt`

Result:

```text
librechat_default_stream_shape: LibreChat stream shape works.
```

### Pipecat voice framework

Installed with:

```bash
uv run --python 3.11 --with pipecat-ai --with websockets python ...
```

Import/install result:

```text
pipecat-ai 1.3.0
OpenAILLMService import ok <class 'pipecat.services.openai.llm.OpenAILLMService'>
```

Live OpenAI voice-service path result against the gateway:

```text
supports_developer_role: True
run_inference: Pipecat voice framework path works.
stream: Pipecat voice framework path works.
usage: {'completion_tokens': 346, 'prompt_tokens': 3908, 'total_tokens': 4254, 'completion_tokens_details': None, 'prompt_tokens_details': None}
```

## Remaining limitations

- First streamed chunk is delayed until the agent run finishes; true low-latency token streaming is still a follow-up.
- No tool-call streaming or exposure is implemented, by design for this compatibility PR.
- LibreChat full browser validation should be repeated in an environment with Docker/MongoDB available; the request shape LibreChat documents now succeeds.
