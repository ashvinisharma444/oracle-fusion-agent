"""Browser session management endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.api.schemas.requests import CreateSessionRequest
from app.api.schemas.responses import SessionStatusResponse
from app.infrastructure.browser.playwright_adapter import get_browser_adapter

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("", response_model=List[SessionStatusResponse], summary="List active browser sessions")
async def list_sessions():
    adapter = get_browser_adapter()
    sessions = await adapter.get_active_sessions()
    return [
        SessionStatusResponse(
            session_id=s.session_id,
            status=s.status.value,
            tenant_url=s.tenant_url,
            authenticated=s.authenticated,
            current_url=s.current_url,
            created_at=s.created_at,
            last_used_at=s.last_used_at,
        )
        for s in sessions
    ]


@router.post("", response_model=SessionStatusResponse, summary="Create a new browser session")
async def create_session(body: CreateSessionRequest):
    adapter = get_browser_adapter()
    session = await adapter.create_session(body.tenant_url)
    return SessionStatusResponse(
        session_id=session.session_id,
        status=session.status.value,
        tenant_url=session.tenant_url,
        authenticated=session.authenticated,
        current_url=session.current_url,
        created_at=session.created_at,
        last_used_at=session.last_used_at,
    )


@router.delete("/{session_id}", summary="Close a browser session")
async def close_session(session_id: str):
    adapter = get_browser_adapter()
    await adapter.close_session(session_id)
    return {"message": f"Session {session_id} closed"}


@router.get("/{session_id}", response_model=SessionStatusResponse, summary="Get session status")
async def get_session(session_id: str):
    adapter = get_browser_adapter()
    session = await adapter.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return SessionStatusResponse(
        session_id=session.session_id,
        status=session.status.value,
        tenant_url=session.tenant_url,
        authenticated=session.authenticated,
        current_url=session.current_url,
        created_at=session.created_at,
        last_used_at=session.last_used_at,
    )
