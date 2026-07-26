# RAG Project — Roadmap (this repo)

> Local roadmap for the `RAG/` project. Philosophy: **build v1 raw** (no service-layer abstractions,
> no LangChain) to learn the internals first. Full stack/architecture rationale lives in
> `../AI/rag-project-plan.md` — this file tracks actual progress against it.

---

## Current state

**Backend layout (`backend/src/`):**
```
backend/
├── .env                 # PORT=3000, QDRANT_HOST, QDRANT_PORT
├── requirements.txt
└── src/
    ├── __init__.py
    ├── main.py           # FastAPI() app, single "/" route, runs on port 3000
    └── config.py         # Settings (pydantic-settings), reads .env
```

**Qdrant:** running in Docker, bind-mounted to `RAG/qdrant_storage` so data survives container recreation.
```
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 -v "<path>\qdrant_storage:/qdrant/storage" qdrant/qdrant
```

**Decision:** no `services/`/`dependencies.py` abstraction layer yet — writing Qdrant calls directly where they're used until v1 works end-to-end.

**No frontend yet** — backend + Qdrant only, until ingestion + query work via curl/dashboard.

---

## Step-by-step (in order)

### Setup
- [x] Qdrant running in Docker with persistent volume
- [x] FastAPI skeleton (`main.py`, `config.py`, `.env`)
- [x] `qdrant-client` in `requirements.txt`
- [ ] Fix `requirements.txt` encoding (was saved as UTF-16 — re-run `pip freeze > requirements.txt`)
- [ ] Add remaining deps: `sentence-transformers`, `pypdf`, `langchain-text-splitters`, `python-multipart` (required for file upload), `pydantic-settings` (already used, confirm it's listed)
- [ ] Decide generation LLM for v1 (OpenAI `gpt-4o-mini` per original plan, or defer this step until retrieval works)
- [ ] Create the Qdrant collection **once**, directly in `main.py` (or a plain `qdrant.py` module — functions, not a class) — size=384 (MiniLM), `Distance.COSINE`

### Ingestion (`POST /upload`)
- [ ] Accept a file upload (start with PDF only)
- [ ] Parse **page-by-page** with `pypdf` — keep `(page_number, text)` pairs, don't flatten
- [ ] Guard against empty extraction (scanned PDF → clear 400 error, not silent empty store)
- [ ] Clean text (collapse whitespace)
- [ ] Chunk each page with `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)`, tag each chunk with its page + running `chunk_index`
- [ ] Embed all chunks in **one batched call**, `normalize_embeddings=True`
- [ ] Upsert to Qdrant — point ID = deterministic UUID from `(doc_id, chunk_index)`, payload = `{text, source, doc_id, page, chunk_index}`

### Query (`POST /chat` or `/search` for now)
- [ ] Embed the question — same model, same `normalize_embeddings=True`
- [ ] `query_points` → top-K (start K=3)
- [ ] Build a grounded prompt with numbered `[source p.N]` context blocks
- [ ] Call the LLM, `temperature=0`
- [ ] Return answer + raw source list (for citations later)

### Once ingestion + query work end-to-end via curl/dashboard
- [ ] Revisit whether a `services/` layer earns its keep (multiple routes reusing the same Qdrant/embedding calls is the trigger, not "just in case")
- [ ] Start frontend (React/Vite) — chat + upload UI

---

## Gotchas checklist (carried over — verify each as you build)
- [ ] Collection created with `Distance.COSINE`, `size=384`
- [ ] `normalize_embeddings=True` on both ingest and query
- [ ] Same embedding model both sides
- [ ] Chunks tagged with page (parsed page-by-page)
- [ ] Point IDs are deterministic UUIDs, not `c1/c2`
- [ ] Empty-extraction guard in place
- [ ] `python-multipart` installed (upload 500s without it)
- [ ] `chunk_size=500` = characters, stays under MiniLM's 256-token cap

---

_Full stack rationale, architecture diagram, and future-scope notes: `../AI/rag-project-plan.md`._
