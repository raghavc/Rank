from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse, JSONResponse

from app.api import auth, bank, leaderboard
from app.api.deps import limiter
from app.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
        )
        return response


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title="Rank API", version="0.1.0")

    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    if s.trusted_host_list:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=s.trusted_host_list)

    if s.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=s.cors_origin_list,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "Accept"],
        )

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(_request: Request, exc: RateLimitExceeded):
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

    @app.get("/privacy", response_class=HTMLResponse, tags=["meta"])
    async def privacy_policy() -> str:
        return """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rank – Privacy Policy</title>
<style>body{font-family:-apple-system,system-ui,sans-serif;max-width:640px;margin:40px auto;padding:0 20px;color:#222;line-height:1.6}h1{font-size:1.5em}h2{font-size:1.15em;margin-top:1.5em}</style>
</head><body>
<h1>Rank — Privacy Policy</h1>
<p><strong>Effective date:</strong> May 8, 2026</p>

<h2>What we collect</h2>
<p>Rank collects the minimum information needed to operate the leaderboard:</p>
<ul>
<li><strong>Account info:</strong> email address, date of birth (used only to determine your age bracket), and a chosen or auto-generated username.</li>
<li><strong>Bank balance:</strong> a single aggregate balance number retrieved via Teller. We never see your transactions, account numbers, or banking credentials.</li>
</ul>

<h2>What we do NOT collect</h2>
<ul>
<li>Real names, phone numbers, or physical addresses</li>
<li>Transaction history or spending data</li>
<li>Device identifiers, advertising IDs, or location data</li>
<li>Analytics, cookies, or tracking pixels</li>
</ul>

<h2>How we use your data</h2>
<p>Your balance is used solely to calculate your position on the Rank leaderboard. Your email is used for authentication only. We do not sell, share, or monetize any user data.</p>

<h2>Data storage</h2>
<p>Data is stored on secured servers (AWS). Passwords are hashed. Bank tokens are encrypted at rest.</p>

<h2>Data deletion</h2>
<p>You can delete your account at any time from the Settings screen in the app. This permanently removes all your data from our servers.</p>

<h2>Third-party services</h2>
<p>We use <a href="https://teller.io">Teller</a> to securely read your bank balance. Teller's privacy policy applies to the data they process on their end.</p>

<h2>Contact</h2>
<p>Questions? Reach us at <strong>support@rankapp.io</strong></p>
</body></html>"""

    return app


app = create_app()
