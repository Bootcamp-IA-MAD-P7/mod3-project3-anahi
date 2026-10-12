from langgraph.graph import END

from src.graph.enums import Language, Platform
from src.graph.state import ContentState


def _route_after_router(state: ContentState) -> str:
    platform = state["platform"]
    if platform in (Platform.MEDIUM, Platform.SUBSTACK):
        return "arxiv_rag_node"
    if platform == Platform.LINKEDIN:
        return "news_rag_node"
    return "llm_node"


def _route_after_llm(state: ContentState) -> str:
    platform = state["platform"]
    return {
        Platform.LINKEDIN: "linkedin_node",
        Platform.INSTAGRAM: "instagram_node",
        Platform.MEDIUM: "medium_node",
        Platform.SUBSTACK: "substack_node",
    }[platform]


def _route_after_platform(state: ContentState) -> str:
    if (
        state["platform"] != Platform.INSTAGRAM
        and state.get("language", Language.EN) != Language.EN
    ):
        return "translation_node"
    if state["image_enabled"]:
        return "image_node"
    return END


def _route_after_translation(state: ContentState) -> str:
    if state["image_enabled"]:
        return "image_node"
    return END
