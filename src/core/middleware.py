"""
Tenant context middleware.
Sets the PostgreSQL session variable for Row-Level Security.
"""
import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts tenant_id from the request header
    and binds it to structlog context for all downstream log lines.

    Note: The actual PostgreSQL RLS session variable (app.current_tenant_id)
    is set at the database session level in the dependency injection layer,
    not here. This middleware handles logging context only.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        tenant_id = request.headers.get("X-Tenant-Id")
        user_id = request.headers.get("X-User-Id")

        structlog.contextvars.clear_contextvars()
        if tenant_id:
            structlog.contextvars.bind_contextvars(tenant_id=tenant_id)
        if user_id:
            structlog.contextvars.bind_contextvars(user_id=user_id)

        response = await call_next(request)
        return response
