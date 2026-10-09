from unittest.mock import patch

import pytest

from src.graph.enums import Platform, Provider
from src.graph.nodes import arxiv_rag_node

pytestmark = pytest.mark.integration

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


@patch("src.graph.nodes.retrieve_chunks", return_value=[MOCK_CHUNK])
@patch("src.graph.nodes.store_chunks")
@patch(
    "src.graph.nodes.embed_chunks",
    return_value=[{**MOCK_CHUNK, "embedding": [0.1] * 384}],
)
@patch("src.graph.nodes.chunk_text", return_value=[MOCK_CHUNK])
@patch("src.graph.nodes.clean_text", return_value="cleaned text")
@patch("src.graph.nodes.parse_pdf", return_value="raw text")
@patch("src.graph.nodes.fetch_arxiv_papers", return_value=[MOCK_PAPER])
@patch("src.graph.nodes.topic_is_cached", return_value=False)
@patch("src.graph.nodes.find_similar_slug", return_value=None)
def test_full_cold_path_call_order(
    mock_similar,
    mock_cached,
    mock_fetch,
    mock_parse,
    mock_clean,
    mock_chunk,
    mock_embed,
    mock_store,
    mock_retrieve,
):
    state = {
        "topic": "quantum computing",
        "platform": Platform.MEDIUM,
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

    result = arxiv_rag_node(state)

    mock_similar.assert_called_once_with("quantum-computing")
    mock_cached.assert_called_once_with("quantum-computing")

    mock_fetch.assert_called_once_with("quantum computing")
    mock_parse.assert_called_once_with(MOCK_PAPER["pdf_url"])
    mock_clean.assert_called_once_with("raw text")
    mock_chunk.assert_called_once_with("cleaned text", "quantum-computing", MOCK_PAPER)
    mock_embed.assert_called_once_with([MOCK_CHUNK])
    mock_store.assert_called_once()

    mock_retrieve.assert_called_once()
    slug_arg, embedding_arg, topk_arg = mock_retrieve.call_args.args
    assert slug_arg == "quantum-computing"
    assert len(embedding_arg) == 384
    assert topk_arg == 3

    assert result["rag_context"] == [MOCK_CHUNK]
    assert result["rag_status"] is None
    assert result["topic"] == "quantum computing"
