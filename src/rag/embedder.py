import os

import requests

_HF_API_URL = (
    "https://api-inference.huggingface.co/models/"
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
_HF_TOKEN = os.environ.get("HF_TOKEN", "")


def _call_hf(texts: list[str]) -> list[list[float]]:
    response = requests.post(
        _HF_API_URL,
        headers={"Authorization": f"Bearer {_HF_TOKEN}"},
        json={"inputs": texts, "options": {"wait_for_model": True}},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def embed_chunks(chunks: list[dict]) -> list[dict]:
    texts = [chunk["chunk_text"] for chunk in chunks]
    embeddings = _call_hf(texts)
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding
    return chunks


def embed_query(query: str) -> list[float]:
    return _call_hf([query])[0]
