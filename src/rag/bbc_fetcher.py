import math

import feedparser

from src.rag.embedder import embed_query, embed_texts

BBC_FEEDS = [
    "http://feeds.bbci.co.uk/news/business/rss.xml",
    "http://feeds.bbci.co.uk/news/technology/rss.xml",
]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def _fetch_feed(url: str) -> list[dict]:
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        articles.append(
            {
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "url": entry.get("link", ""),
                "published": entry.get("published", ""),
            }
        )
    return articles


def _fetch_all_articles() -> list[dict]:
    articles = []
    for feed_url in BBC_FEEDS:
        articles.extend(_fetch_feed(feed_url))
    return articles


def _rank_articles(topic: str, articles: list[dict], top_k: int = 3) -> list[dict]:
    topic_embedding = embed_query(topic)
    summaries = [f"{a['title']}. {a['summary']}" for a in articles]
    article_embeddings = embed_texts(summaries)
    scores = [_cosine(topic_embedding, emb) for emb in article_embeddings]
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
        :top_k
    ]
    return [articles[i] for i in top_indices]


def fetch_bbc_articles(topic: str, top_k: int = 3) -> list[dict]:
    articles = _fetch_all_articles()
    if not articles:
        return []
    return _rank_articles(topic, articles, top_k)
