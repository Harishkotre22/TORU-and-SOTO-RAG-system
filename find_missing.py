"""Find what content was filtered out."""
import re
from bs4 import BeautifulSoup
import sys
sys.path.insert(0, 'f:\\RAG System for Sotu and Toru')

from src.cleaner import extract_main_content
from src.config import DATA_RAW
from pathlib import Path

html_file = DATA_RAW / "production-logistics.html"
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Remove script and style elements
for script in soup(["script", "style"]):
    script.decompose()

# Get all text
all_text = soup.get_text()
all_paragraphs = [p.strip() for p in all_text.split('\n') if p.strip() and len(p.strip()) > 20]

# Get extracted text
extracted = extract_main_content(html)
extracted_paragraphs = [p.strip() for p in extracted.split('\n') if p.strip()]

# Find paragraphs in HTML but NOT in extracted
missing_content = []
for para in all_paragraphs:
    # Check if this paragraph or a significant part of it is in extracted
    if para not in extracted and len(para) > 30:
        # Check if at least 50% of the paragraph is somewhere in extracted
        words = para.split()
        found_words = sum(1 for word in words if word in extracted)
        if found_words < len(words) * 0.5:  # Less than 50% of words found
            missing_content.append(para)

print("=" * 70)
print("CONTENT FROM HTML NOT IN EXTRACTED TEXT")
print("=" * 70)
print(f"Total paragraphs in raw HTML: {len(all_paragraphs)}")
print(f"Significant missing paragraphs: {len(missing_content)}")
print("\nSample of missing content (if any):")
print("-" * 70)
for i, para in enumerate(missing_content[:10]):
    print(f"\n{i+1}. {para[:150]}...")
    
if len(missing_content) == 0:
    print("\n✓ NO SIGNIFICANT CONTENT WAS FILTERED OUT")
    print("  (Trafilatura extracted all the main article content)")
elif len(missing_content) < 10:
    print(f"\n⚠ {len(missing_content)} paragraphs were filtered (likely navigation/ads)")
else:
    print(f"\n✗ {len(missing_content)} paragraphs were filtered (POTENTIAL ISSUE)")
