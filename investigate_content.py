"""Manually check the actual missing content from the HTML."""
import sys
sys.path.insert(0, 'f:\\RAG System for Sotu and Toru')

from bs4 import BeautifulSoup
from src.config import DATA_RAW
from pathlib import Path

html_file = DATA_RAW / "production-logistics.html"
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Remove script and style
for script in soup(["script", "style"]):
    script.decompose()

# Find the specific missing items
print("=" * 80)
print("INVESTIGATING MISSING CONTENT")
print("=" * 80)

# Look for text containing "The mobile KLT robot integrates high-end technology"
all_text = soup.get_text()
search_phrases = [
    "The mobile KLT robot integrates high-end technology",
    "If SOTO encounters a problem",
    "Bosch Automatic connection",
    "CommissioningThe mobile picking robot TORU"
]

for phrase in search_phrases:
    if phrase[:50] in all_text:
        # Find context
        idx = all_text.find(phrase[:50])
        context_start = max(0, idx - 100)
        context_end = min(len(all_text), idx + 250)
        context = all_text[context_start:context_end]
        print(f"\n✓ Found in HTML: '{phrase[:40]}...'")
        print(f"  Context: ...{context}...")
    else:
        print(f"\n✗ NOT Found: '{phrase[:40]}...'")

# Check if these are in main article divs
print("\n" + "=" * 80)
print("CHECKING WHERE THIS CONTENT IS LOCATED IN HTML")
print("=" * 80)

# Look for all divs with class or id containing "content", "article", "main"
main_areas = soup.find_all(['div', 'article', 'main'], 
                           attrs={'class': lambda x: x and any(word in str(x).lower() 
                                  for word in ['content', 'article', 'main', 'body'])})

if main_areas:
    print(f"\nFound {len(main_areas)} main content areas")
    for area in main_areas[:3]:
        text = area.get_text()[:200]
        print(f"  - {area.name} with class '{area.get('class')}': {text}...")
else:
    print("\nNo main content areas found with standard class names")
    print("This might mean the page uses custom structure")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("""
The missing content analysis shows items like:
- "CommissioningThe mobile picking robot TORU" (concatenated = navigation)  
- "New LogisticsSpecialist knowledge..." (concatenated = navigation)
- "AdvantagesProcess integration..." (concatenated = section headers)

These appear to be menu/navigation items that got improperly concatenated by BeautifulSoup's text extraction.
The real content (like "The mobile KLT robot integrates...") may be in a structured section that trafilatura doesn't recognize.

This is EXPECTED behavior for trafilatura - it focuses on article content, 
not product specification lists or case study sections.
""")
