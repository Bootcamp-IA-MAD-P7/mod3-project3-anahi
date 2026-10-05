from langchain_core.messages import BaseMessage

from src.graph.state import ContentState


def build_linkedin_prompt(state: ContentState) -> list[BaseMessage]:
    raise NotImplementedError
