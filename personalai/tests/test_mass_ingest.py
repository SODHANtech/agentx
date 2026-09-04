import unittest
import tempfile
import shutil
from pathlib import Path
from personalai.rag.mass_ingester import MassIngester, SUPPORTED_EXTENSIONS
from personalai.rag.vector_store import LocalVectorStore


class TestMassIngester(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_mass_rag_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_ignore_rules(self):
        ingester = MassIngester()
        self.assertTrue(ingester.is_ignored(self.test_dir / ".git" / "config"))
        self.assertTrue(ingester.is_ignored(self.test_dir / "node_modules" / "package.json"))
        self.assertTrue(ingester.is_ignored(self.test_dir / "__pycache__" / "file.pyc"))
        self.assertTrue(ingester.is_ignored(self.test_dir / "image.png"))
        self.assertFalse(ingester.is_ignored(self.test_dir / "src" / "main.py"))
        self.assertFalse(ingester.is_ignored(self.test_dir / "docs" / "readme.md"))

    def test_chunking_with_line_numbers(self):
        ingester = MassIngester(chunk_size=150, chunk_overlap=30)
        sample_code = "\n".join([f"def function_{i}():\n    return {i}" for i in range(20)])
        file_path = self.test_dir / "sample.py"
        file_path.write_text(sample_code, encoding="utf-8")

        chunks = ingester.chunk_text(sample_code, file_path, base_dir=self.test_dir)
        self.assertGreater(len(chunks), 1)
        self.assertIn("start_line", chunks[0]["metadata"])
        self.assertIn("end_line", chunks[0]["metadata"])
        self.assertEqual(chunks[0]["metadata"]["file_type"], "code")
        self.assertEqual(chunks[0]["metadata"]["filename"], "sample.py")

    def test_directory_scan_and_ingestion(self):
        # Create nested test files
        src_dir = self.test_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        py_file = src_dir / "app.py"
        py_file.write_text("class App:\n    def run(self):\n        print('Hello World')\n", encoding="utf-8")

        doc_file = self.test_dir / "README.md"
        doc_file.write_text("# Project Docs\nThis is a test project documentation.\n", encoding="utf-8")

        # Create an ignored file
        ignored_dir = self.test_dir / "node_modules"
        ignored_dir.mkdir()
        (ignored_dir / "index.js").write_text("console.log('ignored')", encoding="utf-8")

        ingester = MassIngester()
        chunks = ingester.scan_directory(self.test_dir)

        # Ensure node_modules was skipped and app.py + README.md were included
        sources = [c["metadata"]["filename"] for c in chunks]
        self.assertIn("app.py", sources)
        self.assertIn("README.md", sources)
        self.assertNotIn("index.js", sources)

    def test_vector_store_batch_ingestion(self):
        chroma_dir = Path(tempfile.mkdtemp(prefix="test_chroma_"))
        try:
            store = LocalVectorStore(persist_dir=chroma_dir, collection_name="test_mass_ingest")
            
            # Generate 250 dummy chunks
            docs = [
                {
                    "id": f"chunk_{i}",
                    "text": f"This is chunk number {i} for RAG testing.",
                    "metadata": {"source": f"file_{i % 5}.py", "chunk_index": i},
                }
                for i in range(250)
            ]

            count = store.ingest_documents(docs, batch_size=50)
            self.assertEqual(count, 250)

            # Query context
            res = store.query_context("chunk number 10", n_results=1)
            self.assertEqual(len(res), 1)
            self.assertIn("10", res[0]["text"])

        finally:
            shutil.rmtree(chroma_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
