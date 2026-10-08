from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.state import RagChunk


def build_language_instruction(language: str) -> str:
    return f"Generate the content in {language}"


def build_user_block(user_context: str) -> str:
    if not user_context:
        return ""
    return f"Context about the author or person publishing this content: {user_context}"


def build_rag_block(rag_context: list[RagChunk]) -> str:
    if not rag_context:
        return ""
    passages = []
    for i, chunk in enumerate(rag_context, 1):
        passages.append(
            f"[{i}] {chunk['chunk_text']}\n"
            f"Source: {chunk['paper_title']} — {chunk['authors']} "
            f"({chunk['arxiv_url']})"
        )
    formatted = "\n\n".join(passages)
    return (
        "Use the following research as reference material "
        f"and cite sources naturally in the text:\n\n{formatted}"
    )


def build_human_message(parts: list[str]) -> HumanMessage:
    content = "\n\n".join(part for part in parts if part)
    return HumanMessage(content=content)


def build_system_message(content: str) -> SystemMessage:
    return SystemMessage(content=content)
