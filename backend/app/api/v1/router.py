"""API v1 router — aggregates all route modules."""
from fastapi import APIRouter
from app.api.v1 import analyze, sessions, knowledge, health, auth

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(analyze.router)
api_router.include_router(sessions.router)
api_router.include_router(knowledge.router)
api_router.include_router(health.router)
