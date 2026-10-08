import os

import psycopg2
from psycopg2.extras import execute_values


def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def topic_is_cached(slug: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT topic_is_cached(%s)", (slug,))
            return cur.fetchone()[0]


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
                "similarity FROM search_chunks(%s, %s, %s)",
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
