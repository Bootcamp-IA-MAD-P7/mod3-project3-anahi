from dataclasses import dataclass
from typing import Generator

from src.llm.base import BaseLLMClient, LLMResponse
from src.llm.groq import AVAILABLE_MODELS as GROQ_MODELS
from src.llm.groq import GroqClient
from src.llm.openrouter import (
    AVAILABLE_MODELS as OPENROUTER_MODELS,
)
from src.llm.openrouter import (
    DEFAULT_MODEL as OPENROUTER_DEFAULT,
)
from src.llm.openrouter import (
    OpenRouterClient,
)


@dataclass
class FallbackUpdate:
    status: str
    result: LLMResponse | None = None


def _build_groq_cascade(selected_model: str) -> list[str]:
    if selected_model not in GROQ_MODELS:
        return GROQ_MODELS
    idx = GROQ_MODELS.index(selected_model)
    return GROQ_MODELS[idx:] + GROQ_MODELS[:idx]


def _build_openrouter_cascade() -> list[str]:
    available = [m for m in OPENROUTER_MODELS if m]
    if not available:
        return []
    if OPENROUTER_DEFAULT in available:
        rest = [m for m in available if m != OPENROUTER_DEFAULT]
        return [OPENROUTER_DEFAULT] + rest
    return available


def run_with_fallback(
    selected_model: str,
    prompt: str,
    user_id: str,
) -> Generator[FallbackUpdate, None, None]:
    groq_cascade = _build_groq_cascade(selected_model)
    openrouter_cascade = _build_openrouter_cascade()

    for model in groq_cascade:
        try:
            client: BaseLLMClient = GroqClient(model=model)
            result = client.generate(prompt, user_id)
            yield FallbackUpdate(status=f"Generated with {model}", result=result)
            return
        except Exception:
            next_model = _get_next(groq_cascade, openrouter_cascade, model)
            yield FallbackUpdate(
                status=f"Model {model} unavailable, trying {next_model}..."
            )

    for model in openrouter_cascade:
        try:
            client = OpenRouterClient(model=model)
            result = client.generate(prompt, user_id)
            yield FallbackUpdate(status=f"Generated with {model}", result=result)
            return
        except Exception:
            next_model = _get_next([], openrouter_cascade, model)
            yield FallbackUpdate(
                status=f"Model {model} unavailable, trying {next_model}..."
            )

    yield FallbackUpdate(status="All models unavailable, please try again later")


def _get_next(
    groq_cascade: list[str], openrouter_cascade: list[str], current: str
) -> str:
    combined = groq_cascade + openrouter_cascade
    if current in combined:
        idx = combined.index(current)
        if idx + 1 < len(combined):
            return combined[idx + 1]
    return "no models left"
