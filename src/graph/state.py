from typing import NotRequired, TypedDict

from src.graph.enums import Platform, Provider


class RagChunk(TypedDict):
    chunk_text: str
    paper_id: str
    paper_title: str
    authors: str
    arxiv_url: str
    similarity: float


class ContentState(TypedDict):
    token: str
    topic: str
    platform: Platform
    audience: str
    language: str
    model: str
    provider: Provider
    image_enabled: bool
    citations_enabled: bool
    user_context: str
    rag_context: NotRequired[list[RagChunk]]
    rag_status: NotRequired[str | None]
    generated_text: str
    image_data: bytes | None
    image_prompt: str
    status_messages: list[str]
