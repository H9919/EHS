import numpy as np
from typing import Dict, List
from .embeddings import embed_query, cosine_sim

def answer_question_for_sds(rec: Dict, question: str) -> str:
    chunks: List[str] = rec.get("chunks", [])
    embs = rec.get("embeddings", [])
    if not chunks:
        return "I couldn't find content for this SDS."

    if embs and question.strip():
        try:
            qv = embed_query(question)
            # compute similarity to each chunk
            best_idx = -1
            best_score = -1.0
            for i, ev in enumerate(embs):
                ev = np.asarray(ev, dtype="float32")
                score = cosine_sim(qv, ev)
                if score > best_score:
                    best_score, best_idx = score, i
            if best_idx >= 0:
                ans = chunks[best_idx]
                return (ans[:1500] + " …") if len(ans) > 1500 else ans
        except Exception:
            pass

    # fallback
    # return first chunk to avoid empty responses
    ans = chunks[0]
    return (ans[:1500] + " …") if len(ans) > 1500 else ans
