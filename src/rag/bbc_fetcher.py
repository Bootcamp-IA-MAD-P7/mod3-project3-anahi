import feedparser
from sentence_transformers import util

from src.rag.embedder import model

BBC_FEEDS = [
    "http://feeds.bbci.co.uk/news/business/rss.xml",
    "http://feeds.bbci.co.uk/news/technology/rss.xml",
]


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
    topic_embedding = model.encode(topic, convert_to_tensor=True)
    summaries = [f"{a['title']}. {a['summary']}" for a in articles]
    article_embeddings = model.encode(summaries, convert_to_tensor=True)
    scores = util.cos_sim(topic_embedding, article_embeddings)[0]
    top_indices = scores.argsort(descending=True)[:top_k]
    return [articles[i] for i in top_indices]


def fetch_bbc_articles(topic: str, top_k: int = 3) -> list[dict]:
    articles = _fetch_all_articles()
    if not articles:
        return []
    return _rank_articles(topic, articles, top_k)
