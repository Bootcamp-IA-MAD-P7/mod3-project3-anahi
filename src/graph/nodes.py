from src.graph.enums import Platform
from src.graph.state import ContentState


def router_node(state: ContentState) -> dict:
    platform = state["platform"]
    rag_enabled = state["rag_enabled"]
    image_enabled = state["image_enabled"]

    if platform not in (Platform.MEDIUM, Platform.SUBSTACK):
        rag_enabled = False

    if platform == Platform.INSTAGRAM:
        image_enabled = True

    return {
        "rag_enabled": rag_enabled,
        "image_enabled": image_enabled,
    }
