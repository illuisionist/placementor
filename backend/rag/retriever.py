"""
RAG Retriever — wraps Pinecone vector store with ranking and citation.

Thin compatibility layer so all agents can keep using retrieve() calls.
All heavy lifting done by rag.vector_store (Pinecone + sentence-transformers).
"""

from typing import Optional
from loguru import logger
from rag.vector_store import query_collection, query_all_namespaces


class RAGRetriever:
    """Retriever backed by a specific Pinecone namespace."""

    def __init__(self, collection_name: str = "general", top_k: int = 5):
        self.namespace = collection_name
        self.top_k = top_k

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        use_mmr: bool = False,          # kept for API compat, ignored
        filter_metadata: Optional[dict] = None,
    ) -> list[dict]:
        """
        Retrieve relevant document chunks via Pinecone cosine similarity.

        Returns:
            List of dicts: {content, source, score, metadata}
        """
        k = top_k or self.top_k
        try:
            results = query_collection(self.namespace, query, top_k=k)
            # Normalise to {content, source, score, metadata} for backward compat
            return [
                {
                    "content":  r["text"],
                    "source":   r.get("source", r.get("metadata", {}).get("source_file", "KB")),
                    "score":    r["score"],
                    "metadata": r.get("metadata", {}),
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"[Retriever] Failed for '{query[:60]}': {e}")
            return []

    def format_context(self, results: list[dict]) -> str:
        if not results:
            return "No relevant information found in the knowledge base."
        parts = [
            f"[Source {i}: {r['source']} | relevance: {r['score']:.2f}]\n{r['content']}"
            for i, r in enumerate(results, 1)
        ]
        return "\n\n---\n\n".join(parts)

    def retrieve_formatted(
        self, query: str, top_k: Optional[int] = None
    ) -> tuple[str, list[dict]]:
        results = self.retrieve(query, top_k=top_k)
        return self.format_context(results), results


class MultiCollectionRetriever:
    """Retrieve across all Pinecone namespaces and merge by score."""

    def __init__(self, collections: list[str] = None, top_k_per_collection: int = 3):
        self.collections = collections or ["general", "company_profiles", "core_subjects", "interview_experiences"]
        self.top_k_per_collection = top_k_per_collection

    def retrieve(self, query: str) -> list[dict]:
        all_results = query_all_namespaces(query, top_k=self.top_k_per_collection)
        return [
            {
                "content":  r["text"],
                "source":   r.get("source", "KB"),
                "score":    r["score"],
                "metadata": r.get("metadata", {}),
            }
            for r in all_results
        ]


# ─── Convenience Functions (kept for backward compatibility) ──────────────────

def retrieve_for_company(company: str, role: str = "") -> list[dict]:
    query = f"{company} {role} interview process requirements skills".strip()
    return RAGRetriever("company_profiles").retrieve(query)


def retrieve_learning_resources(topic: str, top_k: int = 5) -> list[dict]:
    return RAGRetriever("general", top_k=top_k).retrieve(topic)


def retrieve_placement_policy(query: str) -> list[dict]:
    return RAGRetriever("general").retrieve(query)
