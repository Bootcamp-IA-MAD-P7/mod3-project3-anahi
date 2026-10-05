from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from src.graph.enums import Platform
from src.graph.state import ContentState
from src.prompts.instagram import build_instagram_prompt
from src.prompts.linkedin import build_linkedin_prompt
from src.prompts.medium import build_medium_prompt
from src.prompts.substack import build_substack_prompt


def build_language_instruction(language: str) -> str:
    return f"Generate the content in {language}"


def build_user_block(user_context: str) -> str:
    if not user_context:
        return ""
    return f"Context about the author or person publishing this content: {user_context}"


def build_rag_block(rag_context: str) -> str:
    if not rag_context:
        return ""
    return f"Use the following research as reference material and cite sources naturally in the text:\n{rag_context}"  # noqa: E501


def build_human_message(parts: list[str]) -> HumanMessage:
    content = "\n\n".join(part for part in parts if part)
    return HumanMessage(content=content)


def build_system_message(content: str) -> SystemMessage:
    return SystemMessage(content=content)


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
