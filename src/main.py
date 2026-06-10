"""
Starter script for the SOTU/Toru RAG system.
Run this from the repository root:
    python -m src.main
"""

import argparse
from pathlib import Path

from .scraper import scrape_all
from .cleaner import clean_html_file
from .ingest import build_index
from .qa import answer_question


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="SOTU/Toru RAG system")
    parser.add_argument("--ingest", action="store_true", help="Build the retrieval index from cleaned text")
    parser.add_argument("--ask", type=str, help="Ask a question using the built index")
    args = parser.parse_args()

    print("RAG system starter script")
    print(f"Project root: {root}\n")

    if args.ask:
        print("Answering question:")
        answer = answer_question(args.ask)
        print(answer)
        return

    if args.ingest:
        print("Step: Building retrieval index...")
        build_index()
        print("Done. Index saved to data/embeddings/embeddings.sqlite3")
        return

    print("Step 1: Scraping raw pages...")
    raw_files = scrape_all()

    print("\nStep 2: Cleaning scraped content...")
    for raw_file in raw_files:
        cleaned_path = clean_html_file(raw_file)
        print(f"Saved cleaned text: {cleaned_path}")

    print("\nStep 3: Building retrieval index...")
    build_index()
    print("\nDone. Check data/raw/, data/cleaned/, and data/embeddings/")


if __name__ == "__main__":
    main()
