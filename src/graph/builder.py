from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.graph.enums import Platform
from src.graph.nodes import (
    image_node,
    instagram_node,
    linkedin_node,
    llm_node,
    medium_node,
    rag_node,
    router_node,
    substack_node,
)
from src.graph.state import ContentState


def _route_after_router(state: ContentState) -> str:
    if state["rag_enabled"]:
        return "rag_node"
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
    if state["image_enabled"]:
        return "image_node"
    return END


def build_graph() -> CompiledStateGraph:
    builder = StateGraph(ContentState)

    builder.add_node("router_node", router_node)
    builder.add_node("rag_node", rag_node)
    builder.add_node("llm_node", llm_node)
    builder.add_node("linkedin_node", linkedin_node)
    builder.add_node("instagram_node", instagram_node)
    builder.add_node("medium_node", medium_node)
    builder.add_node("substack_node", substack_node)
    builder.add_node("image_node", image_node)

    builder.add_edge(START, "router_node")
    builder.add_conditional_edges("router_node", _route_after_router)
    builder.add_edge("rag_node", "llm_node")
    builder.add_conditional_edges("llm_node", _route_after_llm)
    builder.add_conditional_edges("linkedin_node", _route_after_platform)
    builder.add_conditional_edges("instagram_node", _route_after_platform)
    builder.add_conditional_edges("medium_node", _route_after_platform)
    builder.add_conditional_edges("substack_node", _route_after_platform)
    builder.add_edge("image_node", END)

    return builder.compile()


graph = build_graph()
