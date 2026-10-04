import os

import pytest

from src.llm.base import LLMResponse
from src.llm.open_router import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    OpenRouterClient,
    get_available_models,
)

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_LLM_TESTS") != "1",
        reason="live OpenRouter tests are opt-in; set RUN_LIVE_LLM_TESTS=1",
    ),
]


def test_get_available_models_returns_free_models() -> None:
    models = get_available_models()

    assert models
    assert all(":free" in model for model in models)
    assert DEFAULT_MODEL in models


@pytest.mark.parametrize("model", AVAILABLE_MODELS)
def test_generate_returns_llm_response(model: str) -> None:
    client = OpenRouterClient(model=model)

    result = client.generate(
        "Say hello in one sentence", user_id="test-user", bypass_limits=True
    )

    assert isinstance(result, LLMResponse)
    assert result.text.strip()
    assert result.model_name == model
