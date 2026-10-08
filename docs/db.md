# Database Setup

Neon (serverless Postgres) with pgvector. No pooling — use the direct connection string.

## Requirements

- Neon account — [neon.tech](https://neon.tech)
- Neon Auth enabled in the dashboard (owns the `users` table)
- pgvector supported on Neon free tier — no extra setup needed

## Setup

1. Create a Neon project, region AWS Europe Central 1 (Frankfurt)
2. Dashboard → Auth → enable (Email provider)
3. Dashboard → Connection Details → copy **direct** connection string (no `-pooler` in the URL)
4. Copy `.env.example` to `.env` and fill in your values
5. Dashboard → SQL Editor → paste and run [schema.sql](../db/schema.sql)

## Tables

| Table | Owner | Description |
|---|---|---|
| `users` | Neon Auth | Managed automatically — do not modify |
| `user_profiles` | us | Extends users with `user_context` for persona/company context |
| `rag_chunks` | us | Stores cleaned, chunked, embedded arXiv passages |

## Functions

| Function | Description |
|---|---|
| `topic_is_cached(slug)` | Returns true if topic already has chunks in DB — skips cold path |
| `search_chunks(slug, embedding, k)` | Returns top-k passages by cosine similarity for a given topic |

## Notes

- ivfflat index on `rag_chunks.embedding` needs ~few hundred rows to be effective; sequential scan is used on small data (fine for PoC)
- `user_context` is free text — company name, tone, brand voice, audience; injected into every generation prompt
- Add `.env` to `.gitignore` immediately and after config.py
