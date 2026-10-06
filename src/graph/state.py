from typing import TypedDict

from src.graph.enums import Platform, Provider


class ContentState(TypedDict):
    topic: str
    platform: Platform
    audience: str
    language: str
    model: str
    provider: Provider
    image_enabled: bool
    rag_enabled: bool
    citations_enabled: bool
    user_context: str
    rag_context: str
    generated_text: str
    image_data: bytes | None
    image_prompt: str
    status_messages: list[str]
