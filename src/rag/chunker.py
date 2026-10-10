from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(text: str, topic_slug: str, paper_meta: dict) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    return [
        {
            "topic_slug": topic_slug,
            "chunk_text": chunk,
            "paper_id": paper_meta["paper_id"],
            "paper_title": paper_meta["title"],
            "authors": paper_meta["authors"],
            "arxiv_url": paper_meta["arxiv_url"],
        }
        for chunk in chunks
        if len(chunk.split()) >= 8
    ]
