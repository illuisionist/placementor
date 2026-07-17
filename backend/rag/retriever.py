"""
RAG Retriever — wraps ChromaDB native collection with ranking and citation.

Uses chromadb collection.query() directly (no LangChain Chroma wrapper).
Works with DefaultEmbeddingFunction (ONNX, no PyTorch).
"""

from typing import Optional
from loguru import logger

from config import settings
from rag.vector_store import get_collection


class RAGRetriever:
    """Retriever backed by a specific ChromaDB collection."""

    def __init__(self, collection_name: str = "general", top_k: int = None):
        self.collection_name = collection_name
        self.top_k = top_k or settings.RETRIEVAL_TOP_K

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[dict] = None,
    ) -> list[dict]:
        """
        Retrieve relevant document chunks via cosine similarity.

        Returns:
            List of dicts: {content, source, score, metadata}
        """
        k = top_k or self.top_k
        try:
            collection = get_collection(self.collection_name)
            results = collection.query(
                query_texts=[query],
                n_results=min(k, collection.count() or 1),
                where=filter_metadata,
                include=["documents", "metadatas", "distances"],
            )

            docs      = results["documents"][0] if results["documents"] else []
            metas     = results["metadatas"][0] if results["metadatas"] else []
            distances = results["distances"][0]  if results["distances"] else []

            # Convert cosine distance → similarity score (1 - distance)
            output = []
            for doc, meta, dist in zip(docs, metas, distances):
                output.append({
                    "content":  doc,
                    "source":   meta.get("source_file", "unknown"),
                    "score":    round(1 - dist, 4),
                    "metadata": meta,
                })

            logger.debug(f"[Retriever] {len(output)} chunks for: {query[:60]}...")
            return output

        except Exception as e:
            logger.error(f"[Retriever] Failed for '{query[:60]}': {e}")
            return []

    def format_context(self, results: list[dict]) -> str:
        """Format retrieved chunks into a single LLM-ready context string."""
        if not results:
            return "No relevant information found in the knowledge base."

        parts = []
        for i, r in enumerate(results, 1):
            parts.append(
                f"[Source {i}: {r['source']} | relevance: {r['score']:.2f}]\n{r['content']}"
            )
        return "\n\n---\n\n".join(parts)

    def retrieve_formatted(
        self, query: str, top_k: Optional[int] = None
    ) -> tuple[str, list[dict]]:
        """Returns (formatted_context_string, raw_results_list)."""
        results = self.retrieve(query, top_k=top_k)
        return self.format_context(results), results


class MultiCollectionRetriever:
    """Retrieve from multiple collections and merge by score."""

    def __init__(self, collections: list[str] = None, top_k_per_collection: int = 3):
        self.collections = collections or ["general", "placement_policies", "company_jds"]
        self.top_k_per_collection = top_k_per_collection

    def retrieve(self, query: str) -> list[dict]:
        all_results = []
        for col in self.collections:
            retriever = RAGRetriever(collection_name=col, top_k=self.top_k_per_collection)
            for r in retriever.retrieve(query):
                r["collection"] = col
                all_results.append(r)

        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results


# ─── Convenience Functions ────────────────────────────────────────────────────

def retrieve_for_company(company: str, role: str = "") -> list[dict]:
    query = f"{company} {role} interview process requirements skills".strip()
    jd  = RAGRetriever("company_jds").retrieve(query)
    exp = RAGRetriever("interview_experiences").retrieve(query)
    return jd + exp


def retrieve_learning_resources(topic: str, top_k: int = 5) -> list[dict]:
    return RAGRetriever("learning_resources", top_k=top_k).retrieve(topic)


def retrieve_placement_policy(query: str) -> list[dict]:
    return RAGRetriever("placement_policies").retrieve(query)
