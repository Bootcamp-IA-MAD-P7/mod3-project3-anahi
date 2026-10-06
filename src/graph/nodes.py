from markdown_it import MarkdownIt
from markdownify import markdownify

from src.graph.enums import Platform
from src.graph.state import ContentState
from src.llm.fallback import run_with_fallback
from src.prompts.base import build_prompt

_md = MarkdownIt()


def _to_plain_text(text: str) -> str:
    return markdownify(text).strip()


def _extract_image_prompt(text: str, prefix: str = "[HEADER IMAGE:") -> tuple[str, str]:
    lines = text.splitlines()
    image_prompt = ""
    filtered_lines = []
    for line in lines:
        if line.strip().startswith(prefix):
            image_prompt = line.strip()[len(prefix) :].rstrip("]").strip()
        else:
            filtered_lines.append(line)
    return "\n".join(filtered_lines).strip(), image_prompt


def _ensure_hashtags_at_end(text: str) -> str:
    lines = text.splitlines()
    hashtag_lines = [
        line
        for line in lines
        if line.strip().startswith("#") and not line.strip().startswith("##")
    ]
    non_hashtag_lines = [
        line
        for line in lines
        if not (line.strip().startswith("#") and not line.strip().startswith("##"))
    ]
    if hashtag_lines:
        return "\n".join(non_hashtag_lines).strip() + "\n\n" + " ".join(hashtag_lines)
    return text


def _trim_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def router_node(state: ContentState) -> dict:
    platform = state["platform"]
    image_enabled = state["image_enabled"]

    rag_enabled = state.get("rag_enabled")
    if rag_enabled is None:
        rag_enabled = platform in (Platform.MEDIUM, Platform.SUBSTACK)

    citations_enabled = state.get("citations_enabled")
    if citations_enabled is None:
        citations_enabled = False
    if platform not in (Platform.MEDIUM, Platform.SUBSTACK):
        citations_enabled = False

    if platform == Platform.INSTAGRAM:
        image_enabled = True

    return {
        "rag_enabled": rag_enabled,
        "citations_enabled": citations_enabled,
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


def rag_node(state: ContentState) -> dict:
    raise NotImplementedError


def image_node(state: ContentState) -> dict:
    raise NotImplementedError


def linkedin_node(state: ContentState) -> dict:
    text = state["generated_text"]
    text = _to_plain_text(text)
    text = _ensure_hashtags_at_end(text)
    text = _trim_words(text, 300)
    return {"generated_text": text}


def instagram_node(state: ContentState) -> dict:
    text = state["generated_text"]
    text = _to_plain_text(text)
    lines = text.splitlines()
    hashtag_lines = [line for line in lines if line.strip().startswith("#")]
    non_hashtag_lines = [line for line in lines if not line.strip().startswith("#")]
    text = "\n".join(non_hashtag_lines).strip()
    if hashtag_lines:
        text = text + "\n\n" + " ".join(hashtag_lines)
    text = _trim_words(text, 150)
    return {"generated_text": text}


def medium_node(state: ContentState) -> dict:
    text = state["generated_text"]
    image_prompt = ""

    if state["image_enabled"]:
        text, image_prompt = _extract_image_prompt(text)

    return {
        "generated_text": text,
        "image_prompt": image_prompt,
    }


def substack_node(state: ContentState) -> dict:
    text = state["generated_text"]
    image_prompt = ""

    if state["image_enabled"]:
        text, image_prompt = _extract_image_prompt(
            text, prefix="[HEADER IMAGE: illustration style —"
        )

    return {
        "generated_text": text,
        "image_prompt": image_prompt,
    }
