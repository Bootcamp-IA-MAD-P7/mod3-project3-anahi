import os
from difflib import SequenceMatcher

import psycopg2
from psycopg2.extras import execute_values


def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def topic_is_cached(slug: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT topic_is_cached(%s)", (slug,))
            return cur.fetchone()[0]


def find_similar_slug(slug: str, threshold: float = 0.8) -> str | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT topic_slug FROM rag_chunks")
            existing_slugs = [row[0] for row in cur.fetchall()]

    best_match = None
    best_ratio = 0.0
    for existing in existing_slugs:
        ratio = SequenceMatcher(None, slug, existing).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = existing

    if best_ratio >= threshold:
        return best_match
    return None


def store_chunks(chunks: list[dict]) -> None:
    rows = [
        (
            chunk["topic_slug"],
            chunk["chunk_text"],
            chunk["embedding"],
            chunk["paper_id"],
            chunk["paper_title"],
            chunk["authors"],
            chunk["arxiv_url"],
        )
        for chunk in chunks
    ]
    with get_connection() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO rag_chunks
                    (topic_slug, chunk_text, embedding, paper_id,
                     paper_title, authors, arxiv_url)
                VALUES %s
                """,
                rows,
            )
        conn.commit()


def retrieve_chunks(
    slug: str, query_embedding: list[float], top_k: int = 3
) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT chunk_text, paper_id, paper_title, authors, arxiv_url, "
                "similarity FROM search_chunks(%s, %s::vector, %s)",
                (slug, query_embedding, top_k),
            )
            rows = cur.fetchall()
    return [
        {
            "chunk_text": row[0],
            "paper_id": row[1],
            "paper_title": row[2],
            "authors": row[3],
            "arxiv_url": row[4],
            "similarity": row[5],
        }
        for row in rows
    ]


def get_user_context(user_id: str) -> str:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_context FROM user_profiles WHERE user_id = %s",
                (user_id,),
            )
            row = cur.fetchone()
    return row[0] if row and row[0] else ""


def upsert_user_context(user_id: str, user_context: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_profiles (user_id, user_context)
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET user_context = EXCLUDED.user_context
                """,
                (user_id, user_context),
            )
        conn.commit()
