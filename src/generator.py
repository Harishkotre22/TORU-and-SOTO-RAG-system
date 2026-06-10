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

RULES:
- Use ONLY the provided context.
- Do NOT guess or add external knowledge.
- If answer is missing, say "Not enough information".

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