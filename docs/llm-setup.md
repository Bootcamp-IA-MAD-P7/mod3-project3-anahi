# LLM Setup

How providers, secrets and the daily model check fit together.

## LLM Providers

### Groq (primary)

Live today through `src/llm/groq.py`. `DEFAULT_MODEL` is `openai/gpt-oss-120b` and
`AVAILABLE_MODELS` currently holds:

- `openai/gpt-oss-120b` (default)
- `openai/gpt-oss-20b`
- `qwen/qwen3.8-27b`

Free tier limits for these models are documented at
https://console.groq.com/docs/rate-limits

### Gemini Flash (secondary, coming soon)

`src/llm/gemini.py` is an empty stub. Once implemented it becomes the secondary
provider behind `GEMINI_API_KEY`.

### Fallback chain (planned)

`src/llm/fallback.py` is empty, so nothing cascades yet. The intended order when a
call fails is:

1. the selected Groq model (default `openai/gpt-oss-120b`)
2. `openai/gpt-oss-20b`
3. `qwen/qwen3.8-27b`
4. Gemini Flash

## GitHub Secrets Required

| Secret | Where to get it | Used for |
| --- | --- | --- |
| `GROQ_API_KEY` | https://console.groq.com/keys | LLM calls + daily model check |
| `GITHUB_TOKEN` | auto-provided by GitHub Actions | opening issues from workflow |

## Daily Model Check Workflow

- **File:** [.github/workflows/groq-model-check.yml](../.github/workflows/groq-model-check.yml)
- Runs daily on a cron schedule (plus manual `workflow_dispatch`), sets
  `RUN_LIVE_LLM_TESTS=1` and runs `pytest tests/integration/ -m live`, which hits
  the real Groq API for every entry in `AVAILABLE_MODELS`
- If any model fails, it automatically opens a GitHub issue titled
  "Daily Groq model check failed" listing the failed models and linking to
  https://console.groq.com/docs/rate-limits to check current free tier availability
- **To update available models:** edit `AVAILABLE_MODELS` in
  [src/llm/groq.py](../src/llm/groq.py) and the same list is picked up by the
  parametrized integration test

## Adding a New LLM Provider

1. Create `src/llm/<provider>.py` inheriting from `BaseLLMClient`
2. Implement `generate(prompt, user_id)` and `get_model_name()`
3. Add it to the fallback chain in `src/llm/fallback.py`
4. Add the API key to `.env` and to `src/config.py`
5. Add the key to GitHub secrets
6. Document it here
