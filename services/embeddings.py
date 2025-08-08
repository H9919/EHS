from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer

@lru_cache(maxsize=1)
def get_model():
    # Compact, fast model
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_texts(texts):
    if not texts:
        return np.zeros((0, 384), dtype="float32")
    model = get_model()
    embs = model.encode(texts, normalize_embeddings=True)
    return np.asarray(embs, dtype="float32")

def embed_query(q: str):
    model = get_model()
    v = model.encode([q], normalize_embeddings=True)[0]
    return np.asarray(v, dtype="float32")

def cosine_sim(a: np.ndarray, b: np.ndarray):
    # expects normalized vectors
    return float(np.dot(a, b))
