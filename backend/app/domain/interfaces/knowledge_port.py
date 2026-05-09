"""Abstract vector knowledge retrieval port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.domain.models.knowledge import KnowledgeChunk, KnowledgeSearchResult


class KnowledgePort(ABC):
    """Vector knowledge store interface. Implementations: ChromaDBAdapter."""

    @abstractmethod
    async def ingest(
        self,
        chunks: List[KnowledgeChunk],
        collection: str,
    ) -> List[str]:
        """Ingest knowledge chunks into a collection. Returns list of IDs."""
        ...

    @abstractmethod
    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 5,
        module_filter: Optional[str] = None,
        score_threshold: float = 0.6,
    ) -> List[KnowledgeSearchResult]:
        """Semantic similarity search. Returns ranked results."""
        ...

    @abstractmethod
    async def search_multi_collection(
        self,
        query: str,
        collections: List[str],
        top_k: int = 10,
        module_filter: Optional[str] = None,
    ) -> List[KnowledgeSearchResult]:
        """Search across multiple collections and merge results."""
        ...

    @abstractmethod
    async def delete(self, chunk_id: str, collection: str) -> bool:
        """Delete a chunk by ID."""
        ...

    @abstractmethod
    async def collection_stats(self, collection: str) -> Dict[str, Any]:
        """Return count, last_updated, etc. for a collection."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if vector store is reachable."""
        ...
