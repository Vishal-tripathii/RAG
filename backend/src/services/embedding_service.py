from sentence_transformers import SentenceTransformer

from src.models import Chunk

# Loaded once at import time (not per-request) since loading the model weights
# is the expensive part - reusing this instance keeps embedding calls fast.
# all-MiniLM-L6-v2 outputs 384-dim vectors - this must match the Qdrant
# collection's vector size, so changing the model later requires re-embedding
# everything.
model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_chunks(chunks: list[Chunk]) -> list[list[float]]:
    texts = [chunk.text for chunk in chunks]
    embeddings = model.encode(texts)
    return embeddings.tolist()
