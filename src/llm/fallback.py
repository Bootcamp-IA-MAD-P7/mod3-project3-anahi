from dataclasses import dataclass
from typing import Generator

from langchain_core.messages import BaseMessage

from src.llm.base import BaseLLMClient, LLMResponse
from src.llm.groq import AVAILABLE_MODELS as GROQ_MODELS
from src.llm.groq import GroqClient
from src.llm.open_router import (
    AVAILABLE_MODELS as OPENROUTER_MODELS,
)
from src.llm.open_router import (
    DEFAULT_MODEL as OPENROUTER_DEFAULT,
)
from src.llm.open_router import (
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


def _build_openrouter_cascade(selected_model: str | None = None) -> list[str]:
    available = [m for m in OPENROUTER_MODELS if m]
    if not available:
        return []
    if selected_model and selected_model in available:
        idx = available.index(selected_model)
        return available[idx:] + available[:idx]
    if OPENROUTER_DEFAULT in available:
        rest = [m for m in available if m != OPENROUTER_DEFAULT]
        return [OPENROUTER_DEFAULT] + rest
    return available


def run_with_fallback(
    selected_model: str,
    prompt: list[BaseMessage],
    user_id: str,
    provider: str = "groq",
) -> Generator[FallbackUpdate, None, None]:
    if provider == "openrouter":
        primary_cascade = _build_openrouter_cascade(selected_model)
        primary_client = OpenRouterClient
        secondary_cascade = GROQ_MODELS
        secondary_client = GroqClient
    else:
        primary_cascade = _build_groq_cascade(selected_model)
        primary_client = GroqClient
        secondary_cascade = _build_openrouter_cascade()
        secondary_client = OpenRouterClient

    bypass_limits = False

    for model in primary_cascade:
        try:
            client: BaseLLMClient = primary_client(model=model)
            result = client.generate(prompt, user_id, bypass_limits)
            yield FallbackUpdate(status=f"Generated with {model}", result=result)
            return
        except Exception:
            bypass_limits = True
            next_model = _get_next(primary_cascade, secondary_cascade, model)
            yield FallbackUpdate(
                status=f"Model {model} unavailable, trying {next_model}..."
            )

    for model in secondary_cascade:
        try:
            client = secondary_client(model=model)
            result = client.generate(prompt, user_id, bypass_limits)
            yield FallbackUpdate(status=f"Generated with {model}", result=result)
            return
        except Exception:
            bypass_limits = True
            next_model = _get_next([], secondary_cascade, model)
            yield FallbackUpdate(
                status=f"Model {model} unavailable, trying {next_model}..."
            )

    yield FallbackUpdate(status="All models unavailable, please try again later")


def _get_next(
    primary_cascade: list[str], secondary_cascade: list[str], current: str
) -> str:
    combined = primary_cascade + secondary_cascade
    if current in combined:
        idx = combined.index(current)
        if idx + 1 < len(combined):
            return combined[idx + 1]
    return "no models left"
