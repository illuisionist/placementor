"""
Build-time script: pre-downloads the fastembed ONNX model (~80MB)
so it's cached in the container image (avoids cold-start download).

Run during Render build: pip install -r requirements.txt && python preload_model.py
"""

def preload_model():
    print("Pre-loading fastembed ONNX embedding model (~80MB)...")
    try:
        from fastembed import TextEmbedding
        model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        # Force download by running one embed
        result = list(model.embed(["PlaceMentor AI preload test"]))
        print(f"Model loaded OK — embedding dim: {len(result[0])}")
    except Exception as e:
        print(f"Warning: Could not preload model: {e}")

if __name__ == "__main__":
    preload_model()
