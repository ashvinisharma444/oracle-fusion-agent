"""Embedding pipeline for knowledge ingestion."""
from __future__ import annotations

import re
from typing import List

from app.config.settings import settings
from app.core.exceptions import EmbeddingError
from app.core.logging import get_logger
from app.domain.models.knowledge import KnowledgeChunk

logger = get_logger(__name__)

CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 50     # overlap between chunks


class EmbeddingService:
    """Handles text chunking and embedding for knowledge base ingestion."""

    def chunk_text(self, text: str, source: str, module: str = "") -> List[KnowledgeChunk]:
        """Split text into overlapping chunks for ingestion."""
        # Clean text
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= CHUNK_SIZE:
            return [KnowledgeChunk(content=text, source=source, module=module)]

        chunks: List[KnowledgeChunk] = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            # Try to break at sentence boundary
            if end < len(text):
                last_period = text.rfind(".", start, end)
                if last_period > start + CHUNK_SIZE // 2:
                    end = last_period + 1

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    KnowledgeChunk(
                        content=chunk_text,
                        source=source,
                        module=module,
                        metadata={"chunk_index": len(chunks), "start_char": start},
                    )
                )
            start = end - CHUNK_OVERLAP

        logger.debug("text_chunked", source=source, chunks=len(chunks))
        return chunks

    def prepare_oracle_doc(
        self,
        content: str,
        source: str,
        module: str,
        doc_type: str = "documentation",
    ) -> List[KnowledgeChunk]:
        """Prepare an Oracle documentation chunk with rich metadata."""
        chunks = self.chunk_text(content, source, module)
        for chunk in chunks:
            chunk.metadata.update({
                "doc_type": doc_type,
                "module": module,
                "source": source,
            })
            chunk.collection = settings.chromadb_collection_oracle_docs
        return chunks

    def prepare_rca_history(
        self,
        rca_text: str,
        entity_id: str,
        module: str,
        severity: str,
    ) -> List[KnowledgeChunk]:
        """Prepare a past RCA for storage as knowledge."""
        chunks = self.chunk_text(rca_text, source=f"rca:{entity_id}", module=module)
        for chunk in chunks:
            chunk.metadata.update({
                "entity_id": entity_id,
                "severity": severity,
                "doc_type": "rca_history",
            })
            chunk.collection = settings.chromadb_collection_rca_history
        return chunks


embedding_service = EmbeddingService()
