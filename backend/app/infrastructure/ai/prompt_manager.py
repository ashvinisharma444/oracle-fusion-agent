"""Prompt template manager for versioned prompt management."""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class PromptTemplate:
    def __init__(self, name: str, version: str, builder: Callable[..., str]) -> None:
        self.name = name
        self.version = version
        self.builder = builder

    def render(self, **kwargs: Any) -> str:
        return self.builder(**kwargs)


class PromptManager:
    """Registry for all prompt templates with versioning support."""

    def __init__(self) -> None:
        self._templates: Dict[str, PromptTemplate] = {}

    def register(self, name: str, version: str, builder: Callable[..., str]) -> None:
        self._templates[f"{name}:{version}"] = PromptTemplate(name, version, builder)
        self._templates[name] = PromptTemplate(name, version, builder)  # Always points to latest

    def get(self, name: str, version: Optional[str] = None) -> PromptTemplate:
        key = f"{name}:{version}" if version else name
        template = self._templates.get(key)
        if not template:
            raise KeyError(f"Prompt template '{key}' not found")
        return template

    def render(self, name: str, version: Optional[str] = None, **kwargs: Any) -> str:
        return self.get(name, version).render(**kwargs)

    def list_templates(self) -> Dict[str, str]:
        return {k: v.version for k, v in self._templates.items() if ":" not in k}


# ── Global instance ───────────────────────────────────────────────────────────
prompt_manager = PromptManager()
