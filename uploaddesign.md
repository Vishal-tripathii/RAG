# RAG Document Ingestion Pipeline

> **Principle:** Uploading a document and indexing it for RAG are two different responsibilities. Never perform parsing, chunking, and embedding during the upload request.

---

# High-Level Architecture

```text
                    Upload Flow

User
 │
 ▼
Frontend
 │
 ▼
S3 Bucket
 │
 ▼
Backend API
 │
 ├── Save document metadata
 ├── Create processing job
 └── Return response immediately
             │
             ▼
      Background Worker
             │
             ▼
 Parse → Clean → Chunk → Embed → Vector DB
             │
             ▼
      Update document status
```

---

# Why This Architecture?

❌ **Bad**

```
Upload
 ↓
Parse
 ↓
Chunk
 ↓
Embed
 ↓
Store
 ↓
Return Response
```

Problems:

- Upload request becomes slow.
- User waits several seconds or minutes.
- API timeouts become likely.
- Difficult to retry failures.
- Backend resources stay occupied.

---

✅ **Good**

```
Upload
 ↓
Return Success (200)

↓

Queue Processing Job

↓

Background Worker

↓

Index Document
```

Advantages:

- Fast API response
- Better scalability
- Easier retries
- Independent workers
- Parallel processing
- Easier monitoring

---

# Step 1 — Upload Document

Upload the original file to object storage (S3, MinIO, Azure Blob, GCS).

Store only metadata in the database.

Example:

```text
documents
---------
id
tenantId
userId
fileName
mimeType
size
storageKey
status
createdAt
```

Initial status:

```
UPLOADED
```

Return immediately:

```json
{
  "documentId": "doc_123",
  "status": "UPLOADED"
}
```

---

# Step 2 — Create Processing Job

Immediately enqueue a background job.

Possible technologies:

- BullMQ + Redis
- RabbitMQ
- Kafka
- AWS SQS
- Database-backed queue

The upload endpoint should never perform parsing or embedding.

---

# Step 3 — Worker Downloads File

The worker retrieves the file from storage.

```
S3
 ↓
Worker
```

The backend API is no longer involved.

---

# Step 4 — Parse Document

Choose parser based on MIME type.

Examples:

| Type | Parser |
|-------|---------|
| PDF | pdfplumber, pymupdf |
| DOCX | python-docx |
| PPTX | python-pptx |
| XLSX | openpyxl |
| TXT | Native |
| Markdown | Native |
| HTML | BeautifulSoup |

Extract:

- Text
- Page numbers
- Headings
- Tables
- Images (optional)
- Metadata

---

# Step 5 — Clean Text

Normalize extracted text.

Typical cleanup:

- Remove duplicate whitespace
- Remove page headers
- Remove page footers
- Remove repeated page numbers
- Fix broken line wrapping
- Normalize Unicode
- Preserve headings

---

# Step 6 — Chunk

Do **not** chunk using fixed character counts alone.

Bad:

```
1000 chars
1000 chars
1000 chars
```

Good:

```
Chapter

↓

Section

↓

Paragraph Group

↓

Chunk
```

A chunk should represent one meaningful idea.

Recommended metadata:

```
chunkId
documentId
tenantId
pageNumber
section
chunkIndex
text
```

---

# Step 7 — Generate Embeddings

For every chunk:

```
Chunk

↓

Embedding Model

↓

Vector
```

Store the embedding model version.

Example:

```
text-embedding-3-small
```

or

```
BAAI/bge-small
```

---

# Step 8 — Store in Vector Database

Store both vector and metadata.

Example:

```json
{
  "id": "chunk_42",
  "vector": [...],
  "metadata": {
    "tenantId": "tenantA",
    "documentId": "doc123",
    "page": 12,
    "section": "Architecture",
    "chunkIndex": 42,
    "fileName": "system-design.pdf"
  }
}
```

Metadata is critical for:

- Filtering
- Citations
- Multi-tenancy
- Deletion
- Auditing

---

# Step 9 — Update Status

Successful:

```
READY
```

Failure:

```
FAILED
```

Track:

```
processedAt
retryCount
errorMessage
workerVersion
embeddingVersion
```

---

# Recommended Database Design

## Documents

```text
documents
---------
id
tenantId
storageKey
status
mimeType
size
uploadedAt
processedAt
```

---

## Chunks

```text
chunks
------
id
documentId
page
section
chunkIndex
text
```

---

## Processing Jobs

```text
processing_jobs
---------------
id
documentId
status
retryCount
startedAt
finishedAt
error
```

---

# Query Flow

When the user asks a question:

```
Question

↓

Embedding Model

↓

Vector Search

↓

Top K Chunks

↓

LLM

↓

Answer
```

The original document is **never parsed again**.

---

# Document Lifecycle

```
UPLOADED

↓

PROCESSING

↓

READY
```

Failure path:

```
PROCESSING

↓

FAILED
```

Optional:

```
READY

↓

REINDEXING

↓

READY
```

---

# Production Best Practices

## 1. Separate Upload and Indexing

Never block uploads while generating embeddings.

---

## 2. Keep Original Files

Always retain the original file in object storage.

Never treat extracted text as the source of truth.

---

## 3. Use Background Workers

Parsing and embedding are CPU-intensive.

Run them outside the API server.

---

## 4. Store Rich Metadata

Every vector should include:

- tenantId
- documentId
- page
- section
- chunkIndex
- fileName

---

## 5. Make Processing Idempotent

Reprocessing a document should replace or version existing vectors instead of creating duplicates.

---

## 6. Version Everything

Track:

- embedding model
- parser version
- chunking strategy
- worker version

This enables safe re-indexing after upgrades.

---

## 7. Retry Failures

Retry transient errors automatically.

Example:

```
Attempt 1

↓

Attempt 2

↓

Attempt 3

↓

FAILED
```

---

## 8. Support Re-indexing

When:

- embedding model changes
- chunk strategy changes
- parser improves

Re-index the document without requiring users to upload again.

---

## 9. Multi-Tenant Isolation

Every vector should contain:

```
tenantId
```

Always filter vector searches by tenant.

Never rely solely on similarity search.

---

## 10. Monitor the Pipeline

Track:

- Queue length
- Processing latency
- Parsing failures
- Embedding failures
- Average chunk count
- Average embedding cost
- Worker throughput

---

# Complete Production Pipeline

```
User
 │
 ▼
Frontend
 │
 ▼
S3
 │
 ▼
Backend API
 │
 ├── Save metadata
 ├── Create processing job
 └── Return immediately
             │
             ▼
      Background Worker
             │
             ▼
     Download from S3
             │
             ▼
      Parse Document
             │
             ▼
       Clean Content
             │
             ▼
      Semantic Chunking
             │
             ▼
    Generate Embeddings
             │
             ▼
      Store in Vector DB
             │
             ▼
     Update Document Status
             │
             ▼
            READY
```

---

# Golden Rule

> **Think of RAG as a _Document Ingestion Pipeline_, not a file upload feature.**

A production-grade ingestion pipeline should always follow:

```
Upload
    ↓
Validate
    ↓
Store Original
    ↓
Create Processing Job
    ↓
Parse
    ↓
Clean
    ↓
Semantic Chunk
    ↓
Generate Embeddings
    ↓
Index in Vector DB
    ↓
Mark READY
```

This architecture is scalable, fault-tolerant, and suitable for systems ranging from a single-user application to enterprise-scale RAG platforms