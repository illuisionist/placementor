import sys
sys.path.insert(0, '.')
from config import settings
from google import genai
from google.genai import types

client = genai.Client(api_key=settings.GOOGLE_API_KEY)

# Test gemini-embedding-001 with 768-dim output
result = client.models.embed_content(
    model="models/gemini-embedding-001",
    contents="PlaceMentor AI test embedding",
    config=types.EmbedContentConfig(
        task_type="RETRIEVAL_DOCUMENT",
        output_dimensionality=768,
    ),
)
dim = len(result.embeddings[0].values)
print(f"gemini-embedding-001 OK — dim: {dim}")
print("Ready to seed!" if dim == 768 else f"Got dim={dim}")
