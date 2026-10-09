# RAG Architecture

This project uses two separate RAG pipelines, each activated by platform.
The routing is platform-driven: the LangGraph router node decides which
pipeline to invoke based on the user's selected platform, before the LLM
generation node runs.

| Platform | RAG Pipeline | Citations |
|---|---|---|
| Medium | arXiv RAG | On |
| Substack | arXiv RAG | On |
| LinkedIn | News RAG (BBC) | Off |
| Instagram | None | Off |

---

## Pipeline 1 — arXiv RAG (Medium, Substack)

Scientific content for long-form platforms is grounded in peer-reviewed
research fetched from arXiv.

### Why arXiv

arXiv is a fully public preprint server — no API key, no rate limits, no
cost. It covers the scientific domains most relevant to science communication
content (AI, physics, biomedicine, computer science). The `arxiv` Python
package wraps the API cleanly.

### Cold path vs cache

The pipeline distinguishes between a first request for a topic (cold path)
and a repeat request (cache hit):

**Cache hit** — topic slug exists in pgvector DB → skip fetch, parse, embed
entirely → go straight to retrieval. This is checked via `topic_is_cached()`
before any network call.

**Fuzzy cache** — before the exact cache check, `find_similar_slug()` uses
`difflib.SequenceMatcher` to compare the incoming slug against all existing
slugs in the DB. If similarity ≥ 0.8, the closest existing slug is reused.
This means "quantum-computing" and "quantum-computers" share the same cached
chunks rather than triggering two separate cold paths.

**Cold path** — topic not in DB → fetch top 3 arXiv papers → parse each PDF
→ clean text → chunk → embed → store all chunks in pgvector → retrieve.

### PDF parsing

PDFs are downloaded in memory (no disk writes) using `requests` + `BytesIO`
and parsed with PyMuPDF (`fitz`). `page.get_text(sort=True)` is used on
every page to enforce reading order — critical for two-column academic papers
where the default parse order mixes columns. The references section is cut
before any further processing using a regex that matches "References",
"Bibliography", or "Works Cited" headings.

### Cleaning

Before chunking, the extracted text goes through two cleaning steps:

**Cross-reference stripping** — phrases like "as shown in Table 2" or
"see Figure 3" are stripped with regex substitution. The surrounding sentence
is kept; only the dangling pointer is removed. This preserves claims like
"our method achieves 94.2 F1" that would otherwise be contextually broken.

**Junk filtering** — lines are dropped entirely if they match known junk
patterns: arXiv stamp headers, lone page numbers, figure/table captions,
LaTeX math residue, bibliography fragments. A minimum word floor of 8 words
per line catches anything that survived the pattern filters.

### Chunking

`RecursiveCharacterTextSplitter` from LangChain with `chunk_size=1000`
characters (≈150–200 words) and `chunk_overlap=150` characters (≈25 words).
Separators are tried in order: paragraph break → line break → sentence
boundary → word boundary. This always prefers natural language boundaries
over arbitrary character cuts. A final 8-word floor on chunks drops any
fragments that survived cleaning.

Each chunk carries full paper metadata (title, authors, arXiv ID, URL)
so citations can be built at output time without a second DB lookup.

### Embeddings

