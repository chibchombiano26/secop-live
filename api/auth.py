"""Shared API-key auth (REST + MCP SSE).

Env API_KEYS="key1,key2". Open paths: /health, /scalar, /openapi.json.
Clients: X-API-Key header or ?api_key=.
"""
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

OPEN = {"/health", "/openapi.json", "/scalar"}


def valid(key: str) -> bool:
    keys = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]
    if not keys:
        return True  # unconfigured: open (development)
    return bool(key) and key in keys


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in OPEN:
            return await call_next(request)
        key = request.headers.get("x-api-key") or request.query_params.get("api_key")
        if not valid(key):
            return JSONResponse({"detail": "missing or invalid api key"}, 401)
        return await call_next(request)
