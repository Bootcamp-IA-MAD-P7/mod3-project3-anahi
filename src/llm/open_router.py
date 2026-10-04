import requests
from langchain_openai import ChatOpenAI

from src.config import get_settings
from src.llm.base import BaseLLMClient, LLMResponse
from src.llm.security import (
    MAX_TOKENS_PER_CALL,
    check_rate_limit,
    check_token_limit,
    register_request,
)

DEFAULT_MODEL = "inclusionai/ling-3.0-flash-sante:free"

BLOCKED_MODELS = {
    "thinkingmachines/inkling:free",
    "thinkingmachines/inkling-small:free",
}


def get_available_models() -> list[str]:
    try:
        settings = get_settings()
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
            timeout=10,
        )
        if not response.ok:
            return [DEFAULT_MODEL]
        data = response.json()
        models = [
            m["id"]
            for m in data["data"]
            if ":free" in m["id"] and m["id"] not in BLOCKED_MODELS
        ]
        return models if models else [DEFAULT_MODEL]
    except Exception:
        return [DEFAULT_MODEL]


AVAILABLE_MODELS = get_available_models()


class OpenRouterClient(BaseLLMClient):
    def __init__(
        self, model: str = DEFAULT_MODEL, max_tokens: int = MAX_TOKENS_PER_CALL
    ):
        settings = get_settings()
        self._model = model
        self._max_tokens = max_tokens
        self._client = ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            model=model,
            max_tokens=max_tokens,
        )

    def get_model_name(self) -> str:
        return self._model

    def generate(
        self, prompt: str, user_id: str, bypass_limits: bool = False
    ) -> LLMResponse:
        check_rate_limit(user_id, bypass_limits)
        check_token_limit(user_id, self._max_tokens, bypass_limits)

        try:
            response = self._client.invoke(prompt)
            usage = response.usage_metadata or {}
            tokens_used = usage.get("total_tokens", 0)
            register_request(user_id, tokens_used)
            return LLMResponse(
                text=response.content,
                tokens_used=tokens_used,
                model_name=self._model,
            )
        except Exception as e:
            raise RuntimeError(f"OpenRouter model {self._model} failed: {e}") from e
