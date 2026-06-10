import re
from pathlib import Path

import trafilatura
from bs4 import BeautifulSoup

from .config import DATA_CLEANED


def extract_main_content(html: str) -> str:
    """
    Surgically cleans HTML layout noise without destroying structural technical content,
    then uses Trafilatura to output clean Markdown.
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1. Eliminate heavy operational and asset code blocks
    ignored_tags = ["script", "style", "noscript", "svg", "iframe", "form"]
    for tag in soup(ignored_tags):
        tag.decompose()

    # 2. Refined noise pattern: Avoid matching terms like "menu" or "sidebar" globally,
    # because technical specifications often live inside custom tab layouts/menus.
    noise_patterns = re.compile(
        r"global-header|site-footer|cookie-notice|social-share|lang-selector|breadcrumbs", 
        re.IGNORECASE
    )
    
    for element in soup.find_all(True):
        # Safety check for zombie elements
        if element.attrs is None:
            continue

        # Convert class attribute to string safely
        class_list = element.get("class", [])
        class_str = " ".join(class_list) if isinstance(class_list, list) else str(class_list)
        element_id = element.get("id", "")
        
        # Strip structural layout noise, but preserve nested content zones
        if element.name in ["header", "footer", "nav"] or \
           noise_patterns.search(class_str) or noise_patterns.search(element_id):
            element.decompose()

    cleaned_html = str(soup)

    # 3. Extract text with relaxed precision to capture layout grids/specs
    extracted = trafilatura.extract(
        cleaned_html,
        include_comments=False,
        include_tables=True,
        output_format="markdown",
        favor_precision=False  # Crucial: stops Trafilatura from eating technical tabs
    )

    if extracted and len(extracted.strip()) > 300:
        return extracted

    # 4. Fallback structural parser if Trafilatura misses anything
    extracted_parts = []
    important_tags = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th"]
    
    for tag in soup.find_all(important_tags):
        if tag.attrs is None:
            continue
            
        text = tag.get_text(" ", strip=True)
        if len(text) <= 1:
            continue
            
        if tag.name.startswith("h"):
            level = tag.name[1]
            extracted_parts.append(f"\n{'#' * int(level)} {text}\n")
        elif tag.name == "li":
            extracted_parts.append(f"* {text}")
        else:
            extracted_parts.append(text)

    return "\n".join(extracted_parts)


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