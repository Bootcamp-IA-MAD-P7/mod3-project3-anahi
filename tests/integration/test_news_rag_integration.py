import pytest

from src.rag.bbc_fetcher import fetch_bbc_articles


@pytest.mark.integration
def test_bbc_pipeline_real():
    articles = fetch_bbc_articles("artificial intelligence", top_k=3)

    assert 0 < len(articles) <= 3
    for article in articles:
        for key in ("title", "summary", "url", "published"):
            assert key in article
        assert article["title"]
        assert article["summary"]
        assert article["url"].startswith("https://")
