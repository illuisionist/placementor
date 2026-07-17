"""
Vector store — Pinecone serverless with Google text-embedding-004.

Uses Google's Generative AI embedding API (768-dim) — fully remote,
zero local model RAM. Free tier: 1500 requests/day.

Each knowledge category is stored in a separate Pinecone namespace.
"""

from __future__ import annotations

import uuid
import time
from functools import lru_cache
from typing import List, Dict, Any

from loguru import logger


# ─── Google Embedding API (no local model, no RAM cost) ──────────────────────

EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIM   = 768   # output_dimensionality we request


def _make_client():
    """Create a google-genai client (lightweight, no local model)."""
    from google import genai
    from config import settings
    return genai.Client(api_key=settings.GOOGLE_API_KEY)


def embed(text: str) -> List[float]:
    """
    Embed text using Gemini embedding API (768-dim).
    Fully remote — zero local RAM usage.
    """
    from google.genai import types
    client = _make_client()
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIM,
        ),
    )
    return list(result.embeddings[0].values)


def embed_query(text: str) -> List[float]:
    """Embed a search query (uses RETRIEVAL_QUERY task type)."""
    from google.genai import types
    client = _make_client()
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIM,
        ),
    )
    return list(result.embeddings[0].values)



# ─── Pinecone Index (768-dim to match Google embeddings) ─────────────────────

EMBEDDING_DIM = 768   # Google text-embedding-004


@lru_cache(maxsize=1)
def _get_pinecone_index():
    from pinecone import Pinecone, ServerlessSpec
    from config import settings

    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    index_name = settings.PINECONE_INDEX

    existing = {idx.name: idx for idx in pc.list_indexes()}
    if index_name not in existing:
        logger.info(f"Creating Pinecone index '{index_name}' (dim={EMBEDDING_DIM}, cosine)...")
        pc.create_index(
            name=index_name,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        # Wait for readiness
        for _ in range(60):
            if pc.describe_index(index_name).status.get("ready"):
                logger.success(f"Index '{index_name}' ready!")
                break
            time.sleep(2)
        else:
            raise TimeoutError(f"Pinecone index '{index_name}' not ready after 120s")
    else:
        # Check dimension matches — warn if not
        dim = existing[index_name].dimension
        if dim != EMBEDDING_DIM:
            logger.warning(
                f"Index '{index_name}' has dim={dim} but we need {EMBEDDING_DIM}. "
                f"Delete and recreate the index in Pinecone dashboard!"
            )
        logger.info(f"Using existing Pinecone index: '{index_name}' (dim={dim})")

    return pc.Index(index_name)


# ─── Namespace mapping ────────────────────────────────────────────────────────

NAMESPACE_MAP: Dict[str, str] = {
    "general":               "general",
    "company_profiles":      "company_profiles",
    "core_subjects":         "core_subjects",
    "interview_experiences": "interview_experiences",
}


def _resolve_namespace(collection: str) -> str:
    return NAMESPACE_MAP.get(collection, "general")


# ─── Public API ───────────────────────────────────────────────────────────────

def upsert_chunks(
    chunks: List[str],
    metadatas: List[Dict[str, Any]],
    namespace: str = "general",
) -> int:
    """
    Embed (via Google API) and upsert chunks into Pinecone.
    Returns number of vectors upserted.
    """
    index = _get_pinecone_index()
    ns = _resolve_namespace(namespace)

    vectors = []
    for i, (chunk, meta) in enumerate(zip(chunks, metadatas)):
        vec_id = meta.get("id") or str(uuid.uuid4())
        try:
            embedding = embed(chunk)
            vectors.append({
                "id":       vec_id,
                "values":   embedding,
                "metadata": {**meta, "text": chunk[:2000]},
            })
            # Rate limit: ~1500 req/day free tier → small delay between calls
            if i > 0 and i % 10 == 0:
                time.sleep(0.5)
        except Exception as e:
            logger.warning(f"Skipping chunk {i} (embed error): {e}")

    # Batch upsert (Pinecone recommends ≤ 100 per batch)
    batch_size = 50
    for i in range(0, len(vectors), batch_size):
        index.upsert(vectors=vectors[i: i + batch_size], namespace=ns)

    logger.debug(f"Upserted {len(vectors)} vectors → namespace '{ns}'")
    return len(vectors)


def query_collection(
    query_text: str,
    namespace: str = "general",
    top_k: int = 5,
    score_threshold: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    Query Pinecone for semantically similar chunks.
    Returns list of {text, score, source, metadata} dicts.
    """
    index = _get_pinecone_index()
    ns = _resolve_namespace(namespace)

    query_emb = embed_query(query_text)
    results = index.query(
        vector=query_emb,
        top_k=top_k,
        namespace=ns,
        include_metadata=True,
    )

    return [
        {
            "text":     match.metadata.get("text", ""),
            "score":    round(match.score, 4),
            "source":   match.metadata.get("source_file", match.metadata.get("source", "KB")),
            "metadata": match.metadata,
        }
        for match in results.matches
        if match.score >= score_threshold
    ]


def query_all_namespaces(
    query_text: str,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Query across all namespaces and return merged, re-ranked results."""
    all_results = []
    for ns in NAMESPACE_MAP.values():
        all_results.extend(query_collection(query_text, namespace=ns, top_k=top_k))
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[: top_k * 2]


def delete_namespace(namespace: str) -> None:
    """Delete all vectors in a namespace (for re-seeding)."""
    index = _get_pinecone_index()
    index.delete(delete_all=True, namespace=_resolve_namespace(namespace))
    logger.info(f"Deleted all vectors in namespace '{namespace}'")


def get_index_stats() -> Dict[str, Any]:
    """Return Pinecone index statistics."""
    return _get_pinecone_index().describe_index_stats()
