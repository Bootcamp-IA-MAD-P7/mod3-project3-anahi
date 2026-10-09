import pytest
from langgraph.graph import END

from src.graph.builder import (
    _route_after_llm,
    _route_after_platform,
    _route_after_router,
)
from src.graph.enums import Platform, Provider, Tone


def base_state(**overrides):
    defaults = {
        "token": "test-jwt-token",
        "topic": "AI",
        "platform": Platform.LINKEDIN,
        "audience": "professionals",
        "tone": Tone.PROFESSIONAL,
        "language": "en",
        "model": "openai/gpt-oss-120b",
        "provider": Provider.GROQ,
        "image_enabled": False,
        "citations_enabled": False,
        "user_context": "",
        "rag_context": [],
        "generated_text": "",
        "image_data": None,
        "status_messages": [],
    }
    return {**defaults, **overrides}


class TestRouteAfterRouter:
    @pytest.mark.parametrize(
        "platform,expected",
        [
            (Platform.MEDIUM, "arxiv_rag_node"),
            (Platform.SUBSTACK, "arxiv_rag_node"),
            (Platform.LINKEDIN, "news_rag_node"),
            (Platform.INSTAGRAM, "llm_node"),
        ],
    )
    def test_routes_to_correct_rag_node(self, platform, expected):
        assert _route_after_router(base_state(platform=platform)) == expected


class TestRouteAfterLlm:
    @pytest.mark.parametrize(
        "platform,expected",
        [
            (Platform.LINKEDIN, "linkedin_node"),
            (Platform.INSTAGRAM, "instagram_node"),
            (Platform.MEDIUM, "medium_node"),
            (Platform.SUBSTACK, "substack_node"),
        ],
    )
    def test_routes_to_correct_platform_node(self, platform, expected):
        assert _route_after_llm(base_state(platform=platform)) == expected


class TestRouteAfterPlatform:
    def test_routes_to_image_node_when_enabled(self):
        assert _route_after_platform(base_state(image_enabled=True)) == "image_node"

    def test_routes_to_end_when_image_disabled(self):
        assert _route_after_platform(base_state(image_enabled=False)) == END
