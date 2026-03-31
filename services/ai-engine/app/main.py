"""Plaito AI Engine — FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import health, llm, mastery, predict


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — seed demo data when using in-memory DB
    if not settings.supabase_service_key:
        from app.models.database import get_supabase
        from app.models.memory_db import InMemoryDB
        db = get_supabase()
        if isinstance(db, InMemoryDB):
            from app.seed import seed_database
            seed_database(db)
            print("Seeded in-memory database with demo data")
    yield
    # Shutdown


app = FastAPI(
    title="Plaito AI Engine",
    description="Grade prediction and knowledge graph API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow mobile app and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(predict.router)
app.include_router(mastery.router)
app.include_router(llm.router)
