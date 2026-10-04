# Conventions

## Tooling

- Dependency management and scripts use `uv`, never `pip`:
  - add packages: `uv add <package>`
  - run: `uv run <script>`
- Lint and format with ruff before committing:

  ```bash
  uv run ruff check --fix .
  uv run ruff format .
  ```

- Pre-commit runs the `ruff` hook (`pre-commit install` to enable it)

## Code Style

- Put imports at the top of the file, no lazy imports
- No docstrings unless strictly necessary, no inline comments unless they explain a
  non-obvious decision
- No hardcoded values: define constants once in the relevant module and import them
- No deprecated APIs
- Raise specific exceptions instead of generic ones, one responsibility per file
- User facing strings have no trailing dots and no dashes inside them

## Tests

- `tests/unit/` runs offline and must stay offline in the default `pytest` run
- `tests/integration/` hits the real Groq API and is opt in:

  ```bash
  RUN_LIVE_LLM_TESTS=1 pytest tests/integration/ -m live
  ```

- The `live` marker is registered in `pyproject.toml`

## Commits

Conventional Commits, subject under 72 characters, no trailing period:

```
feat: add Groq client with rate limiting
fix: remove redundant model validation from GroqClient
docs: document llm setup
```

Types: `feat`, `fix`, `chore`, `refactor`, `docs`, `style`, `test`, `perf`, `ci`,
`revert`.

## Secrets

- Keys live in `.env` (gitignored), only `.env.example` is committed
- GitHub Actions secrets are listed in [docs/llm-setup.md](docs/llm-setup.md)
