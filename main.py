from fastapi import FastAPI
from routes import router

# Stand-in for real auth: the middleware "authenticates" every request as this user.
DEFAULT_USER_ID = 1


class AuthMiddleware:
    """Plain ASGI middleware so it covers WebSocket connections too (@app.middleware("http") doesn't)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            scope.setdefault("state", {})["user_id"] = DEFAULT_USER_ID
        await self.app(scope, receive, send)


app = FastAPI()
app.add_middleware(AuthMiddleware)
app.include_router(router, prefix="/api", tags=["playback"])
