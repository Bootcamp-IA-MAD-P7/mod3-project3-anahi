from langchain_core.messages import HumanMessage, SystemMessage


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
