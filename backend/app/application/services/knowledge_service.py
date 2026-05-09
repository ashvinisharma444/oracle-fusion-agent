"""Knowledge retrieval and ingestion service."""
from __future__ import annotations

from typing import List, Optional

from app.config.settings import settings
from app.core.logging import get_logger
from app.domain.models.knowledge import KnowledgeChunk, KnowledgeSearchResult
from app.infrastructure.vector.chromadb_adapter import get_chromadb_adapter
from app.infrastructure.vector.embedding_service import embedding_service

logger = get_logger(__name__)

ALL_COLLECTIONS = [
    settings.chromadb_collection_oracle_docs,
    settings.chromadb_collection_rca_history,
    settings.chromadb_collection_config_guides,
    settings.chromadb_collection_sql_patterns,
]


class KnowledgeService:
    """Orchestrates knowledge retrieval for diagnostic augmentation."""

    async def search_for_diagnostic(
        self,
        query: str,
        module: str,
        top_k: int = 10,
    ) -> str:
        """Search knowledge base and return formatted context string for AI."""
        if not settings.enable_knowledge_retrieval:
            return ""

        adapter = get_chromadb_adapter()
        results = await adapter.search_multi_collection(
            query=query,
            collections=ALL_COLLECTIONS,
            top_k=top_k,
            module_filter=module if module else None,
        )

        if not results:
            logger.info("no_knowledge_found", query=query[:50], module=module)
            return ""

        context_parts = []
        for result in results:
            source = result.chunk.source or "Oracle Documentation"
            context_parts.append(
                f"[Source: {source} | Score: {result.score:.2f}]\n{result.chunk.content}"
            )

        logger.info("knowledge_retrieved", count=len(results), module=module)
        return "\n\n---\n\n".join(context_parts)

    async def semantic_search(
        self,
        query: str,
        collection: Optional[str] = None,
        module_filter: Optional[str] = None,
        top_k: int = 10,
    ) -> List[KnowledgeSearchResult]:
        """Raw semantic search returning structured results."""
        adapter = get_chromadb_adapter()
        if collection:
            return await adapter.search(
                query=query,
                collection=collection,
                top_k=top_k,
                module_filter=module_filter,
            )
        return await adapter.search_multi_collection(
            query=query,
            collections=ALL_COLLECTIONS,
            top_k=top_k,
            module_filter=module_filter,
        )

    async def ingest_document(
        self,
        content: str,
        source: str,
        module: str,
        doc_type: str = "documentation",
    ) -> List[str]:
        """Ingest a document into the knowledge base."""
        chunks = embedding_service.prepare_oracle_doc(content, source, module, doc_type)
        adapter = get_chromadb_adapter()
        collection = settings.chromadb_collection_oracle_docs
        ids = await adapter.ingest(chunks, collection)
        logger.info("document_ingested", source=source, chunks=len(ids))
        return ids

    async def ingest_rca(
        self,
        rca_text: str,
        entity_id: str,
        module: str,
        severity: str,
    ) -> List[str]:
        """Persist an RCA result as knowledge for future retrieval."""
        chunks = embedding_service.prepare_rca_history(rca_text, entity_id, module, severity)
        adapter = get_chromadb_adapter()
        ids = await adapter.ingest(chunks, settings.chromadb_collection_rca_history)
        logger.info("rca_ingested", entity_id=entity_id, chunks=len(ids))
        return ids

    async def get_collection_stats(self) -> dict:
        adapter = get_chromadb_adapter()
        stats = {}
        for coll in ALL_COLLECTIONS:
            stats[coll] = await adapter.collection_stats(coll)
        return stats


knowledge_service = KnowledgeService()
