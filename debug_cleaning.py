"""Debug script to analyze what's being filtered at each stage."""
import sys
sys.path.insert(0, 'f:\\RAG System for Sotu and Toru')

from src.cleaner import extract_main_content, remove_boilerplate_lines, remove_metadata_and_noise, normalize_whitespace
from src.config import DATA_RAW
from pathlib import Path

html_file = DATA_RAW / "production-logistics.html"
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

print("=" * 70)
print("STAGE 1: TRAFILATURA EXTRACTION")
print("=" * 70)
extracted = extract_main_content(html)
print(f"Characters after extraction: {len(extracted)}")
print(f"Lines after extraction: {len(extracted.splitlines())}")
print("First 500 chars:")
print(extracted[:500])
print("\n")

print("=" * 70)
print("STAGE 2: BOILERPLATE REMOVAL")
print("=" * 70)
after_boilerplate = remove_boilerplate_lines(extracted)
removed_boilerplate_lines = len(extracted.splitlines()) - len(after_boilerplate.splitlines())
print(f"Characters after boilerplate removal: {len(after_boilerplate)}")
print(f"Lines removed in this stage: {removed_boilerplate_lines}")
print(f"Lines remaining: {len(after_boilerplate.splitlines())}")
print("\nSample of removed lines:")
for i, line in enumerate(extracted.splitlines()):
    cleaned = remove_boilerplate_lines(line)
    if cleaned != line and cleaned.strip() == "":
        print(f"  REMOVED: '{line[:60]}...'")
        if i > 20:
            break
print("\n")

print("=" * 70)
print("STAGE 3: METADATA AND NOISE REMOVAL")
print("=" * 70)
after_noise = remove_metadata_and_noise(after_boilerplate)
removed_noise_lines = len(after_boilerplate.splitlines()) - len(after_noise.splitlines())
print(f"Characters after noise removal: {len(after_noise)}")
print(f"Lines removed in this stage: {removed_noise_lines}")
print(f"Lines remaining: {len(after_noise.splitlines())}")
print("\n")

print("=" * 70)
print("STAGE 4: WHITESPACE NORMALIZATION")
print("=" * 70)
final = normalize_whitespace(after_noise)
print(f"Characters in final output: {len(final)}")
print(f"Lines in final output: {len(final.splitlines())}")
print("\n")

print("=" * 70)
print("COMPRESSION SUMMARY")
print("=" * 70)
print(f"HTML size: {len(html)} bytes")
print(f"After trafilatura: {len(extracted)} bytes ({(len(extracted)/len(html))*100:.1f}%)")
print(f"After boilerplate removal: {len(after_boilerplate)} bytes ({(len(after_boilerplate)/len(html))*100:.1f}%)")
print(f"After noise removal: {len(after_noise)} bytes ({(len(after_noise)/len(html))*100:.1f}%)")
print(f"Final output: {len(final)} bytes ({(len(final)/len(html))*100:.1f}%)")
print(f"\nTotal compression ratio: {(len(final)/len(html))*100:.2f}%")
