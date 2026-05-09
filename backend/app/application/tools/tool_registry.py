"""MCP-compatible tool registry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    module: str = "general"
    read_only: bool = True


class ToolRegistry:
    """Registry for all diagnostic tools, compatible with MCP tool spec."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return MCP-compatible tool list."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": {
                    "type": "object",
                    "properties": t.parameters,
                },
                "module": t.module,
                "readOnly": t.read_only,
            }
            for t in self._tools.values()
        ]

    async def execute(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        tool = self.get(name)
        if not tool:
            return {"error": f"Tool '{name}' not found"}
        if not tool.read_only:
            return {"error": "Write tools are disabled in Phase 1"}
        try:
            result = await tool.handler(**kwargs)
            return {"content": result, "tool": name, "status": "success"}
        except Exception as exc:
            return {"error": str(exc), "tool": name, "status": "error"}


tool_registry = ToolRegistry()
