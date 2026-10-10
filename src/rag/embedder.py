from sentence_transformers import SentenceTransformer

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def embed_chunks(chunks: list[dict]) -> list[dict]:
    texts = [chunk["chunk_text"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()
    return chunks
