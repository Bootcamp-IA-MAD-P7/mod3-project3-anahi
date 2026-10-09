import os
import time

import psycopg2
import pytest

from src.rag.embedder import model
from src.rag.store import (
    find_similar_slug,
    retrieve_chunks,
    store_chunks,
    topic_is_cached,
)

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set",
)

TEST_SLUG = "test-integration-quantum"
TEST_TYPO_SLUG = "test-integration-quantom"
TEST_USER_ID = "test-user-integration"
TEST_USER_CONTEXT = "Test company context"
UPDATED_USER_CONTEXT = "Updated company context"
TEXTS = ["test chunk one", "test chunk two"]
RESULT_KEYS = {
    "chunk_text",
    "paper_id",
    "paper_title",
    "authors",
    "arxiv_url",
    "similarity",
}
SEARCH_COLUMNS = [
    "chunk_text",
    "paper_id",
    "paper_title",
    "authors",
    "arxiv_url",
    "similarity",
]


@pytest.fixture
def conn():
    connection = psycopg2.connect(os.environ["DATABASE_URL"])
    yield connection
    try:
        connection.rollback()
        with connection.cursor() as cur:
            cur.execute("DELETE FROM rag_chunks WHERE topic_slug = %s", (TEST_SLUG,))
            cur.execute("DELETE FROM user_profiles WHERE user_id = %s", (TEST_USER_ID,))
        connection.commit()
    finally:
        connection.close()


def make_chunks():
    embeddings = model.encode(TEXTS, show_progress_bar=False)
    return [
        {
            "topic_slug": TEST_SLUG,
            "chunk_text": text,
            "embedding": embedding.tolist(),
            "paper_id": f"2401.0000{i}",
            "paper_title": f"Test Paper {i}",
            "authors": "Test Author",
            "arxiv_url": f"https://arxiv.org/abs/2401.0000{i}",
        }
        for i, (text, embedding) in enumerate(zip(TEXTS, embeddings), start=1)
    ]


def query_embedding():
    return model.encode([TEXTS[0]], show_progress_bar=False)[0].tolist()


@pytest.mark.integration
def test_topic_not_cached_on_empty(conn):
    assert topic_is_cached(TEST_SLUG) is False


@pytest.mark.integration
def test_store_and_retrieve_chunks(conn):
    store_chunks(make_chunks())

    assert topic_is_cached(TEST_SLUG) is True

    results = retrieve_chunks(TEST_SLUG, query_embedding(), 3)
    assert results
    for item in results:
        assert set(item) == RESULT_KEYS


@pytest.mark.integration
def test_find_similar_slug(conn):
    store_chunks(make_chunks())

    assert find_similar_slug(TEST_TYPO_SLUG) == TEST_SLUG


@pytest.mark.integration
def test_find_similar_slug_no_match(conn):
    assert find_similar_slug("completely-different-topic-xyz") is None


@pytest.mark.integration
def test_search_chunks_sql_function(conn):
    store_chunks(make_chunks())

    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM search_chunks(%s, %s::vector, 3)",
            (TEST_SLUG, query_embedding()),
        )
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

    assert rows
    assert columns == SEARCH_COLUMNS
    assert len(rows[0]) == 6


@pytest.mark.integration
def test_user_profile_insert_and_retrieve(conn):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO user_profiles (user_id, user_context) VALUES (%s, %s)",
            (TEST_USER_ID, TEST_USER_CONTEXT),
        )
        conn.commit()
        cur.execute(
            "SELECT user_context FROM user_profiles WHERE user_id = %s",
            (TEST_USER_ID,),
        )
        row = cur.fetchone()

    assert row[0] == TEST_USER_CONTEXT


@pytest.mark.integration
def test_user_profile_updated_at_trigger(conn):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO user_profiles (user_id, user_context) VALUES (%s, %s)",
            (TEST_USER_ID, TEST_USER_CONTEXT),
        )
        conn.commit()
        cur.execute(
            "SELECT updated_at FROM user_profiles WHERE user_id = %s",
            (TEST_USER_ID,),
        )
        first = cur.fetchone()[0]

        time.sleep(1)

        cur.execute(
            "UPDATE user_profiles SET user_context = %s WHERE user_id = %s",
            (UPDATED_USER_CONTEXT, TEST_USER_ID),
        )
        conn.commit()
        cur.execute(
            "SELECT updated_at FROM user_profiles WHERE user_id = %s",
            (TEST_USER_ID,),
        )
        second = cur.fetchone()[0]

    assert second > first
