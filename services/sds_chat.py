import re
from typing import Dict, List

# Dumb but effective local SDS “chat”: pick the chunk with the most keyword hits.
# You can replace this later with embeddings.

def _score_chunk(chunk: str, q: str) -> int:
    terms = [t for t in re.findall(r"\w+", q.lower()) if len(t) > 2]
    score = 0
    low = chunk.lower()
    for t in terms:
        score += low.count(t)
    return score

def answer_question_for_sds(rec: Dict, question: str) -> str:
    chunks: List[str] = rec.get("chunks", [])
    if not chunks:
        return "I couldn't find content for this SDS."
    best = max(chunks, key=lambda c: _score_chunk(c, question))
    # trim answer a bit
    if len(best) > 1200:
        return best[:1200] + " …"
    return best
