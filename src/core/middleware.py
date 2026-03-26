"""
Request context middleware.

Single-user mode: No tenant context needed.
Binds request metadata to structlog for tracing.
"""

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that binds request metadata to structlog context
    for all downstream log lines.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        structlog.contextvars.clear_contextvars()

        # Generate a request ID for tracing
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response
