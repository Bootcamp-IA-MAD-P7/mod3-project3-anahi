import os

import pytest

from src.chains.cloudflare import generate_image
from src.chains.image_fallback import IMAGE_MODELS
from src.config import get_settings
from src.graph.enums import Platform

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_LLM_TESTS") != "1",
        reason="live image tests are opt-in; set RUN_LIVE_LLM_TESTS=1",
    ),
]


@pytest.fixture(autouse=True)
def require_cloudflare_keys():
    try:
        settings = get_settings()
    except RuntimeError as exc:
        pytest.skip(str(exc))
    if not settings.cloudflare_api_token or not settings.cloudflare_account_id:
        pytest.skip("CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID required")


@pytest.mark.asyncio
async def test_default_model_generates_image():
    result = await generate_image(
        prompt="illustration of a red bicycle leaning against a brick wall",
        platform=Platform.LINKEDIN,
        user_id="test-image-integration",
    )

    assert isinstance(result, tuple)
    assert isinstance(result[0], bytes)
    assert len(result[0]) > 0
    assert result[0][:2] in (b"\xff\xd8", b"\x89P")


@pytest.mark.asyncio
@pytest.mark.parametrize("model", IMAGE_MODELS)
async def test_generate_image_per_model(model: str):
    user_id = f"test-image-{model.replace('/', '-').replace('@', '')}"
    result, is_last = await generate_image(
        prompt="illustration of a professional working at a desk, warm lighting",
        platform=Platform.LINKEDIN,
        user_id=user_id,
        model=model,
    )
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result[:2] in (b"\xff\xd8", b"\x89P")
