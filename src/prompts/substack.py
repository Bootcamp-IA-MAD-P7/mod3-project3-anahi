from langchain_core.messages import BaseMessage

from src.graph.state import ContentState


def build_substack_prompt(state: ContentState) -> list[BaseMessage]:
    raise NotImplementedError
