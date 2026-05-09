"""
Fusion tool abstractions — MCP-compatible function signatures.
These tools wrap the browser and AI layers for future agent/MCP integration.
"""
from typing import Any, Dict, List, Optional
from app.core.logging import get_logger
from app.infrastructure.browser.playwright_adapter import get_browser_adapter

logger = get_logger(__name__)


async def fusion_get_subscription(
    session_id: str,
    subscription_number: str,
    tenant_url: str,
) -> Dict[str, Any]:
    """
    Tool: Retrieve subscription details from Oracle Fusion.
    READ-ONLY. Returns structured subscription data.
    """
    from app.infrastructure.browser.page_objects.subscription_page import SubscriptionPage
    adapter = get_browser_adapter()
    sessions = adapter._sessions
    session = sessions.get(session_id)
    if not session or not session.page:
        raise ValueError(f"Browser session {session_id} not found")

    page_obj = SubscriptionPage(session.page)
    snapshot = await page_obj.extract()
    return {"tool": "fusion_get_subscription", "subscription_number": subscription_number, "data": snapshot.structured_data}


async def fusion_get_order(
    session_id: str,
    order_number: str,
) -> Dict[str, Any]:
    """
    Tool: Retrieve order details from Oracle Fusion Order Management.
    READ-ONLY.
    """
    from app.infrastructure.browser.page_objects.order_page import OrderPage
    adapter = get_browser_adapter()
    session = adapter._sessions.get(session_id)
    if not session or not session.page:
        raise ValueError(f"Browser session {session_id} not found")

    page_obj = OrderPage(session.page)
    snapshot = await page_obj.extract()
    return {"tool": "fusion_get_order", "order_number": order_number, "data": snapshot.structured_data}


async def fusion_get_orchestration(
    session_id: str,
    orchestration_id: str,
) -> Dict[str, Any]:
    """
    Tool: Retrieve orchestration process details from Oracle Fusion DOO.
    READ-ONLY.
    """
    from app.infrastructure.browser.page_objects.orchestration_page import OrchestrationPage
    adapter = get_browser_adapter()
    session = adapter._sessions.get(session_id)
    if not session or not session.page:
        raise ValueError(f"Browser session {session_id} not found")

    page_obj = OrchestrationPage(session.page)
    snapshot = await page_obj.extract()
    return {"tool": "fusion_get_orchestration", "orchestration_id": orchestration_id, "data": snapshot.structured_data}


async def fusion_capture_screenshot(
    session_id: str,
    page_type: str = "generic",
) -> Dict[str, Any]:
    """Tool: Capture screenshot of current browser page."""
    adapter = get_browser_adapter()
    screenshot_bytes = await adapter.capture_screenshot(session_id)
    import base64
    return {
        "tool": "fusion_capture_screenshot",
        "page_type": page_type,
        "screenshot_base64": base64.b64encode(screenshot_bytes).decode(),
        "size_bytes": len(screenshot_bytes),
    }


async def fusion_search_knowledge(
    query: str,
    module: Optional[str] = None,
    n_results: int = 5,
) -> Dict[str, Any]:
    """Tool: Search the Oracle knowledge base using semantic search."""
    from app.infrastructure.vector.chromadb_adapter import get_vector_store
    vector_store = await get_vector_store()
    results = await vector_store.search_all_collections(
        query=query,
        module_filter=module,
        n_results_per_collection=n_results,
    )
    return {
        "tool": "fusion_search_knowledge",
        "query": query,
        "module": module,
        "results": results,
        "count": len(results),
    }


# MCP-compatible tool registry
TOOL_REGISTRY = {
    "fusion_get_subscription": fusion_get_subscription,
    "fusion_get_order": fusion_get_order,
    "fusion_get_orchestration": fusion_get_orchestration,
    "fusion_capture_screenshot": fusion_capture_screenshot,
    "fusion_search_knowledge": fusion_search_knowledge,
}

TOOL_SCHEMAS = [
    {
        "name": "fusion_get_subscription",
        "description": "Get subscription details from Oracle Fusion Subscription Management (READ-ONLY)",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "subscription_number": {"type": "string"},
                "tenant_url": {"type": "string"},
            },
            "required": ["session_id", "subscription_number", "tenant_url"],
        },
    },
    {
        "name": "fusion_get_order",
        "description": "Get order details from Oracle Fusion Order Management (READ-ONLY)",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "order_number": {"type": "string"},
            },
            "required": ["session_id", "order_number"],
        },
    },
    {
        "name": "fusion_search_knowledge",
        "description": "Search Oracle Fusion knowledge base using semantic search",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "module": {"type": "string", "enum": ["subscription", "order", "orchestration", "billing", "pricing"]},
                "n_results": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
]
