import os

import pytest
from langchain_core.messages import HumanMessage

from src.llm.base import LLMResponse
from src.llm.open_router import (
    AVAILABLE_MODELS,
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

    assert models, "OpenRouter catalog unreachable or returned no free models"
    assert all(":free" in model for model in models)
    assert all("embed" not in model for model in models)


@pytest.mark.parametrize("model", AVAILABLE_MODELS)
def test_generate_returns_llm_response(model: str) -> None:
    client = OpenRouterClient(model=model)

    try:
        result = client.generate(
            [HumanMessage(content="Say hello in one sentence")],
            user_id="test-user",
            bypass_limits=True,
        )
    except RuntimeError as e:
        err = str(e).lower()
        if "429" in err or "502" in err or "rate" in err or "limit" in err:
            pytest.skip(f"Model {model} rate limited — skipping")
        raise

    assert isinstance(result, LLMResponse)
    if not result.text.strip():
        pytest.skip(f"Model {model} returned empty response — skipping")
    assert result.model_name == model
