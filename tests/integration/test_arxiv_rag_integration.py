import pytest

from src.rag.arxiv_fetcher import fetch_arxiv_papers
from src.rag.chunker import chunk_text
from src.rag.cleaner import clean_text
from src.rag.embedder import embed_chunks
from src.rag.pdf_parser import parse_pdf


@pytest.mark.integration
@pytest.mark.slow
def test_arxiv_pipeline_real():
    papers = fetch_arxiv_papers("quantum computing", max_results=1)
    assert len(papers) >= 1
    for key in ("paper_id", "title", "authors", "arxiv_url", "pdf_url"):
        assert key in papers[0]

    text = parse_pdf(papers[0]["pdf_url"])
    assert isinstance(text, str)
    assert len(text) > 500

    cleaned = clean_text(text)
    assert isinstance(cleaned, str)
    assert cleaned

    chunks = chunk_text(cleaned, "quantum-computing", papers[0])
    assert len(chunks) >= 1
    assert all("chunk_text" in chunk for chunk in chunks)

    embedded = embed_chunks(chunks[:3])
    for chunk in embedded:
        assert "embedding" in chunk
        assert len(chunk["embedding"]) == 384
