# LLM LangGraph content generator

Content generation pipeline that writes posts for Instagram, LinkedIn, Medium and
Substack using LangGraph orchestration, with an optional AI image per post. See
[docs/llm-setup.md](docs/llm-setup.md) for LLM provider details and
[docs/image-generation.md](docs/image-generation.md) for the image pipeline.

## Setup

- **Requirements:** Python 3.13+, [uv](https://docs.astral.sh/uv/)
- **Installation:**

  ```bash
  uv sync
  ```

- **Configuration:** copy `.env.example` to `.env` and fill in the required keys:

  | Key | Where to get it |
  | --- | --- |
  | `GROQ_API_KEY` | https://console.groq.com/keys |
  | `OPENROUTER_API_KEY` | https://openrouter.ai/settings/keys |
  | `CLOUDFLARE_API_TOKEN` | https://dash.cloudflare.com/profile/api-tokens (Workers AI read permission) |
  | `CLOUDFLARE_ACCOUNT_ID` | Cloudflare dashboard, Workers & Pages, Account ID |

- **Run the app:**

  ```bash
  uv run python app.py
  ```

  > Note: `app.py` is currently a stub, so the command starts without output yet.

## Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `GROQ_API_KEY` | Yes | API key for Groq, the primary LLM provider |
| `OPENROUTER_API_KEY` | Yes | API key for OpenRouter, the secondary provider that supplies the free model list |
| `CLOUDFLARE_API_TOKEN` | For images | Cloudflare API token used to call Workers AI image models |
| `CLOUDFLARE_ACCOUNT_ID` | For images | Cloudflare account id that owns the Workers AI models |

## Architecture

The pipeline is orchestrated with LangGraph (`src/graph/`):

`router_node` → `rag_node` (only when RAG is enabled) → `llm_node` → platform node
(`linkedin_node`, `instagram_node`, `medium_node`, `substack_node`) → `image_node`
(only when images are enabled)

- **Prompts** (`src/prompts/`): `build_prompt` dispatches to one builder per
  platform, each with its own system message and structure rules. When images are
  enabled the builder also asks for a scene tag (`[HEADER IMAGE: ...]` for LinkedIn,
  Medium and Substack, `[POST IMAGE: ...]` for Instagram); the platform node strips
  that line out of the text and keeps it as `image_prompt`.
- **LLM clients** (`src/llm/`): Groq is the primary provider and OpenRouter the
  secondary one; `src/llm/fallback.py` cascades from the selected model of either
  provider into the other provider's models, yielding a status update per attempt.
  Per-user request and token limits live in `src/llm/security.py`.
- **Images** (`src/chains/`): `image_node` is async, so the graph must be invoked
  with `await graph.ainvoke()`. It combines the scene description with the
  platform's `IMAGE_STYLE` and streams it through `run_image_with_fallback`, which
  tries Cloudflare models in turn until one returns an image. Rate limits live in
  `src/chains/image_security.py`.

The frontend is planned as a Gradio UI, and RAG over arXiv papers is planned as the
grounding source (`rag_node` raises `NotImplementedError` today). Provider details,
secrets and the daily model checks are documented in
[docs/llm-setup.md](docs/llm-setup.md), the image pipeline in
[docs/image-generation.md](docs/image-generation.md).

## Running Tests

- **Default suite (offline):**

  ```bash
  pytest
  ```

- **Live LLM integration tests** (requires `GROQ_API_KEY` and `OPENROUTER_API_KEY`):

  ```bash
  RUN_LIVE_LLM_TESTS=1 pytest tests/integration/ -m live
  ```

- **Live image integration tests** (requires `CLOUDFLARE_API_TOKEN` and
  `CLOUDFLARE_ACCOUNT_ID`):

  ```bash
  RUN_LIVE_LLM_TESTS=1 pytest tests/integration/test_image_generation.py -m live
  ```

  Both live suites are opt-in and skipped unless `RUN_LIVE_LLM_TESTS=1`.

## Contributing

Read [CONVENTIONS.md](CONVENTIONS.md) before opening a pull request.
