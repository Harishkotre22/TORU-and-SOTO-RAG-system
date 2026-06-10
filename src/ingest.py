import json
import sqlite3
from pathlib import Path
from typing import Dict, List
from sentence_transformers import SentenceTransformer

from .config import DATA_CLEANED, DATA_EMBEDDINGS, EMBEDDING_DB_PATH


# -----------------------------
# TITLE DETECTION
# -----------------------------
def looks_like_title(line: str) -> bool:
    line = line.strip()

    if not line:
        return False

    # too long → paragraph
    if len(line.split()) > 12:
        return False

    # sentences usually end with punctuation
    if line.endswith((".", "?", "!")):
        return False

    # must contain at least one letter (avoid symbols / noise)
    if not any(c.isalpha() for c in line):
        return False

    return True


# -----------------------------
# TOKEN HELPERS
# -----------------------------
def word_count(text: str) -> int:
    return len(text.split())


def split_words(text: str) -> List[str]:
    return text.split()


def join_words(words: List[str]) -> str:
    return " ".join(words)


# -----------------------------
# OVERLAP SPLITTING
# -----------------------------
def split_with_overlap(text: str, max_words: int = 200, overlap: int = 50) -> List[str]:
    words = split_words(text)

    if len(words) <= max_words:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = start + max_words
        chunk = words[start:end]
        chunks.append(join_words(chunk))

        if end >= len(words):
            break

        start = end - overlap

    return chunks


# -----------------------------
# MAIN CHUNKER
# -----------------------------
MIN_SECTION_WORDS = 20
MAX_SECTION_WORDS = 250


def chunk_text(text: str) -> List[Dict]:
    lines = text.splitlines()

    chunks = []
    current = []

    current_section = None

    def flush():
        nonlocal current, current_section

        if not current:
            return

        block = "\n".join(current).strip()

        if not block:
            current = []
            return

        # split oversized blocks
        if word_count(block) > MAX_SECTION_WORDS:
            parts = split_with_overlap(block)

            for p in parts:
                chunks.append({
                    "text": p,
                    "section": current_section
                })
        else:
            chunks.append({
                "text": block,
                "section": current_section
            })

        current = []

    for line in lines:
        line_stripped = line.strip()

        if looks_like_title(line_stripped):
            # close previous block
            flush()

            # update section context
            current_section = line_stripped

            # start new block with title
            current = [line_stripped]
            continue

        if line_stripped:
            current.append(line_stripped)
        else:
            if current and current[-1] != "":
                current.append("")

    flush()

    # filter noise
    return [
        c for c in chunks
        if word_count(c["text"]) >= 3
    ]


# -----------------------------
# BUILD INDEX
# -----------------------------
def build_index() -> Dict:
    DATA_EMBEDDINGS.mkdir(parents=True, exist_ok=True)

    print("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    documents = []

    for file_path in sorted(DATA_CLEANED.glob("*.txt")):
        text = file_path.read_text(encoding="utf-8")
        source = file_path.name

        chunk_objects = chunk_text(text)

        print(f"{source}: {len(chunk_objects)} chunks")

        for i, chunk in enumerate(chunk_objects):
            documents.append({
                "id": f"{file_path.stem}-{i}",
                "source": source,
                "text": chunk["text"],
                "section": chunk.get("section")
            })

    if not documents:
        raise ValueError("No cleaned documents found in data/cleaned/")

    print(f"Generating embeddings for {len(documents)} chunks...")

    embeddings = model.encode(
        [d["text"] for d in documents],
        show_progress_bar=True
    )

    for doc, emb in zip(documents, embeddings):
        doc["vector"] = emb.tolist()

    conn = sqlite3.connect(str(EMBEDDING_DB_PATH))

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                source TEXT,
                text TEXT,
                section TEXT,
                vector TEXT
            )
        """)

        conn.execute("DELETE FROM documents")

        for doc in documents:
            conn.execute(
                """
                INSERT INTO documents (
                    id, source, text, section, vector
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    doc["id"],
                    doc["source"],
                    doc["text"],
                    doc["section"],
                    json.dumps(doc["vector"])
                )
            )

        conn.commit()

    finally:
        conn.close()

    return {"documents_count": len(documents)}


# -----------------------------
# LOAD INDEX
# -----------------------------
def load_index() -> Dict:
    if not EMBEDDING_DB_PATH.exists():
        raise FileNotFoundError("Embedding database not found. Run ingest first.")

    conn = sqlite3.connect(str(EMBEDDING_DB_PATH))
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(
            "SELECT id, source, text, section, vector FROM documents"
        ).fetchall()
    finally:
        conn.close()

    documents = [
        {
            "id": r["id"],
            "source": r["source"],
            "text": r["text"],
            "section": r["section"],
            "vector": json.loads(r["vector"])
        }
        for r in rows
    ]

    return {"documents": documents}