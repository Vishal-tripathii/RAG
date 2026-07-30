from google import genai
from google.genai import types

from src.config import settings

# gemini-2.5-flash still shows up in the API's own model listing but is
# blocked for newer API keys (404 "no longer available to new users"). This
# alias tracks whatever Google currently points it at, so it doesn't go stale
# the way a specific pinned version does.
MODEL_NAME = "gemini-flash-latest"

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    # Built lazily on first use, not at import time: genai.Client() validates
    # the key immediately, and validating it at import would crash the whole
    # app on startup if the key is missing - instead of failing one request
    # with a catchable error, the way a missing/bad key normally should.
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def build_prompt(query: str, chunks: list[dict]) -> dict:
    # Numbered so the model can cite by [n]; page number rather than filename
    # since search_chunks only carries document_id, not the original name.
    context_blocks = "\n\n".join(
        f"[{i}] (p.{chunk['page']}) {chunk['text']}"
        for i, chunk in enumerate(chunks, start=1)
    ) or "(no sources retrieved)"

    system = (
        "You are a question-answering assistant. Answer the question using ONLY "
        "the numbered sources below. Cite the sources you use with their number "
        "in square brackets, e.g. [1]. If the sources do not contain the answer, "
        "say so plainly instead of guessing."
    )

    user = f"Sources:\n{context_blocks}\n\nQuestion: {query}"

    return {"system": system, "user": user}


def call_llm(prompt: dict) -> str:
    response = _get_client().models.generate_content(
        model=MODEL_NAME,
        contents=prompt["user"],
        config=types.GenerateContentConfig(system_instruction=prompt["system"]),
    )
    return response.text
