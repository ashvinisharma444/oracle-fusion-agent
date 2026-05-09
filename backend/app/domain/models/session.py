"""Domain model: Browser session."""
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    IDLE = "idle"
    ERROR = "error"
    CLOSED = "closed"
    MFA_PENDING = "mfa_pending"


@dataclass
class BrowserSession:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    tenant_url: str = ""
    status: SessionStatus = SessionStatus.IDLE
    current_url: Optional[str] = None
    cookies_path: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None
    page_title: Optional[str] = None

    def touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)

    def mark_error(self, message: str) -> None:
        self.status = SessionStatus.ERROR
        self.error_message = message

    @property
    def uptime_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.created_at).total_seconds()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tenant_url": self.tenant_url,
            "status": self.status.value,
            "current_url": self.current_url,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "error_message": self.error_message,
            "page_title": self.page_title,
        }
