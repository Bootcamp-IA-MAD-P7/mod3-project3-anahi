from unittest.mock import patch

import pytest

from src.chains.image_fallback import ImageFallbackUpdate
from src.graph.enums import Platform, Provider
from src.graph.nodes import image_node


def base_state(**overrides):
    defaults = {
        "topic": "AI trends",
        "platform": Platform.LINKEDIN,
        "audience": "professionals",
        "language": "en",
        "model": "openai/gpt-oss-120b",
        "provider": Provider.GROQ,
        "image_enabled": True,
        "rag_enabled": False,
        "citations_enabled": False,
        "user_context": "",
        "rag_context": "",
        "generated_text": "some generated text",
        "image_prompt": "a professional at a desk",
        "image_data": None,
        "status_messages": [],
    }
    return {**defaults, **overrides}


async def mock_fallback_success(*args, **kwargs):
    yield ImageFallbackUpdate(
        status="Image generated with flux-1-schnell", result=b"img", is_last=False
    )


async def mock_fallback_is_last(*args, **kwargs):
    yield ImageFallbackUpdate(
        status="Image generated with flux-1-schnell", result=b"img", is_last=True
    )


async def mock_fallback_failure(*args, **kwargs):
    yield ImageFallbackUpdate(
        status="Image generation failed — your post will be generated without an image",
        result=None,
        is_last=False,
    )


@pytest.mark.asyncio
class TestImageNode:
    async def test_stores_image_data_on_success(self):
        with patch(
            "src.graph.nodes.run_image_with_fallback", new=mock_fallback_success
        ):
            result = await image_node(base_state())
        assert result["image_data"] == b"img"

    async def test_appends_status_messages(self):
        with patch(
            "src.graph.nodes.run_image_with_fallback", new=mock_fallback_success
        ):
            result = await image_node(base_state())
        assert any("flux-1-schnell" in s for s in result["status_messages"])

    async def test_appends_daily_limit_warning_when_is_last(self):
        with patch(
            "src.graph.nodes.run_image_with_fallback", new=mock_fallback_is_last
        ):
            result = await image_node(base_state())
        assert "You've reached your daily image limit" in result["status_messages"]

    async def test_sets_none_when_no_result(self):
        with patch(
            "src.graph.nodes.run_image_with_fallback", new=mock_fallback_failure
        ):
            result = await image_node(base_state())
        assert result["image_data"] is None
