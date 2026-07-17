#!/usr/bin/env python3
"""
Build-time script: pre-downloads the sentence-transformers model
so it's cached in the container image (avoids cold-start download).

Run automatically during Render build via build command.
"""
import os

def preload_model():
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    print(f"Pre-loading embedding model: {model_name}")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
        dim = model.get_sentence_embedding_dimension() if hasattr(model, 'get_sentence_embedding_dimension') else model.get_embedding_dimension()
        print(f"Model loaded OK — dim={dim}")
    except Exception as e:
        print(f"Warning: Could not preload model: {e}")

if __name__ == "__main__":
    preload_model()
