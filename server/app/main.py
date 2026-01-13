"""FastAPI application entry point."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db, init_db
from app.middleware.auth import init_firebase
from app.routers import auth as auth_router
from app.routers import chat as chat_router
from app.routers import drafts as drafts_router
from app.routers import roadmaps as roadmaps_router
from app.services.ai_service import init_gemini

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(colors=True),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    settings = get_settings()
    logger.info(
        "Starting application",
        environment=settings.environment,
        port=settings.port,
    )

    # Initialize Firebase
    init_firebase()

    # Initialize Gemini AI
    init_gemini()

    # Initialize database
    await init_db()

    yield

    # Cleanup
    await close_db()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Learning Roadmap API",
        description="API for the Learning Roadmap App",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "environment": settings.environment}

    # Include routers
    app.include_router(auth_router.router, prefix="/api/v1")
    app.include_router(chat_router.router, prefix="/api/v1")
    app.include_router(drafts_router.router, prefix="/api/v1")
    app.include_router(roadmaps_router.router, prefix="/api/v1")

    return app


app = create_app()
