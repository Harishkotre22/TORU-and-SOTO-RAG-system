from typing import List
from .retriever import retrieve
from .generator import RAGGenerator

generator = RAGGenerator()


def answer_question(question: str, top_k: int = 5) -> str:

    hits = retrieve(question, top_k=top_k)

    if not hits:
        return "No relevant passages found. Try a different question."

    # =========================
    # STEP 1: PRINT TOP CHUNKS
    # =========================
    print("\n===== TOP 5 CHUNKS =====\n")

    for i, hit in enumerate(hits, 1):
        print(f"[Chunk {i}]")
        print(f"Source: {hit['source']} | Score: {hit['score']:.3f}")
        print(hit["text"])
        print("-" * 60)

    # =========================
    # STEP 2: GENERATE ANSWER
    # =========================
    answer = generator.generate(question, hits)

    # =========================
    # STEP 3: FINAL OUTPUT
    # =========================
    final_output = f"""

========================
FINAL ANSWER
========================

Your answer to this question is:

{answer}

"""

    return final_output