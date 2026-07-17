"""
Build-time verification: checks that Google Gemini embedding API is reachable.
No model download needed — embeddings are fully remote.

Run during Render build: pip install -r requirements.txt && python preload_model.py
"""

def verify_embedding():
    print("Verifying Google Gemini embedding API connectivity...")
    try:
        import os
        from google import genai
        from google.genai import types

        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            print("Warning: GOOGLE_API_KEY not set — skipping embedding check")
            return

        client = genai.Client(api_key=api_key)
        result = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents="PlaceMentor build verification",
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=768,
            ),
        )
        dim = len(result.embeddings[0].values)
        print(f"Gemini embedding API OK — dim={dim}")
    except Exception as e:
        print(f"Warning: embedding check failed (will retry at runtime): {e}")

if __name__ == "__main__":
    verify_embedding()