Model: `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions), loaded
once at module import via `sentence-transformers`. Multilingual by design —
a user topic submitted in Spanish or French is embedded directly without a
translation step, and similarity search against English paper chunks still
works because the model maps all languages into the same vector space.

### Storage

pgvector on Neon (serverless Postgres, Frankfurt region, direct connection —
no pooling, which is incompatible with pgvector). Chunks are stored in the
`rag_chunks` table with an ivfflat index on the embedding column using cosine
distance. The `search_chunks` SQL function handles retrieval, returning top-k
passages ranked by cosine similarity for a given topic slug.

### Retrieval

At query time, the user topic is embedded with the same MiniLM model and
passed to `search_chunks(slug, embedding, 3)`. Top 3 passages are returned
as structured dicts (`RagChunk` TypedDict) and written to `state["rag_context"]`
for the prompt builder to consume.

### Failure handling

Any exception in the pipeline — network failure, PDF parse error, DB
unavailability — is caught at the node level. The node degrades gracefully:
`rag_context` is set to an empty list, `rag_status` carries a human-readable
error message that surfaces in the UI, and the LLM generation node runs
without RAG context rather than crashing the graph.

---

## Pipeline 2 — News RAG (LinkedIn)

LinkedIn content is grounded in current news fetched live from BBC News RSS
feeds.

### Why BBC RSS instead of a news API

BBC News publishes live RSS feeds updated continuously. Rather than
integrating a third-party news API (which would require key management, has
rate limits, and introduces an unknown reliability dependency), we chose BBC
as a well-known, editorially independent source with strong business and
technology coverage — the two categories most relevant to LinkedIn
professional content.

RSS is a standard web feed protocol. The fetcher makes an HTTP GET request
to BBC's servers and receives a live XML document containing the latest
articles. This is live updated data, not cached or static content, and
satisfies the project requirement for "updated information via APIs."

No API key is required. No rate limits apply for reasonable usage.

### Feeds

- http://feeds.bbci.co.uk/news/business/rss.xml (~20–30 articles)
- http://feeds.bbci.co.uk/news/technology/rss.xml (~20–30 articles)

Both feeds are fetched and pooled on every request (~50 articles total).
Business and technology are chosen specifically for LinkedIn — they cover
the industry news, market trends, and professional topics most relevant to
that platform's audience.

### Why no query parameter

RSS feeds do not support topic queries — you receive the full current feed
and filter client-side. This is a structural difference from a search API,
but the outcome is the same: current, relevant articles matched to the
user's topic. The matching is handled by semantic similarity rather than
keyword search.

### Relevance matching

Rather than keyword filtering (which fails on nuanced topics), we reuse the
multilingual MiniLM model already loaded in memory from the arXiv pipeline.
The user topic and each article's concatenated title + summary are embedded,
and cosine similarity via `sentence_transformers.util.cos_sim` ranks all
pooled articles in a single matrix operation. The top 3 most semantically
relevant articles are returned.

No additional model, no additional embedding infrastructure. The model is
already in memory.

### Output format

Retrieved articles are mapped to the same `RagChunk` TypedDict used by the
arXiv pipeline, so the prompt builder and formatter nodes handle both
pipelines identically downstream. `authors` is set to `"BBC News"`,
`arxiv_url` to the article URL. Citations are disabled for LinkedIn so the
URL fields are present in state but never rendered in the output.

### Failure handling

Same pattern as arXiv RAG — any exception degrades gracefully to empty
`rag_context` and a `rag_status` message. Feed unavailability or an empty
result set both produce a status message without crashing the graph.

---

## Shared infrastructure

Both pipelines write to the same `rag_context: list[RagChunk]` field in
`ContentState` and the same `rag_status: str | None` field. The prompt
builder (`build_rag_block`) consumes `rag_context` identically regardless
of which pipeline produced it. Citations (Medium/Substack only) are built
from `paper_title`, `authors`, and `arxiv_url` fields — for BBC articles
these fields are populated but the citations block is suppressed by the
`citations_enabled` flag in state.

The router node routes purely by platform: Medium and Substack invoke the arXiv
pipeline, LinkedIn invokes the News pipeline, and Instagram bypasses RAG entirely
because no pipeline exists for it.

### Why there is no `rag_enabled` toggle

RAG was first designed with an explicit `rag_enabled` flag that callers could set
per request, defaulting to on for the platforms that have a pipeline. It was
ultimately decided against and deleted, because the tradeoff was not good.

Removing it makes the system leaner than keeping it: fewer state permutations to
reason about, routing that depends on nothing but the platform, and no branch where
a caller accidentally disables grounding and gets a silently worse answer. The
benefit a toggle would offer — letting a user opt out — would not compensate for
that cost, because most users want the magic to happen, not make more decisions.

So RAG is always on, the router is a pure function of platform, and the only
remaining escape hatch is failure: if a pipeline cannot run, it degrades to an
empty context and generation proceeds without grounding.
