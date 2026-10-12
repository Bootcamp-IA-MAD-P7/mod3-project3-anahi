from fastembed import TextEmbedding

model = TextEmbedding("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [embedding.tolist() for embedding in model.embed(texts)]


def embed_chunks(chunks: list[dict]) -> list[dict]:
    embeddings = embed_texts([chunk["chunk_text"] for chunk in chunks])
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding
    return chunks


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]
