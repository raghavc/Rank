from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse

from app.api import auth, bank, leaderboard
from app.api.deps import limiter


def create_app() -> FastAPI:
    app = FastAPI(title="Rank API", version="0.1.0")

    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(_request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": f"rate limit exceeded: {exc.detail}"},
        )

    app.include_router(auth.router)
    app.include_router(bank.router)
    app.include_router(leaderboard.router)

    @app.get("/", tags=["meta"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "service": "rank-api"}

    return app


app = create_app()
