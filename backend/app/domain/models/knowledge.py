"""Domain model: Knowledge chunk."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeChunk:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    source: str = ""
    module: str = ""  # subscription, order, billing, pricing, orchestration
    collection: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "module": self.module,
            "collection": self.collection,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class KnowledgeSearchResult:
    chunk: KnowledgeChunk
    score: float  # similarity score 0.0 – 1.0
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "score": self.score,
            "chunk": self.chunk.to_dict(),
        }
