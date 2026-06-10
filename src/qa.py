from typing import List

from .retriever import retrieve


def answer_question(question: str, top_k: int = 5) -> str:
    hits = retrieve(question, top_k=top_k)
    if not hits:
        return "No relevant passages found. Try a different question."

    lines: List[str] = [
        "Relevant passages found:",
    ]
    for hit in hits:
        lines.append(f"Source: {hit['source']} (score={hit['score']:.3f})")
        lines.append(hit["text"])
        lines.append("---")

    return "\n".join(lines)


def compose_prompt(question: str, top_k: int = 5) -> str:
    hits = retrieve(question, top_k=top_k)
    prompt_lines = [
        "Use the passages below to answer the question.",
        "",
    ]
    for hit in hits:
        prompt_lines.append(f"[{hit['source']}]:")
        prompt_lines.append(hit["text"])
        prompt_lines.append("")
    prompt_lines.append(f"Question: {question}")
    prompt_lines.append("Answer:")
    return "\n".join(prompt_lines)
