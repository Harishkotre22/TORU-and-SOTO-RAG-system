from typing import List, Dict
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline


class RAGGenerator:
    def __init__(self, model_name: str = "google/flan-t5-base"):

        print("Loading local generator model...")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

        # IMPORTANT: FLAN-T5 is NOT text-generation → it is text2text-generation
        self.pipe = pipeline(
            task="text2text-generation",
            model=self.model,
            tokenizer=self.tokenizer
        )

    def build_prompt(self, question: str, chunks: List[Dict]) -> str:

        context_blocks = []

        for i, c in enumerate(chunks, 1):
            context_blocks.append(
                f"""Chunk {i}
Source: {c.get('source', 'unknown')}
Section: {c.get('section', 'unknown')}
Subsection: {c.get('subsection', 'unknown')}

Text:
{c.get('text', '')}
"""
            )

        context = "\n".join(context_blocks)

        prompt = f"""
Guidelines:
- Extract relevant facts accurately.
- Group related information logically.
- Do not infer or assume missing details.
- Keep terminology consistent with the context.
- Prioritize: capabilities, performance, integration, safety, and use cases.
- If the context does not contain enough information, explicitly say so.

Context:
{context}

Question:
{question}

Answer (structured, precise, factual):
"""
        return prompt.strip()

    def generate(self, question: str, chunks: List[Dict]) -> str:

        prompt = self.build_prompt(question, chunks)

        result = self.pipe(
            prompt,
            max_new_tokens=200,
            do_sample=False
        )

        output = result[0]["generated_text"]

        # remove accidental prompt echoing
        if prompt in output:
            output = output.replace(prompt, "").strip()

        return output