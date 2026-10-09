from markdown_it import MarkdownIt
from markdownify import markdownify

from src.chains.image_fallback import run_image_with_fallback
from src.graph.enums import Platform
from src.graph.state import ContentState
from src.llm.fallback import run_with_fallback
from src.prompts.base import build_prompt
from src.prompts.instagram import IMAGE_STYLE as INSTAGRAM_IMAGE_STYLE
from src.prompts.linkedin import IMAGE_STYLE as LINKEDIN_IMAGE_STYLE
from src.prompts.medium import IMAGE_STYLE as MEDIUM_IMAGE_STYLE
from src.prompts.substack import IMAGE_STYLE as SUBSTACK_IMAGE_STYLE
from src.rag.arxiv_fetcher import fetch_arxiv_papers
from src.rag.bbc_fetcher import fetch_bbc_articles
from src.rag.chunker import chunk_text
from src.rag.cleaner import clean_text
from src.rag.embedder import embed_chunks, model
from src.rag.pdf_parser import parse_pdf
from src.rag.store import (
    find_similar_slug,
    retrieve_chunks,
    store_chunks,
    topic_is_cached,
)
from src.rag.utils import make_topic_slug

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

    citations_enabled = state.get("citations_enabled")
    if citations_enabled is None:
        citations_enabled = False
    if platform not in (Platform.MEDIUM, Platform.SUBSTACK):
        citations_enabled = False

    if platform == Platform.INSTAGRAM:
        image_enabled = True

    return {
        "citations_enabled": citations_enabled,
        "image_enabled": image_enabled,
    }


_DEFAULT_USER_ID = "default-user"

_PLATFORM_IMAGE_STYLES = {
    Platform.LINKEDIN: LINKEDIN_IMAGE_STYLE,
    Platform.INSTAGRAM: INSTAGRAM_IMAGE_STYLE,
    Platform.MEDIUM: MEDIUM_IMAGE_STYLE,
    Platform.SUBSTACK: SUBSTACK_IMAGE_STYLE,
}


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


def arxiv_rag_node(state: ContentState) -> dict:
    user_topic = state["topic"]
    slug = make_topic_slug(user_topic)

    try:
        cached_slug = find_similar_slug(slug)

        if cached_slug:
            slug = cached_slug
        else:
            if not topic_is_cached(slug):
                papers = fetch_arxiv_papers(user_topic)
                all_chunks = []
                for paper in papers:
                    text = parse_pdf(paper["pdf_url"])
                    text = clean_text(text)
                    chunks = chunk_text(text, slug, paper)
                    chunks = embed_chunks(chunks)
                    all_chunks.extend(chunks)
                store_chunks(all_chunks)

        encoded = model.encode([user_topic])
        query_embedding = (
            encoded[0].tolist() if hasattr(encoded[0], "tolist") else list(encoded[0])
        )
        results = retrieve_chunks(slug, query_embedding, 3)
        return {**state, "rag_context": results, "rag_status": None}

    except Exception as e:
        return {
            **state,
            "rag_context": [],
            "rag_status": (
                "Scientific sources unavailable for this topic — "
                f"generating without RAG context. ({type(e).__name__}: {e})"
            ),
        }


def news_rag_node(state: ContentState) -> dict:
    user_topic = state["topic"]

    try:
        articles = fetch_bbc_articles(user_topic, top_k=3)

        if not articles:
            return {
                **state,
                "rag_context": [],
                "rag_status": (
                    "No relevant BBC articles found for this topic — "
                    "generating without news context."
                ),
            }

        rag_context = [
            {
                "chunk_text": f"{a['title']}. {a['summary']}",
                "paper_id": a["url"],
                "paper_title": a["title"],
                "authors": "BBC News",
                "arxiv_url": a["url"],
                "similarity": 0.0,
            }
            for a in articles
        ]

        return {**state, "rag_context": rag_context, "rag_status": None}

    except Exception as e:
        return {
            **state,
            "rag_context": [],
            "rag_status": (
                "News sources unavailable — "
                f"generating without news context. ({type(e).__name__}: {e})"
            ),
        }


async def image_node(state: ContentState) -> dict:
    platform = state["platform"]
    topic = state["topic"]
    image_style = _PLATFORM_IMAGE_STYLES[platform]
    status_messages = list(state["status_messages"])

    prompt = f"{image_style} — {state['image_prompt']}, topic: {topic}"

    image_data = None
    async for update in run_image_with_fallback(
        prompt=prompt,
        platform=platform,
        user_id=_DEFAULT_USER_ID,
    ):
        status_messages.append(update.status)
        if update.result is not None:
            image_data = update.result
        if update.is_last:
            status_messages.append("You've reached your daily image limit")

    return {
        "image_data": image_data,
        "status_messages": status_messages,
    }


def linkedin_node(state: ContentState) -> dict:
    text = state["generated_text"]
    image_prompt = ""

    if state["image_enabled"]:
        text, image_prompt = _extract_image_prompt(text)

    text = _to_plain_text(text)
    text = _ensure_hashtags_at_end(text)
    text = _trim_words(text, 300)
    return {"generated_text": text, "image_prompt": image_prompt}


def instagram_node(state: ContentState) -> dict:
    text = state["generated_text"]
    image_prompt = ""

    if state["image_enabled"]:
        text, image_prompt = _extract_image_prompt(text, prefix="[POST IMAGE:")

    text = _to_plain_text(text)
    lines = text.splitlines()
    hashtag_lines = [line for line in lines if line.strip().startswith("#")]
    non_hashtag_lines = [line for line in lines if not line.strip().startswith("#")]
    text = "\n".join(non_hashtag_lines).strip()
    if hashtag_lines:
        text = text + "\n\n" + " ".join(hashtag_lines)
    text = _trim_words(text, 150)
    return {"generated_text": text, "image_prompt": image_prompt}


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
