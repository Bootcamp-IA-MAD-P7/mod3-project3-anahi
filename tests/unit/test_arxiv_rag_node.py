from unittest.mock import Mock, patch

from src.graph.enums import Platform, Provider, Tone
from src.graph.nodes import arxiv_rag_node

MOCK_CHUNK = {
    "chunk_text": "Quantum entanglement enables faster computation.",
    "paper_id": "2401.00001",
    "paper_title": "Quantum Computing Advances",
    "authors": "Smith et al.",
    "arxiv_url": "https://arxiv.org/abs/2401.00001",
    "similarity": 0.95,
}

MOCK_PAPER = {
    "paper_id": "2401.00001",
    "title": "Quantum Computing Advances",
    "authors": "Smith et al.",
    "arxiv_url": "https://arxiv.org/abs/2401.00001",
    "pdf_url": "https://arxiv.org/pdf/2401.00001",
}

MOCK_EMBEDDING = [0.1] * 384


def base_state(**overrides):
    defaults = {
        "token": "test-jwt-token",
        "topic": "quantum computing",
        "platform": Platform.MEDIUM,
        "audience": "general public",
        "tone": Tone.PROFESSIONAL,
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


@patch("src.graph.nodes.retrieve_chunks", return_value=[MOCK_CHUNK])
@patch("src.graph.nodes.model")
@patch("src.graph.nodes.topic_is_cached", return_value=True)
@patch("src.graph.nodes.find_similar_slug", return_value=None)
@patch("src.graph.nodes.fetch_arxiv_papers")
def test_cache_hit_exact(
    mock_fetch, mock_similar, mock_cached, mock_model, mock_retrieve
):
    mock_model.encode.return_value = [MOCK_EMBEDDING]
    state = base_state()
    result = arxiv_rag_node(state)

    mock_similar.assert_called_once_with("quantum-computing")
    mock_cached.assert_called_once_with("quantum-computing")
    mock_fetch.assert_not_called()
    mock_retrieve.assert_called_once_with("quantum-computing", MOCK_EMBEDDING, 3)
    assert result["rag_context"] == [MOCK_CHUNK]
    assert result["rag_status"] is None


@patch("src.graph.nodes.retrieve_chunks", return_value=[MOCK_CHUNK])
@patch("src.graph.nodes.model")
@patch("src.graph.nodes.topic_is_cached")
@patch("src.graph.nodes.find_similar_slug", return_value="quantum-computers")
def test_cache_hit_fuzzy(mock_similar, mock_cached, mock_model, mock_retrieve):
    mock_model.encode.return_value = [MOCK_EMBEDDING]
    state = base_state()
    result = arxiv_rag_node(state)

    mock_similar.assert_called_once_with("quantum-computing")
    mock_cached.assert_not_called()
    mock_retrieve.assert_called_once_with("quantum-computers", MOCK_EMBEDDING, 3)
    assert result["rag_context"] == [MOCK_CHUNK]
    assert result["rag_status"] is None


@patch("src.graph.nodes.retrieve_chunks", return_value=[MOCK_CHUNK])
@patch("src.graph.nodes.store_chunks")
@patch(
    "src.graph.nodes.embed_chunks",
    return_value=[{**MOCK_CHUNK, "embedding": MOCK_EMBEDDING}],
)
@patch("src.graph.nodes.chunk_text", return_value=[MOCK_CHUNK])
@patch("src.graph.nodes.clean_text", return_value="cleaned text")
@patch("src.graph.nodes.parse_pdf", return_value="raw text")
@patch("src.graph.nodes.fetch_arxiv_papers", return_value=[MOCK_PAPER])
@patch("src.graph.nodes.model")
@patch("src.graph.nodes.topic_is_cached", return_value=False)
@patch("src.graph.nodes.find_similar_slug", return_value=None)
def test_cold_path(
    mock_similar,
    mock_cached,
    mock_model,
    mock_fetch,
    mock_parse,
    mock_clean,
    mock_chunk,
    mock_embed,
    mock_store,
    mock_retrieve,
):
    manager = Mock()
    manager.attach_mock(mock_fetch, "fetch")
    manager.attach_mock(mock_parse, "parse")
    manager.attach_mock(mock_clean, "clean")
    manager.attach_mock(mock_chunk, "chunk")
    manager.attach_mock(mock_embed, "embed")
    manager.attach_mock(mock_store, "store")
    manager.attach_mock(mock_retrieve, "retrieve")

    mock_model.encode.return_value = [MOCK_EMBEDDING]
    state = base_state()
    result = arxiv_rag_node(state)

    assert [call[0] for call in manager.mock_calls] == [
        "fetch",
        "parse",
        "clean",
        "chunk",
        "embed",
        "store",
        "retrieve",
    ]
    mock_fetch.assert_called_once_with("quantum computing")
    mock_parse.assert_called_once_with(MOCK_PAPER["pdf_url"])
    mock_clean.assert_called_once_with("raw text")
    mock_chunk.assert_called_once_with("cleaned text", "quantum-computing", MOCK_PAPER)
    mock_embed.assert_called_once_with([MOCK_CHUNK])
    mock_store.assert_called_once()
    mock_retrieve.assert_called_once_with("quantum-computing", MOCK_EMBEDDING, 3)
    assert result["rag_context"] == [MOCK_CHUNK]
    assert result["rag_status"] is None


@patch("src.graph.nodes.retrieve_chunks", return_value=[MOCK_CHUNK])
@patch("src.graph.nodes.model")
@patch("src.graph.nodes.topic_is_cached", return_value=False)
@patch("src.graph.nodes.find_similar_slug", return_value=None)
@patch("src.graph.nodes.fetch_arxiv_papers", side_effect=Exception("arXiv timeout"))
def test_failure_degrades_gracefully(
    mock_fetch, mock_similar, mock_cached, mock_model, mock_retrieve
):
    mock_model.encode.return_value = [MOCK_EMBEDDING]
    state = base_state()
    result = arxiv_rag_node(state)

    assert result["rag_context"] == []
    assert result["rag_status"] is not None
    assert "arXiv timeout" in result["rag_status"]
    assert "Exception" in result["rag_status"]
