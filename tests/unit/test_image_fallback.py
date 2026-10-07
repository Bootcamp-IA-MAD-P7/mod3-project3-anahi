from unittest.mock import AsyncMock, patch

import pytest

from src.chains.cloudflare import ImageGenerationError, ImageRateLimitError
from src.chains.image_fallback import (
    IMAGE_MODELS,
    run_image_with_fallback,
)
from src.graph.enums import Platform


async def collect(gen):
    updates = []
    async for update in gen:
        updates.append(update)
    return updates


@pytest.mark.asyncio
class TestRunImageWithFallback:
    async def test_succeeds_on_first_model(self):
        with patch(
            "src.chains.image_fallback.generate_image",
            new=AsyncMock(return_value=(b"image", False)),
        ):
            updates = await collect(
                run_image_with_fallback("prompt", Platform.LINKEDIN, "user")
            )
        assert updates[-1].result == b"image"
        assert IMAGE_MODELS[0] in updates[-1].status

    async def test_falls_back_on_image_generation_error(self):
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ImageGenerationError("fail")
            return b"image", False

        with patch("src.chains.image_fallback.generate_image", new=mock_generate):
            updates = await collect(
                run_image_with_fallback("prompt", Platform.LINKEDIN, "user")
            )

        statuses = [u.status for u in updates]
        assert any("unavailable, trying" in s for s in statuses)
        assert updates[-1].result == b"image"

    async def test_stops_on_rate_limit_error(self):
        with patch(
            "src.chains.image_fallback.generate_image",
            new=AsyncMock(side_effect=ImageRateLimitError("quota")),
        ):
            updates = await collect(
                run_image_with_fallback("prompt", Platform.LINKEDIN, "user")
            )
        assert len(updates) == 1
        assert updates[0].result is None
        assert (
            "quota" in updates[0].status.lower()
            or "exhausted" in updates[0].status.lower()
        )

    async def test_all_models_fail(self):
        with patch(
            "src.chains.image_fallback.generate_image",
            new=AsyncMock(side_effect=ImageGenerationError("fail")),
        ):
            updates = await collect(
                run_image_with_fallback("prompt", Platform.LINKEDIN, "user")
            )
        assert updates[-1].result is None
        assert "without an image" in updates[-1].status

    async def test_is_last_true(self):
        with patch(
            "src.chains.image_fallback.generate_image",
            new=AsyncMock(return_value=(b"image", True)),
        ):
            updates = await collect(
                run_image_with_fallback("prompt", Platform.LINKEDIN, "user")
            )
        assert updates[-1].is_last is True
