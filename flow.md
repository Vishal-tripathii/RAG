# Flow — What Happens When You Upload a File

This describes what the code **actually does today** (not the target design in `uploaddesign.md`). Everything below runs synchronously, inside one `/upload` request — no background worker yet.

```
User uploads a PDF
        ↓
routers/upload.py            → receives the file
        ↓
services/upload_service.py   → orchestrates every step below
        ↓
services/pdf_service.py      → opens the PDF, pulls raw text per page
        ↓
utils/text_cleaning.py       → collapses extra whitespace in that text
        ↓
services/chunking_service.py → splits each page into ~500-character overlapping pieces
        ↓
services/embedding_service.py → turns each piece into a 384-number vector (a "meaning fingerprint")
        ↓
services/upload_service.py   → saves the file to disk (uploads/) and saves
                                the Document + Chunk rows to Postgres
        ↓
Response sent back to the user (doc_id, filename, size...)
```

## File-by-file, in order

1. **`routers/upload.py`** — the `/upload` API endpoint. Just receives the file and calls `upload_service`.
2. **`services/upload_service.py`** — the conductor. Calls every step in order and saves the results.
3. **`services/pdf_service.py`** — reads the PDF and extracts plain text, one page at a time. Rejects the file (with an error) if it's a scanned PDF with no real text in it.
4. **`utils/text_cleaning.py`** — tidies up that raw text (removes extra spaces/line breaks).
5. **`services/chunking_service.py`** — breaks the cleaned text into small overlapping pieces ("chunks") small enough for an embedding model to handle.
6. **`services/embedding_service.py`** — feeds each chunk through a local AI model (`all-MiniLM-L6-v2`) that converts text into a list of numbers (a vector) representing its meaning.
7. **`models.py`** — defines what a `Document` (the uploaded file) and a `Chunk` (a piece of it) look like as database rows.
8. **Postgres** — stores the `Document` row and all its `Chunk` rows, linked by `document_id`.

## What's missing (next step)

The vectors from step 6 are generated but **not stored anywhere yet** — they're only printed to the log. The next piece is pushing them into **Qdrant** so a question can later be matched against them (semantic search).
