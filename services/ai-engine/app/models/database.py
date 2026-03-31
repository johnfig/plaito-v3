from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.config import settings

if TYPE_CHECKING:
    from supabase import Client

_client: Any = None


def get_supabase() -> Any:
    global _client
    if _client is None:
        if settings.supabase_service_key:
            from supabase import create_client
            _client = create_client(settings.supabase_url, settings.supabase_service_key)
        else:
            from app.models.memory_db import InMemoryDB
            _client = InMemoryDB()
    return _client
