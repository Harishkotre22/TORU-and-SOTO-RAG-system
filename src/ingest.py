import json
import sqlite3
from pathlib import Path
from typing import Dict, List
from sentence_transformers import SentenceTransformer
from .config import DATA_CLEANED, DATA_EMBEDDINGS, EMBEDDING_DB_PATH

def chunk_text_by_headers(text: str) -> List[str]:
    """
    Surgically splits text into chunks based on Markdown headings (##, ###).
    This ensures that headings, subheadings, and their descriptions 
    stay tightly packaged together for semantic retrieval.
    """
    lines = text.splitlines()
    chunks = []
    current_chunk = []

    for line in lines:
        # If we hit a main header (##) or subheader (###), save the previous block
        if line.startswith("## ") or line.startswith("### "):
            if current_chunk:
                chunks.append("\n".join(current_chunk).strip())
            current_chunk = [line]  # Start a fresh chunk with the header text
        else:
            if line.strip():
                current_chunk.append(line)
            elif current_chunk and current_chunk[-1] != "":
                current_chunk.append("")  # Maintain paragraph spacing inside a section

    # Don't forget to save the very last section
    if current_chunk:
        chunks.append("\n".join(current_chunk).strip())

    # Filter out empty or micro-chunks (less than 10 characters long)
    return [c for c in chunks if len(c.replace("\n", "").strip()) > 10]


def build_index() -> Dict:
    DATA_EMBEDDINGS.mkdir(parents=True, exist_ok=True)

    print(" Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    documents = []
    # Loop over your pristine cleaned text files
    for file_path in sorted(DATA_CLEANED.glob("*.txt")):
        text = file_path.read_text(encoding="utf-8")
        source = file_path.name
        
        # Use our new heading splitter logic here
        chunk_texts = chunk_text_by_headers(text)
        
        for index, chunk in enumerate(chunk_texts):
            documents.append({
                "id": f"{file_path.stem}-{index}",
                "source": source,
                "text": chunk,
            })

    if not documents:
        raise ValueError("No cleaned documents found in data/cleaned/ to build the index.")

    print(f"🧠 Generating semantic vectors for {len(documents)} text chunks...")
    # Gather just the raw text strings to pass to the AI model
    texts_to_encode = [doc["text"] for doc in documents]
    embeddings = model.encode(texts_to_encode, show_progress_bar=True)

    # Convert the resulting machine learning math arrays into normal Python float lists
    for doc, embedding in zip(documents, embeddings):
        doc["vector"] = embedding.tolist()

    # Pack everything away cleanly into SQLite
    connection = sqlite3.connect(str(EMBEDDING_DB_PATH))
    try:
        connection.execute("CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, source TEXT, text TEXT, vector TEXT)")
        connection.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        connection.execute("DELETE FROM documents")
        connection.execute("DELETE FROM settings")

        for doc in documents:
            connection.execute(
                "INSERT INTO documents (id, source, text, vector) VALUES (?, ?, ?, ?)",
                (doc["id"], doc["source"], doc["text"], json.dumps(doc["vector"]))
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
        document_rows = connection.execute("SELECT id, source, text, vector FROM documents").fetchall()
    finally:
        connection.close()

    documents = []
    for row in document_rows:
        documents.append({
            "id": row["id"],
            "source": row["source"],
            "text": row["text"],
            "vector": json.loads(row["vector"]),
        })

    return {"documents": documents}