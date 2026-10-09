from src.graph.enums import Platform, Provider
from src.graph.nodes import router_node


def base_state(**overrides):
    defaults = {
        "topic": "AI",
        "platform": Platform.LINKEDIN,
        "audience": "professionals",
        "language": "en",
        "model": "openai/gpt-oss-120b",
        "provider": Provider.GROQ,
        "image_enabled": False,
        "citations_enabled": None,
        "user_context": "",
        "rag_context": [],
        "generated_text": "",
        "image_data": None,
        "status_messages": [],
    }
    return {**defaults, **overrides}


class TestCitationsDefaults:
    def test_citations_forced_false_for_linkedin(self):
        result = router_node(
            base_state(platform=Platform.LINKEDIN, citations_enabled=True)
        )
        assert result["citations_enabled"] is False

    def test_citations_forced_false_for_instagram(self):
        result = router_node(
            base_state(platform=Platform.INSTAGRAM, citations_enabled=True)
        )
        assert result["citations_enabled"] is False

    def test_citations_allowed_for_medium(self):
        result = router_node(
            base_state(platform=Platform.MEDIUM, citations_enabled=True)
        )
        assert result["citations_enabled"] is True

    def test_citations_allowed_for_substack(self):
        result = router_node(
            base_state(platform=Platform.SUBSTACK, citations_enabled=True)
        )
        assert result["citations_enabled"] is True

    def test_citations_defaults_false_when_none(self):
        result = router_node(
            base_state(platform=Platform.MEDIUM, citations_enabled=None)
        )
        assert result["citations_enabled"] is False


class TestImageDefaults:
    def test_image_forced_true_for_instagram(self):
        result = router_node(
            base_state(platform=Platform.INSTAGRAM, image_enabled=False)
        )
        assert result["image_enabled"] is True

    def test_image_not_forced_for_linkedin(self):
        result = router_node(
            base_state(platform=Platform.LINKEDIN, image_enabled=False)
        )
        assert result["image_enabled"] is False

    def test_image_explicit_true_on_linkedin_preserved(self):
        result = router_node(base_state(platform=Platform.LINKEDIN, image_enabled=True))
        assert result["image_enabled"] is True
