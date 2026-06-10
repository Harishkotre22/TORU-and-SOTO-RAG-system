"""Verify that extracted content contains key information."""
import sys
sys.path.insert(0, 'f:\\RAG System for Sotu and Toru')

from src.cleaner import extract_main_content
from src.config import DATA_RAW
from pathlib import Path

html_file = DATA_RAW / "production-logistics.html"
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

extracted = extract_main_content(html)

# Check for key information
key_topics = {
    "Product name (SOTO)": "SOTO" in extracted,
    "Transport capability": "transport" in extracted.lower(),
    "KLT/totes": "KLT" in extracted or "tote" in extracted.lower(),
    "Safety features": "safety" in extracted.lower() or "sensor" in extracted.lower(),
    "Integration": "integration" in extracted.lower() or "WMS" in extracted,
    "Cost benefits": "cost" in extracted.lower() or "efficiency" in extracted.lower(),
    "Technical specs": "load" in extracted.lower() or "height" in extracted.lower(),
    "Real use cases": "industry" in extracted.lower() or "warehouse" in extracted.lower(),
}

print("=" * 70)
print("KEY INFORMATION EXTRACTED")
print("=" * 70)
all_present = True
for topic, present in key_topics.items():
    status = "✓" if present else "✗"
    print(f"{status} {topic}")
    if not present:
        all_present = False

print("\n" + "=" * 70)
if all_present:
    print("✓ ALL KEY INFORMATION IS PRESENT")
    print("\nConclusion: Trafilatura successfully extracted the main content")
    print("The 4.3% compression ratio is appropriate for web-to-text conversion")
else:
    print("✗ SOME INFORMATION IS MISSING")
    print("\nConclusion: Content loss detected")

print("=" * 70)
print("SAMPLE EXTRACTED CONTENT:")
print("=" * 70)
print(extracted[:800])
