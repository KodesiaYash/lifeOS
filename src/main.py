"""
FastAPI application entry point.
"""
import structlog
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    # --- Startup ---
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.get_level_from_name(settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logger.info("starting_app", app_name=settings.APP_NAME, env=settings.APP_ENV)
    yield
    # --- Shutdown ---
    logger.info("shutting_down_app")


def create_app() -> FastAPI:
    """Application factory."""
    application = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="AI-native multi-tenant life operating system",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @application.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "app": settings.APP_NAME, "env": settings.APP_ENV}

    # Register routers
    _register_routers(application)

    return application


def _register_routers(application: FastAPI) -> None:
    """Register all API routers."""
    from src.core.router import router as core_router
    from src.communication.router import router as communication_router
    from src.events.router import router as events_router

    application.include_router(core_router, prefix="/api/v1/core", tags=["core"])
    application.include_router(communication_router, prefix="/api/v1/communication", tags=["communication"])
    application.include_router(events_router, prefix="/api/v1/events", tags=["events"])


app = create_app()
