from src.graph.enums import Platform
from src.graph.state import ContentState
from src.llm.fallback import run_with_fallback
from src.prompts.base import build_prompt


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


_DEFAULT_USER_ID = "default-user"


def llm_node(state: ContentState) -> dict:
    messages = build_prompt(state)
    status_messages = list(state["status_messages"])

    result = None
    for update in run_with_fallback(
        selected_model=state["model"],
        prompt=messages,
        user_id=_DEFAULT_USER_ID,
        provider=state["provider"],
    ):
        status_messages.append(update.status)
        if update.result is not None:
            result = update.result

    if result is None:
        raise RuntimeError("All models failed — content could not be generated")

    return {
        "generated_text": result.text,
        "status_messages": status_messages,
        "model": result.model_name,
    }
