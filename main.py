from fastapi import FastAPI, Request
from routes import router

# Stand-in for real auth: the middleware "authenticates" every request as this user.
DEFAULT_USER_ID = 1

app = FastAPI()


@app.middleware("http")
async def authenticate(request: Request, call_next):
    request.state.user_id = DEFAULT_USER_ID
    return await call_next(request)


app.include_router(router, prefix="/api", tags=["playback"])
