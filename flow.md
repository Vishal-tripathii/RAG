# Flow — What Happens Today

This describes what the code **actually does today** (not the target design in `uploaddesign.md`,
which is background-worker/S3-based and not implemented yet). Both flows below run synchronously,
inside a single request — no background worker or job queue.

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

1. **`routers/upload.py`** — `/upload`, `/documents` (list/get), `/documents` (delete all/one). Thin — just calls into `upload_service`.
2. **`routers/ask.py`** — `/ask`. Orchestrates search_service → generation_service and shapes the response.
3. **`services/upload_service.py`** — the conductor for ingestion, plus all document CRUD (list/get/delete) and the doc_id→filename lookup `/ask` uses for citations.
4. **`services/pdf_service.py`** — reads the PDF, extracts plain text per page. Rejects scanned/text-less PDFs with a 400.
5. **`utils/text_cleaning.py`** — tidies raw text (collapses horizontal whitespace, keeps newlines — the chunker's separators depend on real `\n`/`\n\n`).
6. **`services/chunking_service.py`** — breaks cleaned text into ~500-char overlapping chunks per page.
7. **`services/embedding_service.py`** — loads `BAAI/bge-small-en-v1.5` once at import time; embeds chunks for ingest and queries for search (query side gets the asymmetric-retrieval instruction prefix, passage side doesn't).
8. **`vector_store.py`** — Qdrant client: collection init, upsert, similarity search, delete-by-document, delete-all.
9. **`services/search_service.py`** — embeds a query and runs the Qdrant search, resolving the configured top-K/threshold.
10. **`services/generation_service.py`** — builds the grounded, citation-numbered prompt and calls Gemini.
11. **`models.py`** — `Document` (uploaded file, incl. `content_hash` for dedup) and `Chunk` (a piece of it), as Postgres rows.
12. **Postgres** — stores `Document` and `Chunk` rows, linked by `document_id`.
13. **Qdrant** — stores chunk vectors + payload, linked by `document_id` for filtering/deletion.

## What's missing / known gaps

- No background worker — ingestion (parse → chunk → embed → Qdrant upsert) all happens inline in the `/upload` request, unlike the target design in `uploaddesign.md`.
- Deleting a document doesn't remove its file from `uploads/` on disk.
- A rare race on identical concurrent uploads can leave orphaned Qdrant vectors/files if the DB's unique-hash constraint rejects the second insert (not currently caught).
