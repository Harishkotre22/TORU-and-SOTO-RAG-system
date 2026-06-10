import shutil
import tempfile
import unittest
from pathlib import Path

import src.config as config
import src.ingest as ingest


class TestIngestSQLite(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="rag_test_", dir=".")
        self.cleaned_dir = Path(self.temp_dir) / "cleaned"
        self.emb_dir = Path(self.temp_dir) / "embeddings"
        self.cleaned_dir.mkdir(parents=True, exist_ok=True)
        self.emb_dir.mkdir(parents=True, exist_ok=True)

        (self.cleaned_dir / "doc1.txt").write_text(
            "SOTU is a robot from Magazino.",
            encoding="utf-8",
        )
        (self.cleaned_dir / "doc2.txt").write_text(
            "TORU is a picking robot for warehouses.",
            encoding="utf-8",
        )

        config.DATA_CLEANED = self.cleaned_dir
        config.DATA_EMBEDDINGS = self.emb_dir
        config.EMBEDDING_DB_PATH = self.emb_dir / "embeddings.sqlite3"
        ingest.DATA_CLEANED = self.cleaned_dir
        ingest.DATA_EMBEDDINGS = self.emb_dir
        ingest.EMBEDDING_DB_PATH = config.EMBEDDING_DB_PATH

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_build_index_persists_to_sqlite(self):
        index_data = ingest.build_index()

        self.assertTrue(config.EMBEDDING_DB_PATH.exists())
        self.assertIn("documents", index_data)
        self.assertGreater(len(index_data["documents"]), 0)

        loaded_index = ingest.load_index()
        self.assertIn("documents", loaded_index)
        self.assertGreater(len(loaded_index["documents"]), 0)
        self.assertIn("idf", loaded_index)


if __name__ == "__main__":
    unittest.main()
