import tempfile
import unittest
from pathlib import Path
from personalai.rag import LocalVectorStore


class TestRAG(unittest.TestCase):
    def test_rag_ingest_and_query(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            store = LocalVectorStore(persist_dir=Path(tmp_dir) / "chroma_test")

            docs = [
                {
                    "id": "doc1",
                    "text": "Personal AI system operates entirely on local silicon to ensure zero data leakage.",
                    "metadata": {"source": "architecture.md"},
                },
                {
                    "id": "doc2",
                    "text": "Model context protocol (MCP) servers mount local filesystem and browser tools.",
                    "metadata": {"source": "mcp_spec.md"},
                },
            ]

            count = store.ingest_documents(docs)
            self.assertEqual(count, 2)

            results = store.query_context("Where does personal AI run?", n_results=1)
            self.assertEqual(len(results), 1)
            self.assertIn("local silicon", results[0]["text"])
            self.assertEqual(results[0]["source"], "architecture.md")

            citation_md = store.format_citations(results)
            self.assertIn("Source: `architecture.md`", citation_md)


if __name__ == "__main__":
    unittest.main()
