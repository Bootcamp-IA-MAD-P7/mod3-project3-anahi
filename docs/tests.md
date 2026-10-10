# Tests

pytest suite — offline by default, external services gated behind markers.

## Layout

126 tests total: 96 unit, 30 integration.

### Unit (`tests/unit/`, 96 tests)

All mocked, no network, no API keys.

| File | Tests | Covers |
|---|---|---|
| `test_prompts.py` | 44 | Prompt builders: shape, topic/audience/tone/language, user context, tone instruction, RAG block, citations block, image block, dispatch |
| `test_edges.py` | 10 | Graph routing: `_route_after_router` (platform → RAG node), `_route_after_llm`, `_route_after_platform` |
| `test_router_node.py` | 8 | `router_node`: citations and image flag normalization |
| `test_image_security.py` | 8 | Image rate limits (per minute, per user, per account) |
| `test_graph_flow.py` | 5 | End-to-end graph flow with mocked nodes, both RAG nodes patched |
| `test_image_fallback.py` | 5 | Image model cascade: rate limit stops, model failure moves on |
| `test_arxiv_rag_node.py` | 4 | `arxiv_rag_node`: exact cache hit, fuzzy cache hit, cold path call order, graceful failure |
| `test_news_rag_node.py` | 4 | `news_rag_node`: articles found, none found, graceful failure, state passthrough |
| `test_image_node.py` | 4 | `image_node` streaming, status messages, daily limit message |
| `test_graph_compilation.py` | 2 | Graph compiles, expected nodes registered |
| `test_config.py` | 2 | Settings and env loading |

### Integration (`tests/integration/`, 30 tests)

| File | Tests | Marker | What it does |
|---|---|---|---|
| `test_arxiv_rag_integration.py` | 1 | `integration` + `slow` | Real pipeline: arXiv fetch → PDF download/parse → clean → chunk → embed (384 dims). No DB writes |
| `test_news_rag_integration.py` | 1 | `integration` | Real BBC RSS fetch + semantic ranking via `fetch_bbc_articles` |
| `test_db_integration.py` | 10 | `integration` | Real Neon DB, no mocks: cache check, store + retrieve, fuzzy slug match, direct `search_chunks` call, `user_profiles` insert and `updated_at` trigger, `get_user_context` / `upsert_user_context` round-trips |
| `test_openrouter.py` | 10 | `live` | Every OpenRouter free model hits the real API |
| `test_image_generation.py` | 5 | `live` | Every Cloudflare image model generates a real image |
| `test_groq.py` | 3 | `live` | Every Groq model hits the real API |

#### DB integration tests

[test_db_integration.py](../tests/integration/test_db_integration.py) talks to the
real Neon database through `psycopg2` and `src/rag/store.py`. It needs
`DATABASE_URL` in the environment, otherwise the whole module skips via
`pytestmark = pytest.mark.skipif`. pytest does not read `.env`, so export it
first — quote it, the URL contains `&`:

```bash
export DATABASE_URL="$(grep '^DATABASE_URL=' .env | cut -d= -f2-)"
```

Every test uses a function-scoped `conn` fixture that opens a real connection
and, on teardown, rolls back, deletes the fixed rows (`topic_slug =
'test-integration-quantum'`, `user_id = 'test-user-integration'`) and closes —
so no test data is ever left behind, pass or fail. Embeddings come from the real
MiniLM model (384 dims), never from a stub. The user-profile tests cover the
Python layer too: `get_user_context` (missing row → `""`) and
`upsert_user_context` (insert path, then `ON CONFLICT ... DO UPDATE` path).

It also caught a real bug: `retrieve_chunks` passed the embedding as a plain
list, which psycopg2 renders as `ARRAY[...]` (`numeric[]`). pgvector's
`numeric[] → vector` cast is assignment-only, so PostgreSQL could not resolve
`search_chunks(text, numeric[], int)` and raised `UndefinedFunction`. INSERT
worked (assignment context) but every retrieval failed. Fixed with an explicit
cast in [src/rag/store.py](../src/rag/store.py): `search_chunks(%s, %s::vector, %s)`.

## Markers

Defined in [pyproject.toml](../pyproject.toml):

| Marker | Meaning |
|---|---|
| `integration` | Hits real external services over the network and the real Neon DB, no API keys needed |
| `slow` | Slow due to network or model loading |
| `live` | Hits paid/quota APIs, opt-in via `RUN_LIVE_LLM_TESTS=1` |

## Running

```bash
uv run pytest                             # default: everything, live tests skipped
uv run pytest -m "not integration"        # CI path: unit only
uv run pytest -m integration              # RAG network tests + Neon DB tests
uv run pytest tests/integration -m live   # live tests (needs RUN_LIVE_LLM_TESTS=1 + keys)
```

The default run needs no keys and no network for the unit tests; the two RAG
`integration` tests hit the network (arXiv + BBC) and load the embedding model,
adding roughly 45 seconds. The 10 DB tests run only when `DATABASE_URL` is
exported, otherwise they skip and the default run is network-free.

## Results

Last run, 2026-10-09 (with `DATABASE_URL` exported):

