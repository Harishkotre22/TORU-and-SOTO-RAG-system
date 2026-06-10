import json
import numpy as np
from typing import Dict, List
from sentence_transformers import SentenceTransformer
from .config import TOP_K
from .ingest import load_index

# 🛡️ THE SECURITY GUARD THRESHOLD
# Semantic cosine similarity sits between -1.0 and 1.0. 
# A score below 0.40 means the document text is completely unrelated to the question.
SIMILARITY_THRESHOLD = 0.40

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculates the alignment between two dense AI embedding vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))


def retrieve(question: str, top_k: int = TOP_K) -> List[Dict[str, object]]:
    index_data = load_index()
    documents = index_data.get("documents", [])
    if not documents:
        return []

    # Vectorize the incoming live question using the exact same transformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_vector = model.encode(question).tolist()

    scored_documents = []
    for doc in documents:
        score = cosine_similarity(query_vector, doc.get("vector", []))
        
        # STRICT RULE: Drop the chunk completely if it falls below our threshold
        if score >= SIMILARITY_THRESHOLD:
            scored_documents.append({
                "id": doc.get("id"),
                "source": doc.get("source"),
                "text": doc.get("text"),
                "score": score,
            })

    # Sort with the best matching text blocks right at the top
    scored_documents.sort(key=lambda item: item["score"], reverse=True)
    return scored_documents[:top_k]