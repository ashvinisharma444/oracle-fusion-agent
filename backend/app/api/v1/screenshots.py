"""Screenshot endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.api.schemas.requests import CaptureScreenshotRequest
from app.application.services.session_service import session_service
from app.core.exceptions import OracleFusionAgentError
from app.core.logging import get_logger
from app.core.security import get_current_user
from app.infrastructure.browser.screenshot_service import screenshot_service
from app.infrastructure.database.postgres import AsyncSessionLocal, ScreenshotORM
from sqlalchemy import select, desc

logger = get_logger(__name__)
router = APIRouter()


@router.post("", summary="Capture a screenshot from an active session")
async def capture_screenshot(
    request: CaptureScreenshotRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        shot, image_bytes = await screenshot_service.capture(
            session_id=request.session_id,
            page_type=request.page_type,
            description=request.description,
        )
        return {
            "screenshot": shot.to_dict(),
            "image_base64": screenshot_service.to_base64(image_bytes) if image_bytes else None,
        }
    except OracleFusionAgentError:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("", summary="List screenshots")
async def list_screenshots(
    session_id: str = None,
    diagnostic_id: str = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    async with AsyncSessionLocal() as db:
        q = select(ScreenshotORM).order_by(desc(ScreenshotORM.captured_at)).limit(limit)
        if session_id:
            q = q.where(ScreenshotORM.session_id == session_id)
        if diagnostic_id:
            q = q.where(ScreenshotORM.diagnostic_id == diagnostic_id)
        result = await db.execute(q)
        rows = result.scalars().all()

    return {
        "screenshots": [
            {
                "id": r.id,
                "session_id": r.session_id,
                "url": r.url,
                "page_type": r.page_type,
                "captured_at": r.captured_at.isoformat() if r.captured_at else None,
                "file_size_bytes": r.file_size_bytes,
            }
            for r in rows
        ],
        "count": len(rows),
    }


@router.get("/{screenshot_id}/image", summary="Get screenshot image bytes")
async def get_screenshot_image(
    screenshot_id: str,
    current_user: dict = Depends(get_current_user),
):
    image_bytes = screenshot_service.read_screenshot_bytes(screenshot_id)
    if not image_bytes:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return Response(content=image_bytes, media_type="image/png")