| Command | Result |
|---|---|
| `uv run pytest -q` | **108 passed, 18 skipped** in 53.6s |
| `uv run pytest -q -m "not integration"` | **96 passed, 18 skipped, 12 deselected** in 36.3s |
| `uv run pytest -m integration -v` | **12 passed, 114 deselected** in 47.3s |
| `uv run pytest -m integration -q` (no `DATABASE_URL`) | **2 passed, 10 skipped, 114 deselected** in 40.9s |

### What the skips and deselections mean

- **18 skipped** — the `live` tests (`test_groq.py`, `test_openrouter.py`,
  `test_image_generation.py`): 3 + 10 + 5. They carry
  `skipif(RUN_LIVE_LLM_TESTS != "1")`, so without that env var every run skips
  them. They are not broken, they are waiting for an opt-in.
- **+10 skipped** — `test_db_integration.py` when `DATABASE_URL` is not in the
  environment. Same opt-in pattern, different gate.
- **12 deselected** — the 12 `integration` tests (2 RAG + 10 DB). `-m "not
  integration"` is a *filter expression*, not a failure: pytest counts
  filtered-out tests as "deselected". The CI path excludes them on purpose so
  the default PR check needs no network and no database.

### Real integration test results

`pytest -m integration -v --durations=12`, against live services and the real
Neon database:

| Test | Result | Duration | Verified |
|---|---|---|---|
| `test_arxiv_rag_integration.py::test_arxiv_pipeline_real` | PASSED | 1.53s | Real arXiv fetch (1 paper), real PDF download + parse (>500 chars), clean, chunk, embed → 384-dim vectors |
| `test_news_rag_integration.py::test_bbc_pipeline_real` | PASSED | 3.06s | Real BBC business + technology RSS feeds, semantic ranking → ≤3 articles, non-empty titles/summaries, `https://` URLs |

#### DB integration results

Same run → **12 passed in 47.8s**, 10 of them DB (≈36s of the wall time is
importing `sentence-transformers` and loading the MiniLM model at collection):

| Test | Duration | Verified |
|---|---|---|
| `test_topic_not_cached_on_empty` | 0.31s | `topic_is_cached("test-integration-quantum")` → `False` before any write |
| `test_store_and_retrieve_chunks` | 1.16s | 2 chunks with real 384-dim MiniLM embeddings stored, `topic_is_cached` → `True`, `retrieve_chunks` → non-empty dicts with the 6 expected keys |
| `test_find_similar_slug` | 0.75s | typo slug `test-integration-quantom` (ratio ≈ 0.96) resolves to `test-integration-quantum` |
| `test_find_similar_slug_no_match` | 0.33s | `completely-different-topic-xyz` → `None` |
| `test_search_chunks_sql_function` | 0.51s | direct `SELECT * FROM search_chunks(...)` returns rows whose 6 columns match the function signature |
| `test_user_profile_insert_and_retrieve` | <0.27s | `user_profiles` insert + select round-trips `user_context` |
| `test_user_profile_updated_at_trigger` | 1.74s | 1s between two `upsert_user_context` calls, `updated_at` increased → the `user_profiles_updated_at` trigger fires on the conflict update |
| `test_get_user_context_empty` | 0.31s | `get_user_context` on a missing row → `""` |
| `test_upsert_and_get_user_context` | 0.62s | upsert `Acme Corp, professional tone` → `get_user_context` returns it (insert path) |
| `test_upsert_updates_existing` | 1.03s | second upsert wins → `updated context`, single row (conflict update path) |

Wall time for the full `-m integration` run was 47.8s despite ~12s of test
calls — the remaining time is importing `sentence-transformers` and loading the
MiniLM model at collection.

### Live integration results

`RUN_LIVE_LLM_TESTS=1 uv run pytest tests/integration/test_openrouter.py -v`,
run 2026-10-10 with `BLOCKED_MODELS` emptied so every free catalog model was
tested:

| Result | Count |
|---|---|
| passed | 12 / 16 (85.0s) |
| failed | 4 |
| skipped | 0 — no model returned an empty response |

Failures:

- **2 blocked — 403** `thinkingmachines/inkling:free` and
  `thinkingmachines/inkling-small:free`: OpenRouter gates both to agentic
  harnesses (`"only available on agentic harnesses"`), so plain chat always
  gets 403. These 2 ids are back in `BLOCKED_MODELS`.
- **2 transient — 429** `google/gemma-4-26b-a4b-it:free` and
  `google/gemma-4-31b-it:free`: `upstream_provider_shared_pool` rate limits
  from Google AI Studio. Not blocked — 429 is provider capacity, not a broken
  model, and the daily workflow retries once before opening an issue.

Also confirmed in this run:

- `DEFAULT_MODEL` (`nvidia/nemotron-3.5-lightning:free`) is present in the free
  catalog and generated successfully.
- `poolside/laguna-s-2.1:free` and
  `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` passed — both were in
  the old blocked list and are now unblocked.
- Embedding models are excluded by `get_available_models()`; all 15 catalog
  entries tested are chat models.

Ruff passes on the whole suite (`.pre-commit-config.yaml` runs it on commit).
