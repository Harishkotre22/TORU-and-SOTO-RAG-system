from typing import List, Dict
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch


class RAGGenerator:
    def __init__(self, model_name: str = "google/flan-t5-base"):

        print("Loading local generator model...")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

        self.model.eval()

    # -----------------------------
    # CLEAN + COMPRESSED PROMPT
    # -----------------------------
    def build_prompt(self, question: str, chunks: List[Dict]) -> str:

        context_blocks = []

        for i, c in enumerate(chunks, 1):

            text = c.get("text", "").replace("\n", " ").strip()

            context_blocks.append(
                f"[{i}] {c.get('section', 'unknown')} :: {text}"
            )

        context = "\n".join(context_blocks)

        prompt = f"""
You are a strict question answering system.

IMPORTANT RULES:
- Do NOT say "not enough information" if relevant information exists in ANY chunk.
- Even if the wording is different, match concepts semantically.
- Prefer the most relevant chunk(s); ignore irrelevant chunks.
- If multiple chunks contain partial information, combine them.
- If still nothing is relevant, then say: "Not found in the provided context."
- Do not hallucinate beyond the context.

ANSWER STYLE:
- Direct and clear definition if asked "what is..."
- Use 2–5 sentences maximum
- Preserve technical terms as they are
- No repetition of chunks

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""
        return prompt.strip()

    # -----------------------------
    # GENERATION (FIXED)
    # -----------------------------
    def generate(self, question: str, chunks: List[Dict]) -> str:

        prompt = self.build_prompt(question, chunks)

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=450   # critical fix (prevents 512 overflow)
        )

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=180,
                do_sample=False,
                num_beams=4
            )

        output = self.tokenizer.decode(
            output_ids[0],
            skip_special_tokens=True
        )

        # safety cleanup (rare but useful)
        output = output.replace(prompt, "").strip()

        if not output:
            return "Not enough information in retrieved context."

        return output