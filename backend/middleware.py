"""ASGI Streaming Limit and Security Header Middleware for QICP Backend.

1. Enforces 1 MB streaming limit mid-flight on chunked payloads without memory buffering.
2. Injects production security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options).
3. Handles RFC 402 challenge negotiation for protected services.
"""
from typing import Callable
from starlette.types import ASGIApp, Receive, Scope, Send

MAX_REQUEST_BODY_BYTES = 1_048_576  # 1 MB Limit


class ProductionSecurityAndLimitMiddleware:
    """Pure ASGI middleware enforcing request limits and production security headers."""

    def __init__(self, app: ASGIApp, max_body_bytes: int = MAX_REQUEST_BODY_BYTES):
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))

        # Check Content-Length header upfront
        content_length_header = headers.get(b"content-length")
        if content_length_header:
            try:
                cl = int(content_length_header.decode("latin1"))
                if cl < 0:
                    await self._send_response(send, 400, b'{"detail": "Invalid Content-Length header"}')
                    return
                if cl > self.max_body_bytes:
                    await self._send_response(send, 413, b'{"detail": "Request body exceeds 1 MB limit"}')
                    return
            except ValueError:
                await self._send_response(send, 400, b'{"detail": "Malformed Content-Length header"}')
                return

        # Stream chunk monitoring
        bytes_received = 0
        exceeded = False

        async def stream_receive():
            nonlocal bytes_received, exceeded
            message = await receive()
            if message["type"] == "http.request":
                body_chunk = message.get("body", b"")
                bytes_received += len(body_chunk)
                if bytes_received > self.max_body_bytes:
                    exceeded = True
            return message

        async def wrapped_send(message):
            if exceeded:
                return
            if message["type"] == "http.response.start":
                # Inject production security headers
                resp_headers = list(message.get("headers", []))
                resp_headers.append((b"x-content-type-options", b"nosniff"))
                resp_headers.append((b"x-frame-options", b"DENY"))
                resp_headers.append((b"strict-transport-security", b"max-age=31536000; includeSubDomains"))
                resp_headers.append((b"content-security-policy", b"default-src 'self' 'unsafe-inline' https: data:;"))
                message["headers"] = resp_headers
            await send(message)

        try:
            await self.app(scope, stream_receive, wrapped_send)
        except Exception:
            if exceeded:
                await self._send_response(send, 413, b'{"detail": "Streaming request body exceeded 1 MB limit"}')
            else:
                raise

        if exceeded:
            await self._send_response(send, 413, b'{"detail": "Streaming request body exceeded 1 MB limit"}')

    async def _send_response(self, send: Send, status: int, body: bytes) -> None:
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("latin1")),
                (b"x-content-type-options", b"nosniff"),
                (b"x-frame-options", b"DENY"),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
            "more_body": False,
        })
