"""
ChromaDB vector store adapter for Oracle knowledge retrieval.
Implements semantic search across Oracle docs, RCA history, SQL patterns, config guides.
"""
import asyncio
import uuid
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.config.settings import get_settings
from app.core.exceptions import VectorStoreError, KnowledgeIngestError
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ChromaDBAdapter:
    """Async-wrapped ChromaDB adapter with sentence-transformer embeddings."""

    def __init__(self):
        self._client: Optional[chromadb.HttpClient] = None
        self._embedding_model: Optional[SentenceTransformer] = None
        self._collections: Dict[str, Any] = {}

    async def initialize(self) -> None:
        try:
            self._client = chromadb.HttpClient(
                host=settings.CHROMADB_HOST,
                port=settings.CHROMADB_PORT,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._embedding_model = await asyncio.to_thread(
                SentenceTransformer, settings.EMBEDDING_MODEL
            )
            # Initialize collections
            collection_names = [
                settings.CHROMADB_COLLECTION_ORACLE_DOCS,
                settings.CHROMADB_COLLECTION_RCA_HISTORY,
                settings.CHROMADB_COLLECTION_SQL_PATTERNS,
                settings.CHROMADB_COLLECTION_CONFIG_GUIDES,
            ]
            for name in collection_names:
                collection = await asyncio.to_thread(
                    self._client.get_or_create_collection,
                    name=name,
                    metadata={"hnsw:space": "cosine"},
                )
                self._collections[name] = collection
            logger.info("chromadb_initialized", collections=collection_names)
        except Exception as e:
            raise VectorStoreError(f"ChromaDB initialization failed: {e}")

    async def search(
        self,
        query: str,
        collection_name: str,
        n_results: int = None,
        module_filter: Optional[str] = None,
        score_threshold: float = None,
    ) -> List[Dict[str, Any]]:
        n_results = n_results or settings.RETRIEVAL_TOP_K
        score_threshold = score_threshold or settings.RETRIEVAL_SCORE_THRESHOLD

        collection = self._get_collection(collection_name)
        embedding = await self._embed(query)

        where_filter = {"module": module_filter} if module_filter else None

        try:
            results = await asyncio.to_thread(
                collection.query,
                query_embeddings=[embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            raise VectorStoreError(f"ChromaDB search failed: {e}")

        docs = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            similarity = 1.0 - dist  # cosine distance → similarity
            if similarity >= score_threshold:
                docs.append({
                    "content": doc,
                    "metadata": meta or {},
                    "similarity_score": round(similarity, 4),
                })

        logger.debug("chromadb_search", query=query[:50], collection=collection_name, results=len(docs))
        return docs

    async def search_all_collections(
        self,
        query: str,
        module_filter: Optional[str] = None,
        n_results_per_collection: int = 3,
    ) -> List[str]:
        """Search all collections and return combined text context."""
        all_results = []
        collection_names = [
            settings.CHROMADB_COLLECTION_ORACLE_DOCS,
            settings.CHROMADB_COLLECTION_RCA_HISTORY,
            settings.CHROMADB_COLLECTION_SQL_PATTERNS,
        ]
        for name in collection_names:
            try:
                results = await self.search(
                    query=query,
                    collection_name=name,
                    n_results=n_results_per_collection,
                    module_filter=module_filter,
                )
                for r in results:
                    all_results.append(f"[{name}] {r['content'][:400]}")
            except Exception as e:
                logger.warning("collection_search_failed", collection=name, error=str(e))

        return all_results

    async def ingest(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> int:
        collection = self._get_collection(collection_name)
        if not ids:
            ids = [str(uuid.uuid4()) for _ in documents]

        embeddings = await self._embed_batch(documents)
        try:
            await asyncio.to_thread(
                collection.upsert,
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            logger.info("chromadb_ingested", collection=collection_name, count=len(documents))
            return len(documents)
        except Exception as e:
            raise KnowledgeIngestError(f"Ingestion failed: {e}")

    async def delete(self, collection_name: str, doc_id: str) -> None:
        collection = self._get_collection(collection_name)
        await asyncio.to_thread(collection.delete, ids=[doc_id])

    async def health_check(self) -> bool:
        try:
            await asyncio.to_thread(self._client.heartbeat)
            return True
        except Exception:
            return False

    async def _embed(self, text: str) -> List[float]:
        embedding = await asyncio.to_thread(self._embedding_model.encode, text)
        return embedding.tolist()

    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = await asyncio.to_thread(self._embedding_model.encode, texts)
        return [e.tolist() for e in embeddings]

    def _get_collection(self, name: str) -> Any:
        collection = self._collections.get(name)
        if collection is None:
            raise VectorStoreError(f"Collection '{name}' not initialized. Call initialize() first.")
        return collection


_chroma_adapter: Optional[ChromaDBAdapter] = None


async def get_vector_store() -> ChromaDBAdapter:
    global _chroma_adapter
    if _chroma_adapter is None:
        _chroma_adapter = ChromaDBAdapter()
        await _chroma_adapter.initialize()
    return _chroma_adapter
