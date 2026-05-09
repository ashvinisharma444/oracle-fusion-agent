"""
FastAPI middleware: correlation IDs, auth, request logging, rate limiting.
"""
import time
import uuid
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AgentBaseException, AuthenticationError
from app.core.logging import get_logger, set_correlation_id
from app.core.security import decode_token

logger = get_logger(__name__)

EXCLUDED_PATHS = {"/health", "/ready", "/metrics", "/api/v1/auth/login", "/docs", "/openapi.json"}


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Injects X-Correlation-ID header into every request/response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        set_correlation_id(correlation_id)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with duration and status code."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=request.client.host if request.client else "unknown",
        )
        return response


class AuthMiddleware(BaseHTTPMiddleware):
    """Validates JWT Bearer token on protected routes."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in EXCLUDED_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error_code": "MISSING_TOKEN", "message": "Authorization header required"},
            )

        token = auth_header.removeprefix("Bearer ").strip()
        try:
            payload = decode_token(token)
            request.state.user_id = payload["sub"]
            request.state.user_role = payload.get("role", "viewer")
        except AgentBaseException as e:
            return JSONResponse(status_code=e.status_code, content=e.to_dict())

        return await call_next(request)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Converts domain exceptions to structured JSON responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except AgentBaseException as e:
            logger.warning("domain_exception", error_code=e.error_code, message=e.message)
            return JSONResponse(status_code=e.status_code, content=e.to_dict())
        except Exception as e:
            logger.exception("unhandled_exception", error=str(e))
            return JSONResponse(
                status_code=500,
                content={"error_code": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
            )


def register_middleware(app: FastAPI) -> None:
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIDMiddleware)
