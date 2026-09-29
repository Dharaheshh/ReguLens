"""Local embedding generation - TASK-007 / CORRECTION-002.

Uses sentence-transformers/all-MiniLM-L6-v2 (384 dimensions).
Runs locally, no external API needed.
"""
from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the embedding model (loaded once, reused)."""
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def embed(text: str) -> list[float]:
    """Generate a 384-dimensional embedding for the given text.

    Args:
        text: The text to embed.

    Returns:
        A list of 384 floats (normalized embedding).
    """
    model = _get_model()
    return model.encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts.

    Args:
        texts: List of texts to embed.

    Returns:
        List of 384-dimensional embeddings.
    """
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return [e.tolist() for e in embeddings]
