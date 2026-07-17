"""
Seed script — loads all knowledge base documents into ChromaDB.
Run from backend/ directory: python seed_knowledge_base.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.ingestor import ingest_directory, ingest_file
from loguru import logger

KB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")

COLLECTION_MAP = {
    "companies": "company_profiles",
    "core_subjects": "core_subjects",
    "interview_experiences": "interview_experiences",
}

def seed():
    logger.info(f"Seeding knowledge base from: {KB_DIR}")
    total = 0

    # Root-level .md files → general collection
    for fname in sorted(os.listdir(KB_DIR)):
        fpath = os.path.join(KB_DIR, fname)
        if os.path.isfile(fpath) and fname.endswith(".md"):
            try:
                n = ingest_file(fpath, "general")
                total += n
                logger.success(f"  {fname} → general ({n} chunks)")
            except Exception as e:
                logger.error(f"  Failed {fname}: {e}")

    # Sub-directories → specific collections
    for subdir, collection in COLLECTION_MAP.items():
        dir_path = os.path.join(KB_DIR, subdir)
        if os.path.exists(dir_path):
            result = ingest_directory(dir_path, collection)
            total += result["total_chunks"]
            logger.success(f"  {subdir}/ → {collection} ({result['total_chunks']} chunks, {result['files_processed']} files)")
        else:
            logger.warning(f"  Directory not found: {dir_path}")

    logger.success(f"\nDone! Total chunks ingested: {total}")
    return total

if __name__ == "__main__":
    seed()
