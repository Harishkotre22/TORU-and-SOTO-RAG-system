import json
import sqlite3
import re
from pathlib import Path
from typing import Dict, List
from sentence_transformers import SentenceTransformer
from .config import DATA_CLEANED, DATA_EMBEDDINGS, EMBEDDING_DB_PATH


def extract_heading_level(line: str) -> int:
    """
    Returns heading level:
    # = 1
    ## = 2
    ### = 3
    #### = 4
    etc.
    """
    match = re.match(r"^(#+)\s+", line)
    if match:
        return len(match.group(1))
    return 0


def extract_heading_text(line: str) -> str:
    """Removes markdown hashes and returns clean heading text."""
    return re.sub(r"^#+\s+", "", line).strip()


def chunk_text_by_headers(text: str) -> List[Dict]:
    """
    Semantic hierarchical chunking with metadata.

    Each chunk now contains:
    - section hierarchy
    - clean text
    - level awareness
    """

    lines = text.splitlines()

    chunks = []
    current_chunk = []

    #  NEW: metadata tracking
    current_section = None
    current_subsection = None
    current_subsubsection = None

    def flush():
        """Save current chunk with metadata"""
        if not current_chunk:
            return

        chunks.append({
            "text": "\n".join(current_chunk).strip(),
            "section": current_section,
            "subsection": current_subsection,
            "subsubsection": current_subsubsection
        })

    for line in lines:

        level = extract_heading_level(line)

        #  IMPROVED: split on ALL heading levels (# → ######)
        if level > 0:

            flush()
            current_chunk = []

            heading_text = extract_heading_text(line)

            # update hierarchy
            if level == 1:
                current_section = heading_text
                current_subsection = None
                current_subsubsection = None

            elif level == 2:
                current_subsection = heading_text
                current_subsubsection = None

            elif level >= 3:
                current_subsubsection = heading_text

            current_chunk.append(line)
            continue

        # normal text
        if line.strip():
            current_chunk.append(line)

        elif current_chunk and current_chunk[-1] != "":
            current_chunk.append("")

    flush()

    # filter tiny chunks
    return [
        c for c in chunks
        if len(c["text"].replace("\n", "").strip()) > 10
    ]


def build_index() -> Dict:
    DATA_EMBEDDINGS.mkdir(parents=True, exist_ok=True)

    print("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    documents = []

    for file_path in sorted(DATA_CLEANED.glob("*.txt")):
        text = file_path.read_text(encoding="utf-8")
        source = file_path.name

        chunk_objects = chunk_text_by_headers(text)

        for index, chunk in enumerate(chunk_objects):

            documents.append({
                "id": f"{file_path.stem}-{index}",
                "source": source,
                "text": chunk["text"],

                # 🔴 NEW: metadata added
                "section": chunk["section"],
                "subsection": chunk["subsection"],
                "subsubsection": chunk["subsubsection"]
            })

    if not documents:
        raise ValueError("No cleaned documents found in data/cleaned/ to build the index.")

    print(f"Generating embeddings for {len(documents)} chunks...")

    texts_to_encode = [doc["text"] for doc in documents]
    embeddings = model.encode(texts_to_encode, show_progress_bar=True)

    for doc, embedding in zip(documents, embeddings):
        doc["vector"] = embedding.tolist()

    connection = sqlite3.connect(str(EMBEDDING_DB_PATH))

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                source TEXT,
                text TEXT,
                section TEXT,
                subsection TEXT,
                subsubsection TEXT,
                vector TEXT
            )
        """)

        connection.execute("DELETE FROM documents")

        for doc in documents:
            connection.execute(
                """
                INSERT INTO documents (
                    id, source, text,
                    section, subsection, subsubsection,
                    vector
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc["id"],
                    doc["source"],
                    doc["text"],
                    doc["section"],
                    doc["subsection"],
                    doc["subsubsection"],
                    json.dumps(doc["vector"])
                )
            )

        connection.commit()

    finally:
        connection.close()

    return {"documents_count": len(documents)}


def load_index() -> Dict:
    if not EMBEDDING_DB_PATH.exists():
        raise FileNotFoundError("Embedding database not found. Run ingest first.")

    connection = sqlite3.connect(str(EMBEDDING_DB_PATH))
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            "SELECT id, source, text, section, subsection, subsubsection, vector FROM documents"
        ).fetchall()

    finally:
        connection.close()

    documents = []

    for row in rows:
        documents.append({
            "id": row["id"],
            "source": row["source"],
            "text": row["text"],
            "section": row["section"],
            "subsection": row["subsection"],
            "subsubsection": row["subsubsection"],
            "vector": json.loads(row["vector"])
        })

    return {"documents": documents}