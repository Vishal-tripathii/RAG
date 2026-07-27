from fastembed import TextEmbedding

from src.models import Chunk

# Loaded once at import time (not per-request) since loading the model weights
# is the expensive part - reusing this instance keeps embedding calls fast.
# bge-small-en-v1.5 outputs 384-dim vectors - this must match the Qdrant
# collection's vector size, so changing the model later requires re-embedding
# everything.
model = TextEmbedding("BAAI/bge-small-en-v1.5")


def embed_chunks(chunks: list[Chunk]) -> list[list[float]]:
    texts = [chunk.text for chunk in chunks]
    # embed() is lazy - it returns a generator of numpy arrays, so this has to
    # be materialised before the vectors can be handed to Qdrant.
    return [embedding.tolist() for embedding in model.embed(texts)]
