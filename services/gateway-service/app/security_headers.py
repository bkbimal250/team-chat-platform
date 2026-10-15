from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, *, production: bool) -> None:
        self.app = app
        self._production = production

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                extra = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"x-frame-options", b"DENY"),
                    (b"content-security-policy", b"frame-ancestors 'none'"),
                    (
                        b"permissions-policy",
                        b"camera=(), microphone=(), geolocation=(), payment=()",
                    ),
                ]
                if self._production:
                    extra.append(
                        (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
                    )
                existing = {name.lower() for name, _ in headers}
                for name, value in extra:
                    if name not in existing:
                        headers.append((name, value))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)
