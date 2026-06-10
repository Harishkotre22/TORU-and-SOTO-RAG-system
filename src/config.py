

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_CLEANED = ROOT / "data" / "cleaned"
DATA_EMBEDDINGS = ROOT / "data" / "embeddings"
EMBEDDING_DB_PATH = DATA_EMBEDDINGS / "embeddings.sqlite3"

URLS = [
    "https://www.magazino.eu/en/shoe-logistics/",
    "https://www.magazino.eu/en/production-logistics/",
]

CHUNK_SIZE = 200
CHUNK_OVERLAP = 50
TOP_K = 3
