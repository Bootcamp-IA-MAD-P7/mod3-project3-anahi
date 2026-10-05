from langchain_core.messages import BaseMessage

from src.graph.state import ContentState


def build_instagram_prompt(state: ContentState) -> list[BaseMessage]:
    raise NotImplementedError
