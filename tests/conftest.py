import os

os.environ["OPENAI_API_KEY"] = "your-gemini-api-key-here"
os.environ["QDRANT_URL"] = "http://127.0.0.1:65534"
os.environ["QDRANT_HOST"] = "127.0.0.1"
os.environ["QDRANT_PORT"] = "65534"
os.environ["QDRANT_COLLECTION"] = "legal_chunks_gemini_embedding_001_v1"
os.environ["QDRANT_API_KEY"] = ""
os.environ["EMBEDDING_DIMENSION"] = "768"
os.environ["EMBEDDING_API_KEY"] = "your-gemini-api-key-here"
os.environ["API_KEY"] = ""
os.environ["ENVIRONMENT"] = "development"
