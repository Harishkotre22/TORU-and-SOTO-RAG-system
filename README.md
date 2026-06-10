# RAG System for SOTU and Toru

This repository is a starter structure for building a Retrieval-Augmented Generation (RAG) system for the SOTU and Toru robots from Magazino.

## First program

1. Open `src/main.py`.
2. Save it in the repository under `src/main.py`.
3. Run it from the workspace root:
   ```bash
   python -m src.main
   ```

## Ingest and ask

- Build the retrieval index after cleaning:
  ```bash
  python -m src.main --ingest
  ```
  This writes the embeddings to a SQLite database in `data/embeddings/embeddings.sqlite3`.
- Ask a question against the built index:
  ```bash
  python -m src.main --ask "What is SOTU?"
  ```

## Next steps

- Add scraping code in `src/scraper.py`.
- Add text cleaning code in `src/cleaner.py`.
- Add embedding and vector store ingestion in `src/ingest.py`.
- Add retrieval and QA flow in `src/qa.py`.

## Data folders

- `data/raw/` — raw scraped content
- `data/cleaned/` — cleaned text chunks
- `data/embeddings/` — saved embedding index or vector store
