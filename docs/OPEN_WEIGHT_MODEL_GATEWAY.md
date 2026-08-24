# Governed Open-Weight Model Gateway

## Purpose and scope

OAE now contains a **disabled-by-default provider foundation** for a privately hosted, open-weight model endpoint. It is an adapter, not a model download, a model benchmark, or a replacement for proprietary systems. No model weights are committed to this repository, and the foundation does not create a public inference route or attach a model reply to a build worker.

The first transport targets Ollama’s non-streaming `/api/chat` endpoint. Ollama documents this local API and states that its default local base URL is `http://localhost:11434/api`; it also documents a partial OpenAI-compatible interface. [1] [2] OAE deliberately uses the native non-streaming chat endpoint, sends no tool definitions, and does not process model-generated tool calls.

## Model policy

An operator must choose an approved model only after license, security, quality, and model-host review. **Qwen3** is an example evaluation candidate because its official repository describes public open-weight releases, Ollama support, and Apache 2.0 licensing for its open-weight models. [3] This document does not declare Qwen3 or any model production-approved.

| Control | Foundation behavior |
|---|---|
| Activation | `OPEN_WEIGHT_MODEL_ENABLED=false` by default. |
| Endpoint | Server-side environment configuration only. The tenant cannot choose an endpoint. |
| Model identity | Exact model name must match `OPEN_WEIGHT_MODEL_ALLOWED_MODELS`; the endpoint must return the same identity. |
| Tenant boundary | Every call requires a tenant identifier and emits only a SHA-256 tenant pseudonym in its audit metadata. |
| Operation boundary | Only `analyze`, `review`, and `verify` are accepted. `build` and direct execution are rejected. |
| Tool boundary | The request is non-streaming and carries no tools or tool-choice inputs. |
| Size boundary | Prompt, output-token request, and response-character limits are configured server-side. |
| Observability | The returned audit record contains duration, pseudonymized tenant, model, operation, status, and character counts only. It does not contain prompts or replies. |

## Activation sequence

Keep the gateway disabled until there is a private model host on an isolated network. Add an explicit allowlisted model name only after it is installed from an authorized upstream, its license is reviewed, and its immutable image or artifact digest is recorded outside the application database. Configure the endpoint and secret management on the host, not in Git or browser-local storage.

For the first controlled profile, OAE uses `qwen3:8b` in `docker-compose.open-weight.yml`. The overlay provides an internal-only Ollama service and a separate one-shot `ollama-pull-qwen3` tool profile. It deliberately publishes no model-service port. Before running the pull profile, confirm the Ollama image tag, Qwen artifact provenance, and available host capacity. This repository does not pull the artifact automatically.

On the private host, copy the approved environment configuration, set `OPEN_WEIGHT_MODEL_ENABLED=true`, then start the private service and run the one-shot pull tool. After recording its operator-approved provenance, run the smoke test from the API container so the Compose-only hostname is not exposed outside the private network.

```bash
docker compose --env-file .env.production \
  -f docker-compose.production.yml -f docker-compose.open-weight.yml \
  --profile open-weight up -d ollama

docker compose --env-file .env.production \
  -f docker-compose.production.yml -f docker-compose.open-weight.yml \
  --profile open-weight-tools run --rm ollama-pull-qwen3

docker compose --env-file .env.production \
  -f docker-compose.production.yml -f docker-compose.open-weight.yml \
  exec -T api python -m oae.providers.open_weight_smoke_test
```

The final command uses a fixed non-sensitive prompt and emits audit metadata only. It is valid only after OAE itself is running with the `OPEN_WEIGHT_MODEL_*` variables enabled and the allowlist includes exactly the approved profile. A real result must be retained as redacted evidence; it must not be represented by a unit-test fixture.

Run a request-boundary test with a synthetic, non-sensitive prompt. Verify that an allowlisted `analyze`, `review`, or `verify` request produces a response and a redacted audit record. Verify separately that an empty tenant, a non-allowlisted model, an oversized prompt, and a `build` operation are denied before network access. Only after those checks may OAE consider adding a separately authorized API route or durable-event projection.

> A model response is planning material, not execution authority or verification evidence. OAE’s `UNDERSTAND → PLAN → AUTHORIZE → EXECUTE → VERIFY → RECORD` sequence remains unchanged.

## Host boundary

The ordinary sandbox and the current OAE web frontend are not model hosts. A real model runtime requires a separately managed host with adequate CPU or GPU capacity, storage for weights, a private network path to OAE, host-level logging, model-specific license review, resource limits, and operational recovery. Do not expose Ollama’s port publicly. Do not paste a remote install command into a privileged shell without reviewing it and pinning the approved installation method.

## References

[1] [Ollama API introduction](https://docs.ollama.com/api/introduction)

[2] [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility)

[3] [Qwen3 official repository and licensing statement](https://github.com/QwenLM/Qwen3)
