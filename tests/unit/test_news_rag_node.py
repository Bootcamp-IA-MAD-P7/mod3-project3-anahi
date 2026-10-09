from unittest.mock import patch

from src.graph.enums import Platform, Provider
from src.graph.nodes import news_rag_node

MOCK_ARTICLE = {
    "title": "AI reshapes the workplace",
    "summary": "Companies are adopting AI tools at record pace.",
    "url": "https://www.bbc.co.uk/news/technology/123",
    "published": "Thu, 08 Oct 2026 10:00:00 GMT",
}


def base_state(**overrides):
    defaults = {
        "token": "test-jwt-token",
        "topic": "quantum computing",
        "platform": Platform.LINKEDIN,
        "audience": "general public",
        "language": "en",
        "model": "openai/gpt-oss-120b",
        "provider": Provider.GROQ,
        "image_enabled": False,
        "citations_enabled": True,
        "user_context": "",
        "rag_context": [],
        "generated_text": "",
        "image_data": None,
        "image_prompt": "",
        "status_messages": [],
    }
    return {**defaults, **overrides}


@patch("src.graph.nodes.fetch_bbc_articles")
def test_articles_found(mock_fetch):
    articles = [{**MOCK_ARTICLE, "title": f"Article {i}"} for i in range(3)]
    mock_fetch.return_value = articles
    state = base_state()
    result = news_rag_node(state)

    mock_fetch.assert_called_once_with("quantum computing", top_k=3)
    assert len(result["rag_context"]) == 3
    assert all(c["authors"] == "BBC News" for c in result["rag_context"])
    assert [c["paper_title"] for c in result["rag_context"]] == [
        a["title"] for a in articles
    ]
    assert result["rag_status"] is None


@patch("src.graph.nodes.fetch_bbc_articles", return_value=[])
def test_no_articles_found(mock_fetch):
    state = base_state()
    result = news_rag_node(state)

    mock_fetch.assert_called_once_with("quantum computing", top_k=3)
    assert result["rag_context"] == []
    assert result["rag_status"] is not None
    assert "No relevant BBC articles found" in result["rag_status"]


@patch("src.graph.nodes.fetch_bbc_articles", side_effect=Exception("feed timeout"))
def test_failure_degrades_gracefully(mock_fetch):
    state = base_state()
    result = news_rag_node(state)

    assert result["rag_context"] == []
    assert result["rag_status"] is not None
    assert "feed timeout" in result["rag_status"]
    assert "Exception" in result["rag_status"]


@patch("src.graph.nodes.fetch_bbc_articles", return_value=[MOCK_ARTICLE])
def test_state_passthrough(mock_fetch):
    state = base_state()
    result = news_rag_node(state)

    for key in state:
        assert key in result
    for key, value in state.items():
        if key not in ("rag_context", "rag_status"):
            assert result[key] == value
    assert len(result["rag_context"]) == 1
    assert result["rag_context"][0]["paper_title"] == MOCK_ARTICLE["title"]
    assert result["rag_context"][0]["arxiv_url"] == MOCK_ARTICLE["url"]
    assert result["rag_status"] is None
