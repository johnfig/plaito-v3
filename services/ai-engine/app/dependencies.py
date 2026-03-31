"""FastAPI dependency injection."""

from fastapi import Header, HTTPException

from app.config import settings
from app.engines.llm_router import LLMRouter
from app.models.database import get_supabase


def get_db():
    return get_supabase()


def get_current_user(x_user_id: str = Header(default=None)) -> str:
    """Extract user ID from request headers.

    In development: accepts x-user-id header directly.
    In production: would validate Supabase JWT and extract user_id.
    """
    if settings.environment == "development" and x_user_id:
        return x_user_id

    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")

    return x_user_id


def get_llm() -> LLMRouter:
    return LLMRouter()
