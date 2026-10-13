# LLM LangGraph content generator

Content generation pipeline that writes posts for Instagram, LinkedIn, Medium and
Substack using LangGraph orchestration, with an optional AI image per post. See
[docs/llm-setup.md](docs/llm-setup.md) for LLM provider details,
[docs/image-generation.md](docs/image-generation.md) for the image pipeline and
[docs/rag.md](docs/rag.md) for the RAG pipelines.

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
  | `DATABASE_URL` | Neon dashboard → Connection Details (direct, no `-pooler`), for RAG storage |
  | `NEON_AUTH_JWKS_URL` | Neon dashboard → Auth (JWKS endpoint, used to verify request JWTs) |

- **Run the app:**

  ```bash
  uv run uvicorn app:app --reload
  ```

  > **Cold start warning:** the embedding model
  > (`paraphrase-multilingual-MiniLM-L12-v2`, int8 ONNX) is downloaded on first
  > boot (~120MB). Subsequent cold starts load from cache (~1–2s). HF Spaces
  > caches it after the first run so subsequent cold starts are faster.

## Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `GROQ_API_KEY` | Yes | API key for Groq, the primary LLM provider |
| `OPENROUTER_API_KEY` | Yes | API key for OpenRouter, the secondary provider that supplies the free model list |
| `CLOUDFLARE_API_TOKEN` | For images | Cloudflare API token used to call Workers AI image models |
| `CLOUDFLARE_ACCOUNT_ID` | For images | Cloudflare account id that owns the Workers AI models |
| `DATABASE_URL` | For RAG | Neon Postgres connection string used to store and retrieve embedded chunks |
| `NEON_AUTH_JWKS_URL` | Yes | Neon Auth JWKS endpoint for JWT verification — found in Neon dashboard → Auth |

## Deployment

Deployed on Render as a Docker web service using the Dockerfile at repo root.

> **Deploy checklist — do these before the first deploy or it will break:**
> 1. Set `ALLOWED_ORIGIN` to your Render URL before deploying — defaults to
>    `localhost:5173` which blocks all prod requests.
> 2. `VITE_*` variables must be available to the **Docker build**, not just
>    runtime. In Render: service settings → Environment → enable
>    "Available to build environment" for `VITE_NEON_AUTH_URL` and
>    `VITE_API_BASE_URL`. Without this the frontend bundle is built with
>    empty strings and API calls go nowhere.

**Render environment variables required:**

| Variable | Required | Description |
| --- | --- | --- |
| `GROQ_API_KEY` | Yes | Groq LLM provider |
| `OPENROUTER_API_KEY` | Yes | OpenRouter fallback provider |
| `CLOUDFLARE_API_TOKEN` | For images | Cloudflare Workers AI |
| `CLOUDFLARE_ACCOUNT_ID` | For images | Cloudflare account |
| `DATABASE_URL` | For RAG | Neon direct connection string (no `-pooler`) |
| `NEON_AUTH_JWKS_URL` | Yes | Neon Auth JWKS endpoint |
| `ALLOWED_ORIGIN` | Yes | Your Render service URL, e.g. `https://saymore.onrender.com` |
| `VITE_NEON_AUTH_URL` | Yes | Neon Auth URL — baked into the frontend bundle at build time |
| `VITE_API_BASE_URL` | Yes | API base URL — leave **empty** on Render (same-origin requests); use `/api` locally so the Vite proxy forwards to `:8000` |

`VITE_*` variables are Vite build-time values. They must be set as Render
environment variables before the Docker image builds — they are inlined into
the JS bundle during `npm run build` and are not available at runtime.

**Cold start:** the embedding model (~120MB) is baked into the Docker image at
build time (`FASTEMBED_CACHE_PATH=/app/.cache/fastembed`), so cold starts only
load it from the image cache — no download at runtime.

SPA client-side routing is handled by the catch-all route in `app.py` —
no separate redirect rules needed on Render.

## Architecture

The pipeline is orchestrated with LangGraph (`src/graph/`):

`router_node` → RAG node (`arxiv_rag_node` for Medium/Substack,
`news_rag_node` for LinkedIn; Instagram skips RAG) → `llm_node` → platform node
(`linkedin_node`, `instagram_node`, `medium_node`, `substack_node`) → `image_node`
(only when images are enabled)

- **Router** (`src/graph/builder.py`): `router_node` normalizes flags and
  `_route_after_router` picks which RAG pipeline runs based on platform — arXiv for
  Medium/Substack, BBC news for LinkedIn, none for Instagram — before generation.
  Details in [docs/rag.md](docs/rag.md).
- **Prompts** (`src/prompts/`): `build_prompt` dispatches to one builder per
  platform, each with its own system message and structure rules. The human
  message carries the per-request context: topic, audience, tone
  (`build_tone_instruction`, selected via the `Tone` enum) and language. When
  images are enabled the builder also asks for a scene tag (`[HEADER IMAGE: ...]`
  for LinkedIn, Medium and Substack, `[POST IMAGE: ...]` for Instagram); the
  platform node strips that line out of the text and keeps it as `image_prompt`.
- **LLM clients** (`src/llm/`): Groq is the primary provider and OpenRouter the
  secondary one; `src/llm/fallback.py` cascades from the selected model of either
  provider into the other provider's models, yielding a status update per attempt.
  Per-user request and token limits live in `src/llm/security.py`.
- **Embeddings** (`src/rag/`): **fastembed** — lightweight ONNX-based
  embedding (int8 quantized, no torch dependency), same multilingual MiniLM
  model as before. Details in [docs/rag.md](docs/rag.md).
- **Images** (`src/chains/`): `image_node` is async, so the graph must be invoked
  with `await graph.ainvoke()`. It streams the extracted scene description (which
  already carries the platform's `IMAGE_STYLE` from the prompt) through
  `run_image_with_fallback`, which tries Cloudflare models in turn until one
  returns an image. Rate limits live in `src/chains/image_security.py`.

RAG is live with two pipelines (arXiv for Medium/Substack, BBC news for
LinkedIn) — see [docs/rag.md](docs/rag.md) for how they work. Provider details,
secrets and the daily model checks are documented in
[docs/llm-setup.md](docs/llm-setup.md), the image pipeline in
[docs/image-generation.md](docs/image-generation.md).

### Frontend

React 19 + Vite, with `@neondatabase/neon-js` for Neon Auth.

Run: `cd frontend && npm install && npm run dev`

Env: copy `frontend/.env.local.example` to `frontend/.env.local` and fill in
`VITE_NEON_AUTH_URL` and `VITE_API_BASE_URL`

### Supported languages

English, Spanish, French, Italian.

Adding a new language is a one-line change in `src/graph/enums.py` — no other
code change needed. The translation pipeline handles everything downstream
automatically.

## Running Tests

Full breakdown, markers and latest results in [docs/tests.md](docs/tests.md).

- **Default suite** (unit + RAG network tests, live tests skipped):

  ```bash
  pytest
  ```

- **Unit only** (what CI runs):

  ```bash
  pytest -m "not integration"
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

## Known limitations

- **Forgot password**: UI stub only. Implement once Neon Auth SDK password reset flow
  is confirmed (`resetPassword(email)` + `/reset-password` token route on the frontend).
- **Neon Auth SDK**: pinned at `0.8.0-beta`. Works for MVP. Check for a stable version and upgrade.

## Contributing

Read [CONVENTIONS.md](CONVENTIONS.md) before opening a pull request.
