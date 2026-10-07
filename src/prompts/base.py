from langchain_core.messages import BaseMessage

from src.graph.enums import Platform
from src.graph.state import ContentState
from src.prompts.instagram import build_instagram_prompt
from src.prompts.linkedin import build_linkedin_prompt
from src.prompts.medium import build_medium_prompt
from src.prompts.substack import build_substack_prompt

_PLATFORM_BUILDERS = {
    Platform.LINKEDIN: build_linkedin_prompt,
    Platform.INSTAGRAM: build_instagram_prompt,
    Platform.MEDIUM: build_medium_prompt,
    Platform.SUBSTACK: build_substack_prompt,
}


def build_prompt(state: ContentState) -> list[BaseMessage]:
    platform = state["platform"]
    builder = _PLATFORM_BUILDERS.get(platform)
    if builder is None:
        raise ValueError(f"No prompt builder for platform {platform}")
    return builder(state)
