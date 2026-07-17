"""
Vector store — Pinecone serverless (replaces ChromaDB).

Uses sentence-transformers (all-MiniLM-L6-v2, 384-dim) for embeddings.
Each knowledge category is stored in a separate Pinecone namespace.
"""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import List, Dict, Any

from loguru import logger

# ─── Lazy imports (heavy models loaded only on first use) ─────────────────────

@lru_cache(maxsize=1)
def _get_embedding_model():
    # fastembed: ONNX-based, no PyTorch, ~80MB download (vs 2GB for torch)
    from fastembed import TextEmbedding
    from config import settings
    model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    logger.info(f"Embedding model loaded via fastembed: {settings.EMBEDDING_MODEL}")
    return model


@lru_cache(maxsize=1)
def _get_pinecone_index():
    from pinecone import Pinecone, ServerlessSpec
    from config import settings

    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    index_name = settings.PINECONE_INDEX

    existing_names = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing_names:
        logger.info(f"Creating Pinecone index '{index_name}' (dim=384, cosine)...")
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        logger.success(f"Index '{index_name}' created.")
    else:
        logger.info(f"Using existing Pinecone index: '{index_name}'")

    return pc.Index(index_name)


# ─── Namespace mapping (replaces ChromaDB collections) ───────────────────────

NAMESPACE_MAP: Dict[str, str] = {
    "general":               "general",
    "company_profiles":      "company_profiles",
    "core_subjects":         "core_subjects",
    "interview_experiences": "interview_experiences",
}


def _resolve_namespace(collection: str) -> str:
    return NAMESPACE_MAP.get(collection, "general")


# ─── Public API ───────────────────────────────────────────────────────────────

def embed(text: str) -> List[float]:
    """Embed a single string → 384-dim float list using fastembed (ONNX)."""
    model = _get_embedding_model()
    # fastembed returns a generator; convert to list and take first result
    embeddings = list(model.embed([text]))
    return embeddings[0].tolist()


def upsert_chunks(
    chunks: List[str],
    metadatas: List[Dict[str, Any]],
    namespace: str = "general",
) -> int:
    """
    Embed and upsert chunks into Pinecone.
    Returns number of vectors upserted.
    """
    index = _get_pinecone_index()
    ns = _resolve_namespace(namespace)

    vectors = []
    for chunk, meta in zip(chunks, metadatas):
        vec_id = meta.get("id") or str(uuid.uuid4())
        embedding = embed(chunk)
        vectors.append({
            "id":     vec_id,
            "values": embedding,
            "metadata": {**meta, "text": chunk[:2000]},  # Pinecone metadata limit
        })

    # Batch upsert (Pinecone recommends ≤ 100 per batch)
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        index.upsert(vectors=vectors[i : i + batch_size], namespace=ns)

    logger.debug(f"Upserted {len(vectors)} vectors → namespace '{ns}'")
    return len(vectors)


def query_collection(
    query_text: str,
    namespace: str = "general",
    top_k: int = 5,
    score_threshold: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    Query Pinecone for similar chunks.
    Returns list of {text, score, metadata} dicts.
    """
    index = _get_pinecone_index()
    ns = _resolve_namespace(namespace)

    query_emb = embed(query_text)
    results = index.query(
        vector=query_emb,
        top_k=top_k,
        namespace=ns,
        include_metadata=True,
    )

    hits = []
    for match in results.matches:
        if match.score >= score_threshold:
            hits.append({
                "text":     match.metadata.get("text", ""),
                "score":    round(match.score, 4),
                "source":   match.metadata.get("source", ""),
                "metadata": match.metadata,
            })

    return hits


def query_all_namespaces(
    query_text: str,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Query across all namespaces and merge results."""
    all_results = []
    for ns in NAMESPACE_MAP.values():
        hits = query_collection(query_text, namespace=ns, top_k=top_k)
        all_results.extend(hits)

    # Sort by score descending
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:top_k * 2]


def delete_namespace(namespace: str) -> None:
    """Delete all vectors in a namespace (for re-seeding)."""
    index = _get_pinecone_index()
    ns = _resolve_namespace(namespace)
    index.delete(delete_all=True, namespace=ns)
    logger.info(f"Deleted all vectors in namespace '{ns}'")


def get_index_stats() -> Dict[str, Any]:
    """Return index statistics."""
    index = _get_pinecone_index()
    return index.describe_index_stats()
