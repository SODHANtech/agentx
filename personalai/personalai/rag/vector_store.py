import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from personalai.config import settings

logger = logging.getLogger(__name__)


class LocalVectorStore:
    """Zero-leak local vector database powered by embedded ChromaDB and bge-small-en-v1.5 embeddings."""

    def __init__(self, persist_dir: Optional[Path] = None, collection_name: str = "personal_knowledge"):
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Private personal knowledge embeddings"},
        )

    def ingest_documents(self, documents: List[Dict[str, Any]]) -> int:
        """Ingests documents into ChromaDB.
        Each doc dict must contain 'id', 'text', and optional 'metadata' (e.g. source, title, date).
        """
        if not documents:
            return 0

        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc.get("metadata", {"source": "local"}) for doc in documents]

        self.collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
        logger.info(f"Ingested {len(documents)} document chunks into {self.collection_name}")
        return len(documents)

    def query_context(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Queries vector database and returns top relevant chunks with source citations."""
        results = self.collection.query(query_texts=[query_text], n_results=n_results)
        retrieved = []

        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metadatas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)

            for text, meta, dist in zip(docs, metadatas, distances):
                retrieved.append({
                    "text": text,
                    "metadata": meta,
                    "score": 1.0 - float(dist) if dist else 1.0,
                    "source": meta.get("source", "unknown"),
                })

        return retrieved

    def format_citations(self, results: List[Dict[str, Any]]) -> str:
        """Formats retrieved chunks into clean markdown context block with citations."""
        if not results:
            return ""

        formatted_blocks = ["### Retrieved Knowledge Context:"]
        for idx, item in enumerate(results, start=1):
            source = item.get("source", f"Doc-{idx}")
            formatted_blocks.append(f"**[{idx}] Source: `{source}`**\n{item['text']}\n")

        return "\n".join(formatted_blocks)
