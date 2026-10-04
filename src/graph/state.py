from typing import TypedDict

from src.graph.enums import Platform, Provider


class ContentState(TypedDict):
    topic: str
    platform: Platform
    audience: str
    language: str
    model: str
    provider: Provider
    rag_enabled: bool
    image_enabled: bool
    company_context: str
    rag_context: str
    generated_text: str
    image_data: bytes | None
    status_messages: list[str]
