import os

import pytest

from src.llm.groq import AVAILABLE_MODELS, GroqClient

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_LLM_TESTS") != "1",
        reason="live Groq tests are opt-in; set RUN_LIVE_LLM_TESTS=1",
    ),
]


@pytest.mark.parametrize("model", AVAILABLE_MODELS)
def test_generate_returns_text(model: str) -> None:
    client = GroqClient(model=model)

    response = client.generate("Say hello in one sentence", user_id="test-user")

    assert response.text.strip()
    assert response.tokens_used > 0
    assert response.model_name == model
