import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.enums import Platform, Provider
from src.prompts.base import build_prompt
from src.prompts.instagram import build_instagram_prompt
from src.prompts.linkedin import build_linkedin_prompt
from src.prompts.medium import build_medium_prompt
from src.prompts.substack import build_substack_prompt

BUILDERS = {
    Platform.LINKEDIN: build_linkedin_prompt,
    Platform.INSTAGRAM: build_instagram_prompt,
    Platform.MEDIUM: build_medium_prompt,
    Platform.SUBSTACK: build_substack_prompt,
}

PLATFORM_MARKERS = {
    Platform.LINKEDIN: ["HOOK", "BODY", "CALL TO ACTION"],
    Platform.INSTAGRAM: ["Contradiction & Contrast", "Specificity Effect", "POV"],
    Platform.MEDIUM: ["HEADLINE", "STRUCTURE", "FORMATTING"],
    Platform.SUBSTACK: ["TITLE & SUBTITLE", "OPENING", "TONE"],
}

PLATFORMS = list(Platform)


def base_state(**overrides):
    defaults = {
        "topic": "AI",
        "platform": Platform.LINKEDIN,
        "audience": "professionals",
        "language": "en",
        "model": "openai/gpt-oss-120b",
        "provider": Provider.GROQ,
        "image_enabled": False,
        "rag_enabled": False,
        "citations_enabled": False,
        "user_context": "",
        "rag_context": "",
        "generated_text": "",
        "image_data": None,
        "status_messages": [],
    }
    return {**defaults, **overrides}


class TestPromptShape:
    @pytest.mark.parametrize("platform", PLATFORMS)
    def test_returns_system_then_human(self, platform):
        messages = BUILDERS[platform](base_state(platform=platform))
        assert len(messages) == 2
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[1], HumanMessage)


class TestHumanMessage:
    @pytest.mark.parametrize("platform", PLATFORMS)
    def test_includes_topic_audience_and_language(self, platform):
        state = base_state(
            platform=platform,
            topic="quantum computing",
            audience="tech professionals",
            language="es",
        )
        human = BUILDERS[platform](state)[1].content
        assert "Topic: quantum computing" in human
        assert "Target audience: tech professionals" in human
        assert "Generate the content in es" in human

    @pytest.mark.parametrize("platform", PLATFORMS)
    def test_includes_user_context_when_set(self, platform):
        state = base_state(platform=platform, user_context="writes as a CTO")
        human = BUILDERS[platform](state)[1].content
        assert "writes as a CTO" in human

    @pytest.mark.parametrize("platform", PLATFORMS)
    def test_omits_user_context_when_empty(self, platform):
        human = BUILDERS[platform](base_state(platform=platform))[1].content
        assert "Context about the author" not in human


class TestSystemStructure:
    @pytest.mark.parametrize("platform,markers", PLATFORM_MARKERS.items())
    def test_contains_platform_markers(self, platform, markers):
        system = BUILDERS[platform](base_state(platform=platform))[0].content
        for marker in markers:
            assert marker in system


class TestRagBlock:
    @pytest.mark.parametrize(
        "platform",
        [Platform.LINKEDIN, Platform.MEDIUM, Platform.SUBSTACK],
    )
    def test_includes_research_block_when_enabled(self, platform):
        state = base_state(
            platform=platform,
            rag_enabled=True,
            rag_context="source one says X",
        )
        human = BUILDERS[platform](state)[1].content
        assert "reference material" in human
        assert "source one says X" in human

    @pytest.mark.parametrize(
        "platform",
        [Platform.LINKEDIN, Platform.MEDIUM, Platform.SUBSTACK],
    )
    def test_omits_research_block_when_disabled(self, platform):
        human = BUILDERS[platform](base_state(platform=platform))[1].content
        assert "reference material" not in human

    def test_instagram_ignores_rag(self):
        state = base_state(
            platform=Platform.INSTAGRAM,
            rag_enabled=True,
            rag_context="source one says X",
        )
        human = build_instagram_prompt(state)[1].content
        assert "reference material" not in human
        assert "source one says X" not in human


class TestCitationsBlock:
    @pytest.mark.parametrize(
        "platform",
        [Platform.MEDIUM, Platform.SUBSTACK],
    )
    def test_includes_references_when_enabled(self, platform):
        state = base_state(platform=platform, citations_enabled=True)
        human = BUILDERS[platform](state)[1].content
        assert "References section" in human
        assert "APA" in human

    @pytest.mark.parametrize(
        "platform",
        [Platform.MEDIUM, Platform.SUBSTACK],
    )
    def test_omits_references_when_disabled(self, platform):
        human = BUILDERS[platform](base_state(platform=platform))[1].content
        assert "References section" not in human


class TestImageBlock:
    @pytest.mark.parametrize(
        "platform",
        [Platform.MEDIUM, Platform.SUBSTACK],
    )
    def test_includes_header_image_when_enabled(self, platform):
        state = base_state(platform=platform, image_enabled=True)
        human = BUILDERS[platform](state)[1].content
        assert "[HEADER IMAGE:" in human

    @pytest.mark.parametrize(
        "platform",
        [Platform.MEDIUM, Platform.SUBSTACK],
    )
    def test_omits_header_image_when_disabled(self, platform):
        human = BUILDERS[platform](base_state(platform=platform))[1].content
        assert "[HEADER IMAGE:" not in human


class TestBuildPromptDispatch:
    @pytest.mark.parametrize("platform", PLATFORMS)
    def test_routes_to_platform_builder(self, platform):
        state = base_state(platform=platform)
        messages = build_prompt(state)
        assert messages[0].content == BUILDERS[platform](state)[0].content

    def test_raises_for_unknown_platform(self):
        with pytest.raises(ValueError, match="No prompt builder for platform"):
            build_prompt(base_state(platform="pinterest"))
