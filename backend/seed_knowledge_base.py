"""
Memory-efficient seed script — processes one file at a time,
forces garbage collection between each to avoid MemoryError.

Run from backend/ directory: python seed_knowledge_base.py
"""
import sys
import os
import gc
import traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

KB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")

COLLECTION_MAP = {
    "companies":             "company_profiles",
    "core_subjects":         "core_subjects",
    "interview_experiences": "interview_experiences",
}


def ingest_one(fpath: str, collection: str) -> int:
    """Ingest a single file in isolation, then GC."""
    from rag.ingestor import load_document
    from rag.vector_store import upsert_chunks
    import uuid, hashlib

    text = load_document(fpath)
    if not text or not text.strip():
        return 0

    # Small chunks to reduce peak memory
    chunk_size = 600
    overlap    = 100
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if end < len(text):
            for sep in ["\n\n", "\n", ". ", " "]:
                idx = chunk.rfind(sep)
                if idx > chunk_size // 2:
                    chunk = chunk[: idx + len(sep)]
                    break
        if chunk.strip():
            chunks.append(chunk.strip())
        start += len(chunk) - overlap

    source = os.path.basename(fpath)
    fhash = hashlib.sha256(fpath.encode()).hexdigest()[:12]
    metas = [
        {"id": f"{fhash}-{i}", "source_file": source,
         "file_path": fpath, "chunk_index": i, "collection": collection}
        for i in range(len(chunks))
    ]

    n = upsert_chunks(chunks, metas, namespace=collection)
    del chunks, metas, text          # explicit free
    gc.collect()
    return n


def seed():
    logger.info(f"Seeding knowledge base from: {KB_DIR}")
    total = 0

    # ── Step 0: connect to Pinecone ──────────────────────────────────────────
    logger.info("Connecting to Pinecone...")
    try:
        from rag.vector_store import _get_pinecone_index, get_index_stats
        _get_pinecone_index()
        stats = get_index_stats()
        logger.success(f"Pinecone ready — current vectors: {stats.get('total_vector_count', 0)}")
    except Exception:
        logger.error(f"Cannot connect to Pinecone:\n{traceback.format_exc()}")
        return 0

    # ── Step 1: root-level .md → general ─────────────────────────────────────
    logger.info("Ingesting root-level files → general namespace...")
    for fname in sorted(os.listdir(KB_DIR)):
        fpath = os.path.join(KB_DIR, fname)
        if os.path.isfile(fpath) and fname.endswith(".md"):
            try:
                n = ingest_one(fpath, "general")
                total += n
                logger.success(f"  ✓ {fname} ({n} chunks)")
            except MemoryError:
                logger.error(f"  ✗ {fname}: OUT OF MEMORY — skip and continue")
                gc.collect()
            except Exception:
                logger.error(f"  ✗ {fname}:\n{traceback.format_exc()}")

    # ── Step 2: sub-directories ───────────────────────────────────────────────
    for subdir, collection in COLLECTION_MAP.items():
        dir_path = os.path.join(KB_DIR, subdir)
        if not os.path.exists(dir_path):
            logger.warning(f"  Directory not found: {dir_path}")
            continue

        logger.info(f"Ingesting {subdir}/ → {collection}...")
        from pathlib import Path
        for fpath in sorted(Path(dir_path).rglob("*.md")):
            try:
                n = ingest_one(str(fpath), collection)
                total += n
                logger.success(f"  ✓ {fpath.name} ({n} chunks)")
            except MemoryError:
                logger.error(f"  ✗ {fpath.name}: OUT OF MEMORY — skip")
                gc.collect()
            except Exception:
                logger.error(f"  ✗ {fpath.name}:\n{traceback.format_exc()}")

    # ── Final stats ───────────────────────────────────────────────────────────
    try:
        from rag.vector_store import get_index_stats
        final = get_index_stats()
        logger.success(f"\n✅ Done! Chunks this run: {total}")
        logger.success(f"✅ Total vectors in Pinecone: {final.get('total_vector_count', '?')}")
    except Exception:
        logger.success(f"\n✅ Done! Total chunks: {total}")

    return total


if __name__ == "__main__":
    seed()
