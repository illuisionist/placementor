"""
Document ingestor — loads, chunks, and embeds documents into Pinecone.

Supports: PDF (.pdf), DOCX (.docx), TXT (.txt), Markdown (.md)

Usage:
    # From CLI
    python -m rag.ingestor --dir knowledge_base/ --collection general

    # From code
    from rag.ingestor import ingest_file, ingest_directory
    ingest_file("my_doc.pdf", collection_name="company_profiles")
"""

import os
import uuid
import hashlib
import argparse
from pathlib import Path

from loguru import logger
from config import settings
from rag.vector_store import upsert_chunks, NAMESPACE_MAP


# ─── Text Splitter ────────────────────────────────────────────────────────────

def split_text(text: str, chunk_size: int = None, overlap: int = None) -> list[str]:
    """Split text into overlapping chunks."""
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap    = overlap    or settings.CHUNK_OVERLAP

    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at a sentence or paragraph boundary
        if end < len(text):
            for sep in ["\n\n", "\n", ". ", " "]:
                idx = chunk.rfind(sep)
                if idx > chunk_size // 2:
                    chunk = chunk[: idx + len(sep)]
                    break

        if chunk.strip():
            chunks.append(chunk.strip())
        start += len(chunk) - overlap

    return chunks


# ─── Document Loaders ─────────────────────────────────────────────────────────

def load_pdf(file_path: str) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        return "\n\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception as e:
        logger.error(f"PDF load failed {file_path}: {e}")
        return ""


def load_docx(file_path: str) -> str:
    try:
        import docx2txt
        return docx2txt.process(file_path)
    except Exception as e:
        logger.error(f"DOCX load failed {file_path}: {e}")
        return ""


def load_text(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Text load failed {file_path}: {e}")
        return ""


def load_document(file_path: str) -> str:
    """Load a file and return raw text."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext == ".docx":
        return load_docx(file_path)
    elif ext in (".txt", ".md", ".csv"):
        return load_text(file_path)
    else:
        logger.warning(f"Unsupported file type: {ext} — skipping {file_path}")
        return ""


# ─── File Hash (deduplication) ───────────────────────────────────────────────

def compute_file_hash(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


# ─── Core Ingest ─────────────────────────────────────────────────────────────

def ingest_file(file_path: str, collection_name: str = "general") -> int:
    """
    Ingest a single file into a Pinecone namespace.
    Returns the number of chunks upserted.
    """
    logger.info(f"Ingesting: {file_path} → {collection_name}")

    text = load_document(file_path)
    if not text or not text.strip():
        logger.warning(f"No text extracted from {file_path}")
        return 0

    chunks = split_text(text)
    if not chunks:
        return 0

    file_hash = compute_file_hash(file_path)
    source_name = os.path.basename(file_path)

    metadatas = [
        {
            "id":           f"{file_hash}-{i}",
            "source_file":  source_name,
            "file_path":    file_path,
            "file_hash":    file_hash,
            "chunk_index":  i,
            "collection":   collection_name,
        }
        for i in range(len(chunks))
    ]

    n = upsert_chunks(chunks, metadatas, namespace=collection_name)
    logger.success(f"✓ {n} chunks from {source_name} → {collection_name}")
    return n


def ingest_directory(directory: str, collection_name: str = "general") -> dict:
    """Recursively ingest all supported files in a directory."""
    supported = {".pdf", ".docx", ".txt", ".md"}
    results = {"files_processed": 0, "total_chunks": 0, "errors": []}

    for root, _, files in os.walk(directory):
        for fname in sorted(files):
            if Path(fname).suffix.lower() in supported:
                fpath = os.path.join(root, fname)
                try:
                    n = ingest_file(fpath, collection_name)
                    results["total_chunks"] += n
                    results["files_processed"] += 1
                except Exception as e:
                    results["errors"].append({"file": fpath, "error": str(e)})
                    logger.error(f"Error on {fpath}: {e}")

    logger.info(
        f"Done: {results['files_processed']} files, "
        f"{results['total_chunks']} chunks, "
        f"{len(results['errors'])} errors"
    )
    return results


def ingest_text(text: str, metadata: dict, collection_name: str = "general") -> int:
    """Ingest raw text string directly (e.g. scraped data, resume text)."""
    chunks = split_text(text)
    metas  = [{**metadata, "id": str(uuid.uuid4()), "chunk_index": i} for i in range(len(chunks))]
    return upsert_chunks(chunks, metas, namespace=collection_name)


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PlaceMentor RAG Ingestor")
    parser.add_argument("--dir",  type=str, help="Directory to ingest")
    parser.add_argument("--file", type=str, help="Single file to ingest")
    parser.add_argument(
        "--collection",
        type=str,
        default="general",
        choices=list(NAMESPACE_MAP.keys()),
        help="Target Pinecone namespace",
    )
    args = parser.parse_args()

    if args.dir:
        print(ingest_directory(args.dir, args.collection))
    elif args.file:
        print(f"Ingested {ingest_file(args.file, args.collection)} chunks")
    else:
        parser.print_help()
