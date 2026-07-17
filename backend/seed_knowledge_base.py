"""
Seed script — loads all knowledge base documents into Pinecone.
Run from backend/ directory: python seed_knowledge_base.py
"""
import sys
import os
import traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.ingestor import ingest_directory, ingest_file
from loguru import logger

KB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")

COLLECTION_MAP = {
    "companies":             "company_profiles",
    "core_subjects":         "core_subjects",
    "interview_experiences": "interview_experiences",
}

def seed():
    logger.info(f"Seeding knowledge base from: {KB_DIR}")
    total = 0

    # ── Step 0: verify Pinecone is reachable ──────────────────────────────────
    logger.info("Connecting to Pinecone (index will be created if it doesn't exist)...")
    try:
        from rag.vector_store import _get_pinecone_index, get_index_stats
        index = _get_pinecone_index()       # creates + waits if new
        stats = get_index_stats()
        logger.success(f"Pinecone ready. Current vectors: {stats.get('total_vector_count', 0)}")
    except Exception as e:
        logger.error(f"Cannot connect to Pinecone — aborting seed:\n{traceback.format_exc()}")
        return 0

    # ── Step 1: root-level .md → general namespace ────────────────────────────
    logger.info("Ingesting root-level KB files → general namespace...")
    for fname in sorted(os.listdir(KB_DIR)):
        fpath = os.path.join(KB_DIR, fname)
        if os.path.isfile(fpath) and fname.endswith(".md"):
            try:
                n = ingest_file(fpath, "general")
                total += n
                logger.success(f"  ✓ {fname} ({n} chunks)")
            except Exception as e:
                logger.error(f"  ✗ {fname}: {traceback.format_exc()}")

    # ── Step 2: sub-directories → specific namespaces ────────────────────────
    for subdir, collection in COLLECTION_MAP.items():
        dir_path = os.path.join(KB_DIR, subdir)
        if os.path.exists(dir_path):
            logger.info(f"Ingesting {subdir}/ → {collection} namespace...")
            try:
                result = ingest_directory(dir_path, collection)
                total += result["total_chunks"]
                logger.success(
                    f"  ✓ {subdir}/ → {collection} "
                    f"({result['total_chunks']} chunks, {result['files_processed']} files)"
                )
            except Exception as e:
                logger.error(f"  ✗ {subdir}/: {traceback.format_exc()}")
        else:
            logger.warning(f"  Directory not found: {dir_path}")

    # ── Final stats ───────────────────────────────────────────────────────────
    try:
        final_stats = get_index_stats()
        logger.success(f"\nDone! Chunks upserted this run: {total}")
        logger.success(f"Total vectors in Pinecone: {final_stats.get('total_vector_count', '?')}")
    except Exception:
        logger.success(f"\nDone! Total chunks ingested: {total}")

    return total

if __name__ == "__main__":
    seed()
