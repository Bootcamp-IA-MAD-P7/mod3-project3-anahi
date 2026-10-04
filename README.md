# LLM LangGraph content generator

Content generation pipeline that writes posts for Instagram, LinkedIn, Medium and
Substack using LangGraph orchestration. See [docs/llm-setup.md](docs/llm-setup.md)
for LLM provider details.

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

## Architecture

The app is orchestrated with LangGraph (`src/graph/`), which routes prompt building
(`src/prompts/`) through LLM clients (`src/llm/`). Groq is the primary provider and
OpenRouter the secondary one, with `src/llm/fallback.py` cascading from the selected
Groq model through the remaining Groq models and then the free OpenRouter models,
yielding a status update per attempt. The frontend is planned as a Gradio UI, and
RAG over arXiv papers is planned as the grounding source. Provider details, secrets
and the daily model checks are documented in
[docs/llm-setup.md](docs/llm-setup.md).

## Running Tests

- **Default suite (offline):**

  ```bash
  pytest
  ```

- **Live LLM integration tests** (requires `GROQ_API_KEY` and `OPENROUTER_API_KEY`):

  ```bash
  RUN_LIVE_LLM_TESTS=1 pytest tests/integration/ -m live
  ```

## Contributing

Read [CONVENTIONS.md](CONVENTIONS.md) before opening a pull request.
