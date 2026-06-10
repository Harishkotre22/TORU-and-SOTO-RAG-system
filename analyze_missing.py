"""Analyze missing content to see if it's duplicates or new information."""
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
all_paragraphs = [p.strip() for p in all_text.split('\n') if p.strip() and len(p.strip()) > 30]

# Get extracted text
extracted = extract_main_content(html)
extracted_lower = extracted.lower()

# Find potentially important missing paragraphs
missing = []
for para in all_paragraphs:
    if para not in extracted and len(para) > 40:
        words = para.split()
        found_words = sum(1 for word in words if word.lower() in extracted_lower)
        if found_words < len(words) * 0.5:
            # Check if this looks like important content (has tech terms, not just nav)
            if any(keyword in para.lower() for keyword in 
                   ['robot', 'sensor', 'technology', 'integration', 'feature', 'system', 'data', 'safety', 'capability']):
                missing.append({
                    'text': para,
                    'type': 'IMPORTANT' if len(para) > 80 else 'MEDIUM'
                })

print("=" * 80)
print("MISSING CONTENT ANALYSIS")
print("=" * 80)

important = [m for m in missing if m['type'] == 'IMPORTANT']
medium = [m for m in missing if m['type'] == 'MEDIUM']

print(f"\n⚠️  IMPORTANT MISSING CONTENT: {len(important)} items")
print("-" * 80)
for i, item in enumerate(important[:8]):
    print(f"\n{i+1}. {item['text'][:120]}...")

print(f"\n\nMEDIUM PRIORITY: {len(medium)} items")
print("-" * 80)
for i, item in enumerate(medium[:5]):
    print(f"\n{i+1}. {item['text'][:100]}...")

print("\n" + "=" * 80)
print("ASSESSMENT")
print("=" * 80)

if len(important) > 5:
    print("✗ SIGNIFICANT CONTENT IS BEING FILTERED")
    print("  Recommendation: Adjust trafilatura parameters or use different extraction method")
elif len(important) == 0:
    print("✓ NO IMPORTANT CONTENT IS BEING FILTERED")
    print("  The filtered content appears to be navigation/duplicate/CTA text")
else:
    print("⚠ Some important content is being filtered")
    print(f"  But it may be duplicate or supplementary to what we have")
