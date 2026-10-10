import arxiv


def fetch_arxiv_papers(topic: str, max_results: int = 3) -> list[dict]:
    client = arxiv.Client()
    search = arxiv.Search(
        query=topic, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance
    )
    papers = []
    for result in client.results(search):
        papers.append(
            {
                "paper_id": result.entry_id.split("/")[-1],
                "title": result.title,
                "authors": ", ".join(a.name for a in result.authors),
                "arxiv_url": result.entry_id,
                "pdf_url": result.pdf_url,
                "summary": result.summary,
            }
        )
    return papers
