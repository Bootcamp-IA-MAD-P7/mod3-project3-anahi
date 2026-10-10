-- Run on a fresh Neon DB (direct connection, no pooling)
-- Requires pgvector extension support (enabled on Neon free tier)
-- Neon Auth must be enabled separately in the dashboard — it owns the users table

-- 1. Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. user_profiles (Neon Auth owns users, we just extend it)
CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,
    user_context TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. RAG chunks
CREATE TABLE rag_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_slug TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    paper_id TEXT NOT NULL,
    paper_title TEXT NOT NULL,
    authors TEXT NOT NULL,
    arxiv_url TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Indexes
CREATE INDEX idx_rag_chunks_topic_slug ON rag_chunks(topic_slug);
CREATE INDEX idx_rag_chunks_embedding ON rag_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 5. updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 6. Trigger on user_profiles
CREATE TRIGGER user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- 7. Cache check
CREATE OR REPLACE FUNCTION topic_is_cached(p_topic_slug TEXT)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM rag_chunks WHERE topic_slug = p_topic_slug LIMIT 1
    );
$$ LANGUAGE sql STABLE;

-- 8. Similarity search
CREATE OR REPLACE FUNCTION search_chunks(
    p_topic_slug TEXT,
    p_query_embedding vector(384),
    p_top_k INT DEFAULT 3
)
RETURNS TABLE (
    chunk_text TEXT,
    paper_id TEXT,
    paper_title TEXT,
    authors TEXT,
    arxiv_url TEXT,
    similarity FLOAT
) AS $$
    SELECT
        chunk_text,
        paper_id,
        paper_title,
        authors,
        arxiv_url,
        1 - (embedding <=> p_query_embedding) AS similarity
    FROM rag_chunks
    WHERE topic_slug = p_topic_slug
    ORDER BY embedding <=> p_query_embedding
    LIMIT p_top_k;
$$ LANGUAGE sql STABLE;
