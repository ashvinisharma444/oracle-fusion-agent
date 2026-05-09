"""Unit tests for PromptManager."""
from __future__ import annotations

import pytest
from app.infrastructure.ai.prompt_manager import PromptManager, PromptTemplate


class TestPromptManager:
    def test_register_and_get(self):
        pm = PromptManager()
        pm.register("test_prompt", "v1", lambda **kwargs: f"Hello {kwargs.get('name', 'world')}")
        template = pm.get("test_prompt")
        assert template.name == "test_prompt"
        assert template.version == "v1"

    def test_render(self):
        pm = PromptManager()
        pm.register("greeting", "v1", lambda **kwargs: f"Hello {kwargs['name']}")
        result = pm.render("greeting", name="Oracle")
        assert result == "Hello Oracle"

    def test_get_unknown_raises(self):
        pm = PromptManager()
        with pytest.raises(KeyError):
            pm.get("nonexistent")

    def test_version_specific_get(self):
        pm = PromptManager()
        pm.register("test", "v1", lambda **kwargs: "v1 result")
        pm.register("test", "v2", lambda **kwargs: "v2 result")
        assert pm.render("test:v1") == "v1 result"
        assert pm.render("test:v2") == "v2 result"
        # Latest should be v2
        assert pm.render("test") == "v2 result"

    def test_list_templates(self):
        pm = PromptManager()
        pm.register("prompt_a", "v1", lambda **kwargs: "a")
        pm.register("prompt_b", "v1", lambda **kwargs: "b")
        templates = pm.list_templates()
        assert "prompt_a" in templates
        assert "prompt_b" in templates
