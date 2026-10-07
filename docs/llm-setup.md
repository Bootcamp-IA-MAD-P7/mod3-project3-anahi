# LLM Setup

How providers, secrets and the daily model checks fit together.

## LLM Providers

### Groq (primary)

Live today through `src/llm/groq.py`. `DEFAULT_MODEL` is `openai/gpt-oss-120b` and
`AVAILABLE_MODELS` currently holds:

- `openai/gpt-oss-120b` (default)
- `openai/gpt-oss-20b`
- `qwen/qwen3.8-27b`

Free tier limits for these models are documented at
https://console.groq.com/docs/rate-limits

### OpenRouter (secondary)

Live today through `src/llm/open_router.py`. The model list is discovered at import
time by `get_available_models()`, which queries the OpenRouter models endpoint and
keeps every id containing `:free`, falling back to `DEFAULT_MODEL`
(`inclusionai/ling-3.0-flash-sante:free`) when the API is unreachable. Ids listed in
`BLOCKED_MODELS` are filtered out, currently the models that answer 403 because they
only run inside agentic harnesses. Browse the free catalog at
https://openrouter.ai/models?q=:free

### Fallback chain

`run_with_fallback(selected_model, prompt, user_id, provider)` in
`src/llm/fallback.py` is a generator that yields a `FallbackUpdate` per attempt so
callers can show progress. `provider` decides which client starts and therefore the
order:

- `provider="groq"` (default): the selected Groq model rotated to the front, then
  the remaining Groq models in `AVAILABLE_MODELS` order, then the OpenRouter free
  models with `DEFAULT_MODEL` first
- `provider="openrouter"`: the OpenRouter free models rotated so the selected one
  leads (`DEFAULT_MODEL` first when no model is selected), then all Groq models

Any other value falls back to the Groq order. When both lists are exhausted the
generator yields "All models unavailable, please try again later".

Only the first attempt is checked against the rate and token limits. Every retry
after a failure passes `bypass_limits=True` so one cascade does not consume the
user's budget twice.

## Rate Limits

`src/llm/security.py` guards every LLM call per user:

| Limit | Constant | Value |
| --- | --- | --- |
| Requests per minute | `MAX_REQUESTS_PER_MINUTE` | 5 |
| Requests per day | `MAX_REQUESTS_PER_DAY` | 200 |
| Tokens per call | `MAX_TOKENS_PER_CALL` | 2000 |
| Tokens per day | `MAX_TOKENS_PER_DAY` | 20000 |

`check_rate_limit` runs before a request is sent, `check_token_limit` before the
token spend is accepted, and `register_request` records the tokens used afterwards.
Both checks take `bypass_limits=True`, which the fallback chain passes on retries so
one cascade does not spend the budget twice. `get_user_stats(user_id)` reports the
current minute and day usage plus tokens remaining.

## GitHub Secrets Required

| Secret | Where to get it | Used for |
| --- | --- | --- |
| `GROQ_API_KEY` | https://console.groq.com/keys | Groq calls + daily model check |
| `OPENROUTER_API_KEY` | https://openrouter.ai/settings/keys | OpenRouter calls + daily model check |
| `GITHUB_TOKEN` | auto-provided by GitHub Actions | opening issues from workflows |

## Daily Model Check Workflows

### Groq

- **File:** [.github/workflows/groq-model-check.yml](../.github/workflows/groq-model-check.yml)
- Runs daily on a cron schedule (plus manual `workflow_dispatch`), sets
  `RUN_LIVE_LLM_TESTS=1` and runs `pytest tests/integration/test_groq.py -m live`,
  which hits the real Groq API for every entry in `AVAILABLE_MODELS`
- If any model fails it opens a GitHub issue titled "Daily Groq model check failed"
  listing the failed models and linking to
  https://console.groq.com/docs/rate-limits to check current free tier availability
- **To update available models:** edit `AVAILABLE_MODELS` in
  [src/llm/groq.py](../src/llm/groq.py) and the parametrized integration test picks
  up the change

### OpenRouter

- **File:** [.github/workflows/openrouter-model-check.yml](../.github/workflows/openrouter-model-check.yml)
- Runs daily, sets `RUN_LIVE_LLM_TESTS=1` and runs
  `pytest tests/integration/test_openrouter.py -m live` against every model in
  `AVAILABLE_MODELS`, retrying once after a 3 second sleep when pytest exits with
  code 1 so transient upstream 429s can settle
- If models still fail it opens "Daily OpenRouter model check failed" with the
  failed model ids and a link to https://openrouter.ai/models?q=:free
- Failures caused by a 403 open a second, separate issue titled
  "OpenRouter models to block" listing the ids to add to `BLOCKED_MODELS` in
  [src/llm/open_router.py](../src/llm/open_router.py)

## Adding a New LLM Provider

1. Create `src/llm/<provider>.py` inheriting from `BaseLLMClient`
2. Implement `generate(prompt, user_id, bypass_limits=False)` and `get_model_name()`
3. Add it to the cascade in `src/llm/fallback.py`
4. Add the API key to `.env`, `.env.example` and `src/config.py`
5. Add the key to GitHub secrets
6. Document it here
