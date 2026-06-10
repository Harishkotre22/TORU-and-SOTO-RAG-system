import requests
from pathlib import Path
from typing import List

from .config import DATA_RAW, URLS


def fetch_page(url: str, timeout: int = 15) -> str:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def save_raw_html(url: str, html: str) -> Path:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    name = url.rstrip("/").split("/")[-1] or "index"
    output_path = DATA_RAW / f"{name}.html"
    output_path.write_text(html, encoding="utf-8")
    return output_path


def scrape_all() -> List[Path]:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    saved_files = []
    for url in URLS:
        html = fetch_page(url)
        path = save_raw_html(url, html)
        print(f"Saved raw page: {url} -> {path}")
        saved_files.append(path)
    return saved_files
