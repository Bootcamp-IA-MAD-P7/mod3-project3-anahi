from langchain_groq import ChatGroq

from src.config import get_settings
from src.llm.base import BaseLLMClient, LLMResponse
from src.llm.security import (
    MAX_TOKENS_PER_CALL,
    check_rate_limit,
    check_token_limit,
    register_request,
)

DEFAULT_MODEL = "openai/gpt-oss-120b"

AVAILABLE_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
]


class GroqClient(BaseLLMClient):
    def __init__(
        self, model: str = DEFAULT_MODEL, max_tokens: int = MAX_TOKENS_PER_CALL
    ):
        if model not in AVAILABLE_MODELS:
            raise ValueError(f"Model {model} is not available on the free tier")
        settings = get_settings()
        self._model = model
        self._max_tokens = max_tokens
        self._client = ChatGroq(
            api_key=settings.groq_api_key,
            model=model,
            max_tokens=max_tokens,
        )

    def get_model_name(self) -> str:
        return self._model

    def generate(self, prompt: str, user_id: str) -> LLMResponse:
        check_rate_limit(user_id)
        check_token_limit(user_id, self._max_tokens)

        try:
            response = self._client.invoke(prompt)
        except Exception as e:
            raise RuntimeError(f"Groq model {self._model} failed: {e}") from e

        usage = response.usage_metadata or {}
        tokens_used = usage.get("total_tokens", 0)
        register_request(user_id, tokens_used)
        return LLMResponse(
            text=response.content,
            tokens_used=tokens_used,
            model_name=self._model,
        )
