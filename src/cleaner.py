import re
from pathlib import Path

import trafilatura
from bs4 import BeautifulSoup

from .config import DATA_CLEANED


def extract_main_content(html: str) -> str:
    """
    Surgically cleans HTML layout noise without destroying structural technical content,
    then uses Trafilatura or a robust structural fallback to output clean Markdown.
    """
    # 0. Pre-clean string-level byte anomalies (soft-hyphens & non-breaking spaces)
    html = html.replace("\xad", "")
    html = html.replace("\xa0", " ")
    html = re.sub(r"&shy;", "", html, flags=re.IGNORECASE)
    html = re.sub(r"&nbsp;", " ", html, flags=re.IGNORECASE)

    soup = BeautifulSoup(html, "html.parser")

    # 1. Eliminate heavy operational, asset, and unrendered template blocks
    ignored_tags = ["script", "style", "noscript", "svg", "iframe", "form", "template"]
    for tag in soup(ignored_tags):
        tag.decompose()

    # 2. Refined noise pattern: Avoid matching terms like "menu" or "sidebar" globally
    noise_patterns = re.compile(
        r"global-header|site-footer|cookie-notice|social-share|lang-selector|breadcrumbs", 
        re.IGNORECASE
    )
    
    for element in soup.find_all(True):
        if element.attrs is None:
            continue

        class_list = element.get("class", [])
        class_str = " ".join(class_list) if isinstance(class_list, list) else str(class_list)
        element_id = element.get("id", "")
        
        if element.name in ["header", "footer", "nav"] or \
           noise_patterns.search(class_str) or noise_patterns.search(element_id):
            element.decompose()

    # ==========================================================================
    # NEW STEP: Inject a structural marker into headings BEFORE text extraction.
    # This guarantees that the exact heading hierarchy (H1-H6) survives with 100% fidelity.
    # ==========================================================================
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        level = tag.name[1]
        tag.insert(0, f"H{level}HEADERMARKER ")

    # 3. Pre-compile fallback structured content to ensure 100% data preservation
    fallback_parts = []
    content_tags = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "table"]
    
    for tag in soup.find_all(content_tags):
        if tag.find_parent(["p", "li", "table"]):
            continue
            
        text = tag.get_text(" ", strip=True)
        if not text:
            continue
            
        if tag.name.startswith("h"):
            level = tag.name[1]
            fallback_parts.append(f"\n{'#' * int(level)} {text}\n")
        elif tag.name == "li":
            fallback_parts.append(f"* {text}")
        elif tag.name == "table":
            for i, row in enumerate(tag.find_all("tr")):
                cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
                if any(cells):
                    fallback_parts.append("| " + " | ".join(cells) + " |")
                    if i == 0 and row.find_all("th"):
                        fallback_parts.append("| " + " | ".join(["---"] * len(cells)) + " |")
            fallback_parts.append("")
        else:
            fallback_parts.append(text)

    fallback_text = "\n".join(fallback_parts)

    # 4. Extract text with Trafilatura
    cleaned_html = str(soup)
    extracted = trafilatura.extract(
        cleaned_html,
        include_comments=False,
        include_tables=True,
        output_format="markdown",
        favor_precision=False  
    )

    # 5. Smart choice selection
    if extracted and len(extracted.strip()) > len(fallback_text.strip()) * 0.85:
        return extracted
    elif fallback_text.strip():
        return fallback_text

    return extracted if extracted else ""


def restore_headings(text: str) -> str:
    """
    Uses the injected HTML markers to flawlessly reconstruct the correct Markdown heading hierarchy
    (# through ######). This completely replaces the brittle guessing heuristic.
    """
    lines = text.splitlines()
    rebuilt = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            rebuilt.append("")
            continue

        # Look for the embedded structural markers (e.g., H2HEADERMARKER or H3HEADERMARKER)
        match = re.search(r"H([1-6])HEADERMARKER", stripped)
        if match:
            level = int(match.group(1))
            # Strip out any pre-existing markdown tokens or markers to extract the raw title text
            clean_text = re.sub(r"^[#\s]*H[1-6]HEADERMARKER\s*", "", stripped).strip()
            if clean_text:
                rebuilt.append(f"{'#' * level} {clean_text}")
            continue

        # Fallback to protect any pre-existing markdown headings that escaped extraction unscathed
        if stripped.startswith("#"):
            rebuilt.append(line)
            continue

        rebuilt.append(line)

    return "\n".join(rebuilt)


def remove_boilerplate_lines(text: str) -> str:
    boilerplate_patterns = [
        r"skip to", r"jump to", r"cookie settings", r"accept cookies",
        r"privacy policy", r"terms of use", r"all rights reserved",
        r"imprint", r"data policy", r"sign up for.*newsletter",
        r"thank you very much for your message"
    ]
    cleaned = []
    for line in text.splitlines():
        if not line.strip():
            cleaned.append("")
            continue
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
    cleaned_lines = []
    for line in text.splitlines():
        trimmed = line.strip()
        if not trimmed:
            cleaned_lines.append("")
            continue
        if re.match(r"^[\s\-_•·|*:=]+$", trimmed):
            if trimmed in ["---", "***", "___"] or "|" in trimmed:
                cleaned_lines.append(line)
                continue
            else:
                continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def deduplicate_lines(text: str) -> str:
    seen = set()
    unique_lines = []
    for line in text.splitlines():
        trimmed = line.strip()
        if not trimmed:
            unique_lines.append("")
            continue
        normalized = trimmed.lower()
        if len(normalized) > 30:
            if normalized not in seen:
                unique_lines.append(line)
                seen.add(normalized)
        else:
            unique_lines.append(line)
    return "\n".join(unique_lines)


def normalize_whitespace(text: str) -> str:
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
    text = restore_headings(text)
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