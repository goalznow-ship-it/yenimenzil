"""Request correlation ID and structured request logging.

Generates an X-Request-ID per request (honoring a client-provided ID),
logs a single structured line per request (method, path, status, duration),
and never logs bodies, headers, tokens or credentials.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("yenimenzil.request")

_SENSITIVE_PATH_PARTS = ("password", "token", "secret", "webhook", "reset")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach X-Request-ID and log structured request summaries."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": 500,
                    "duration_ms": round(elapsed_ms, 2),
                },
            )
            raise
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id

        log_method = logger.warning if response.status_code >= 500 else logger.info
        log_method(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(elapsed_ms, 2),
            },
        )
        return response
