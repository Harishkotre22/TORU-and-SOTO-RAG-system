import re
from pathlib import Path

import trafilatura
from bs4 import BeautifulSoup

from .config import DATA_CLEANED


import re
from bs4 import BeautifulSoup
import trafilatura

def extract_main_content(html_content):
    if not html_content:
        return ""
    
    # 1. Try Trafilatura extraction
    extracted = trafilatura.extract(
        html_content, 
        include_links=False, 
        include_images=False, 
        include_tables=True
    )
    
    # 2. Generate a custom, highly targetable fallback using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Strip scripts, styles, and templates that cause extraction noise
    for noise in soup(['script', 'style', 'nav', 'footer', 'header', 'template']):
        noise.decompose()
        
    # Track down specific container classes used by this theme
    target_classes = ['mag_section', 'text-magbody', 'mag_product_explainer_text', 'entry-content']
    content_divs = soup.find_all(class_=lambda c: c and any(x in c for x in target_classes))
    
    fallback_lines = []
    if content_divs:
        for div in content_divs:
            # Extract text from structural readable tags
            for element in div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                text = element.get_text(strip=True)
                if text and text not in fallback_lines:
                    fallback_lines.append(text)
        fallback_text = "\n\n".join(fallback_lines)
    else:
        # Global fallback if no specialized content classes match
        fallback_text = soup.get_text(separator="\n\n", strip=True)
        
    # 3. Clean hidden soft hyphens (\u00ad) disrupting processing frameworks
    if extracted:
        extracted = extracted.replace('\u00ad', '')
    if fallback_text:
        fallback_text = fallback_text.replace('\u00ad', '')

    # 4. Smart Decision Override Logic
    if extracted and fallback_text:
        # If Trafilatura captures significantly less text than the raw container tags,
        # it means it fell into the heuristic comment pruning trap. Force the fallback text.
        if len(extracted.strip()) < len(fallback_text.strip()) * 0.75:
            return fallback_text
        return extracted
        
    return fallback_text if fallback_text else (extracted if extracted else "")


def remove_boilerplate_lines(text: str) -> str:
    """
    Filters generic privacy policy terms, cookie agreements, and lingering layout items.
    """
    boilerplate_patterns = [
        r"skip to",
        r"jump to",
        r"cookie settings",
        r"accept cookies",
        r"privacy policy",
        r"terms of use",
        r"all rights reserved",
        r"imprint",
        r"data policy",
        r"sign up for.*newsletter",
        r"thank you very much for your message"
    ]

    cleaned = []
    for line in text.splitlines():
        if not line.strip():
            cleaned.append("")
            continue

        # Strip Markdown tokens temporarily to accurately evaluate line contents
        normalized_line = re.sub(r"^[#*\-\s\d\.]+", "", line).strip().lower()

        remove = False
        for pattern in boilerplate_patterns:
            if re.search(pattern, normalized_line):
                remove = True
                break

        if not remove:
            cleaned.append(line)

    return "\n".join(cleaned)


def remove_metadata_and_noise(text: str) -> str:
    """
    Cleans punctuation lines without corrupting structural Markdown elements.
    """
    cleaned_lines = []
    for line in text.splitlines():
        trimmed = line.strip()
        if not trimmed:
            cleaned_lines.append("")
            continue

        if re.match(r"^[\s\-_•·|*:=]+$", trimmed):
            # Safe passage for Markdown dividers or markdown table layouts
            if trimmed in ["---", "***", "___"] or "|" in trimmed:
                cleaned_lines.append(line)
                continue
            else:
                continue

        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def deduplicate_lines(text: str) -> str:
    """
    Deduplicates text sections cloned between mobile/desktop variants 
    while preserving naturally repeating local tags (e.g. 'Safety', 'Advantages').
    """
    seen = set()
    unique_lines = []
    for line in text.splitlines():
        trimmed = line.strip()
        if not trimmed:
            unique_lines.append("")
            continue

        normalized = trimmed.lower()
        # Restrict structural global tracking to long context sentences
        if len(normalized) > 30:
            if normalized not in seen:
                unique_lines.append(line)
                seen.add(normalized)
        else:
            unique_lines.append(line)

    return "\n".join(unique_lines)


def normalize_whitespace(text: str) -> str:
    """
    Erases breaking hidden soft-hyphens and shapes text blocks cleanly.
    """
    # Stitch fragmented words back together by dropping hidden soft-hyphens
    text = text.replace("\xad", "")
    
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.splitlines()]

    cleaned_lines = []
    prev_blank = False

    for line in lines:
        if not line:
            if not prev_blank:
                cleaned_lines.append("")
            prev_blank = True
        else:
            cleaned_lines.append(line)
            prev_blank = False

    return "\n".join(cleaned_lines).strip()


def html_to_text(html: str) -> str:
    """
    Pipeline mapping raw scraped HTML straight to clear, structured Markdown.
    """
    text = extract_main_content(html)
    text = remove_boilerplate_lines(text)
    text = remove_metadata_and_noise(text)
    text = deduplicate_lines(text)
    text = normalize_whitespace(text)
    return text


def save_clean_text(name: str, text: str) -> Path:
    DATA_CLEANED.mkdir(parents=True, exist_ok=True)
    output_path = DATA_CLEANED / f"{name}.txt"
    output_path.write_text(text, encoding="utf-8")
    return output_path


def clean_html_file(input_path: Path) -> Path:
    html = input_path.read_text(encoding="utf-8")
    cleaned_text = html_to_text(html)
    name = input_path.stem
    return save_clean_text(name, cleaned_text)