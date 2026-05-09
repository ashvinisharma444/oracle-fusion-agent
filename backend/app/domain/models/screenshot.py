"""Domain model: Screenshot."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Screenshot:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    diagnostic_id: Optional[str] = None
    url: str = ""
    page_type: str = ""
    file_path: Optional[str] = None
    file_size_bytes: int = 0
    width: int = 1920
    height: int = 1080
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "diagnostic_id": self.diagnostic_id,
            "url": self.url,
            "page_type": self.page_type,
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "width": self.width,
            "height": self.height,
            "captured_at": self.captured_at.isoformat(),
            "description": self.description,
        }
