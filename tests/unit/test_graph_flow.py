from unittest.mock import patch

import pytest

from src.graph.builder import build_graph
from src.graph.enums import Platform, Provider


def base_input(**overrides):
    defaults = {
        "topic": "quantum computing",
        "platform": Platform.LINKEDIN,
        "audience": "tech professionals",
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


def mock_llm_node(state):
    return {
        "generated_text": "mocked content",
        "status_messages": ["llm ok"],
        "model": state["model"],
    }


def mock_platform_node(state):
    return {"generated_text": state["generated_text"] + " [formatted]"}


def mock_image_node(state):
    return {"image_data": b"fake-image-bytes"}


def mock_rag_node(state):
    return {"rag_context": "mocked rag context"}


@pytest.fixture
def graph_with_mocks():
    with (
        patch("src.graph.builder.llm_node", mock_llm_node),
        patch("src.graph.builder.linkedin_node", mock_platform_node),
        patch("src.graph.builder.instagram_node", mock_platform_node),
        patch("src.graph.builder.medium_node", mock_platform_node),
        patch("src.graph.builder.substack_node", mock_platform_node),
        patch("src.graph.builder.image_node", mock_image_node),
        patch("src.graph.builder.rag_node", mock_rag_node),
    ):
        yield build_graph()


class TestGraphFlow:
    def test_linkedin_no_rag_no_image(self, graph_with_mocks):
        result = graph_with_mocks.invoke(
            base_input(
                platform=Platform.LINKEDIN,
                rag_enabled=False,
                image_enabled=False,
            )
        )
        assert result["generated_text"] != ""
        assert result["image_data"] is None

    def test_medium_with_rag_no_image(self, graph_with_mocks):
        result = graph_with_mocks.invoke(
            base_input(
                platform=Platform.MEDIUM,
                rag_enabled=True,
                image_enabled=False,
            )
        )
        assert result["generated_text"] != ""
        assert result["rag_context"] == "mocked rag context"

    def test_instagram_forces_image(self, graph_with_mocks):
        result = graph_with_mocks.invoke(
            base_input(
                platform=Platform.INSTAGRAM,
                image_enabled=False,
            )
        )
        assert result["image_data"] == b"fake-image-bytes"

    def test_linkedin_with_image_enabled(self, graph_with_mocks):
        result = graph_with_mocks.invoke(
            base_input(
                platform=Platform.LINKEDIN,
                image_enabled=True,
            )
        )
        assert result["image_data"] == b"fake-image-bytes"

    def test_substack_with_rag(self, graph_with_mocks):
        result = graph_with_mocks.invoke(
            base_input(
                platform=Platform.SUBSTACK,
                rag_enabled=True,
                image_enabled=False,
            )
        )
        assert result["generated_text"] != ""
