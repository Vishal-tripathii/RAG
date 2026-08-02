# Flow — What Happens Today

This describes what the code **actually does today** (not the target design in `uploaddesign.md`,
which is background-worker/S3-based and not implemented yet). Both backend flows below run
synchronously, inside a single request — no background worker or job queue.

## Frontend

```
Vite dev server (localhost:5173)
        ↓
App.tsx                    → RouterProvider(router)
        ↓
app/router.tsx              → "/" and "/chat" render inside AppLayout (Sidebar + <Outlet/>).
                               No route guard - every page is reachable by anyone right now.
        ↓
pages/Home.tsx               → static placeholder, no data
pages/Chat.tsx                → upload form (→ api/documents.ts → POST /upload)
                                 + ask form (→ api/ask.ts → POST /ask, top_k defaults to 5)
                                 renders the answer as Markdown (react-markdown) and the
                                 numbered sources via components/SourceList.tsx
        ↓
api/client.ts                 → fetch wrapper against VITE_API_BASE_URL
                                 (frontend/.env.development, defaults to http://localhost:8000)
```

`components/LoginForm.tsx` exists but is **not wired to any route** - there's no `/login` in
`app/router.tsx` and nothing renders it. It's dead code today, not a working auth screen.

## Upload — `POST /upload`

```
User uploads a PDF
        ↓
routers/upload.py            → receives the file
        ↓
services/upload_service.py   → hashes the bytes (SHA-256) and checks Postgres for
                                that hash. If found: 409, stop here — nothing below runs.
        ↓
services/pdf_service.py      → opens the PDF, pulls raw text per page
                                (400 if there's no extractable text, e.g. a scanned PDF)
        ↓
utils/text_cleaning.py       → collapses extra whitespace, keeps newlines
        ↓
services/chunking_service.py → splits each page into ~500-character overlapping pieces
        ↓
services/embedding_service.py → turns each piece into a 384-number vector
                                 (BAAI/bge-small-en-v1.5, local via fastembed)
        ↓
vector_store.py               → upserts the vectors + payload (text, document_id,
                                 page, chunk_index) into Qdrant
        ↓
services/upload_service.py    → saves the file to disk (uploads/) and saves the
                                 Document + Chunk rows to Postgres
        ↓
Response sent back (doc_id, filename, size...)
```

## Ask — `POST /ask`

```
User asks a question
        ↓
routers/ask.py                 → receives { query, top_k? }
        ↓
services/search_service.py     → embeds the query (same model, with the bge
                                  "search query" instruction prefix)
        ↓
vector_store.py                → Qdrant similarity search, top-K chunks
                                  (K defaults to SEARCH_TOP_K, capped at 50/request)
        ↓
services/upload_service.py     → resolves each hit's document_id to a filename
(get_filenames)
        ↓
services/generation_service.py → builds a numbered-source prompt ([1], [2]...)
                                  and calls Gemini (gemini-flash-latest)
        ↓
Response sent back: { answer, sources[] } — each source carries its number,
                     filename, document_id, page, score, and text
```

## Documents — `GET/DELETE /documents`, `GET/DELETE /documents/{doc_id}`

Read/list/delete against Postgres metadata. Delete also removes the document's
vectors from Qdrant (`vector_store.delete_by_document_id` / `delete_all_points`).
It does **not** currently delete the file saved under `uploads/`.

## File-by-file

1. **`routers/health.py`** — `GET /`, returns `{"status": "FastAPI is running!"}`. Used as a liveness check, not called by the frontend.
2. **`routers/upload.py`** — `/upload`, `/documents` (list/get), `/documents` (delete all/one). Thin — just calls into `upload_service`.
3. **`routers/ask.py`** — `/ask`. Orchestrates search_service → generation_service and shapes the response.
4. **`services/upload_service.py`** — the conductor for ingestion, plus all document CRUD (list/get/delete) and the doc_id→filename lookup `/ask` uses for citations.
5. **`services/pdf_service.py`** — reads the PDF, extracts plain text per page. Rejects scanned/text-less PDFs with a 400.
6. **`utils/text_cleaning.py`** — tidies raw text (collapses horizontal whitespace, keeps newlines — the chunker's separators depend on real `\n`/`\n\n`).
7. **`services/chunking_service.py`** — breaks cleaned text into ~500-char overlapping chunks per page.
8. **`services/embedding_service.py`** — loads `BAAI/bge-small-en-v1.5` once at import time; embeds chunks for ingest and queries for search (query side gets the asymmetric-retrieval instruction prefix, passage side doesn't).
9. **`vector_store.py`** — Qdrant client: collection init, upsert, similarity search, delete-by-document, delete-all.
10. **`services/search_service.py`** — embeds a query and runs the Qdrant search, resolving the configured top-K/threshold.
11. **`services/generation_service.py`** — builds the grounded, citation-numbered prompt and calls Gemini.
12. **`models.py`** — `Document` (uploaded file, incl. `content_hash` for dedup) and `Chunk` (a piece of it), as Postgres rows.
13. **Postgres** — stores `Document` and `Chunk` rows, linked by `document_id`.
14. **Qdrant** — stores chunk vectors + payload, linked by `document_id` for filtering/deletion.
15. **`app/router.tsx`** — `/` (Home) and `/chat` (Chat), both inside `AppLayout`. No `/login` route and no auth guard.
16. **`pages/Chat.tsx`** — the only page that talks to the backend: upload form + ask form, renders answers as Markdown and sources via `SourceList.tsx`.
17. **`api/client.ts`** — fetch wrapper; base URL from `VITE_API_BASE_URL` (`frontend/.env.development`), falls back to `http://localhost:8000`.
18. **`components/LoginForm.tsx`** — unused; not imported by any route or page.

## What's missing / known gaps

- No background worker — ingestion (parse → chunk → embed → Qdrant upsert) all happens inline in the `/upload` request, unlike the target design in `uploaddesign.md`.
- Deleting a document doesn't remove its file from `uploads/` on disk.
- No auth anywhere — no `/login` route wired up (`LoginForm.tsx` is dead code), no auth guard on any frontend route, no auth check on any backend endpoint.
- CORS on the backend hard-codes `http://localhost:5173` as the only allowed origin (`main.py`) — nothing else works against this API as-is.
- A rare race on identical concurrent uploads can leave orphaned Qdrant vectors/files if the DB's unique-hash constraint rejects the second insert (not currently caught).
