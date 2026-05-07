# Rank

A minimalist iOS app that ranks your checking + savings balance against everyone else, anonymously, by global pool and by age bucket. Bank data via [Teller](https://teller.io). No PFPs, no real names — just an auto-generated handle like `silent-otter-4821`.

## Stack

| Layer    | Tech                                                                |
| -------- | ------------------------------------------------------------------- |
| Backend  | Python 3.11, FastAPI, SQLAlchemy 2 (async), Alembic, Celery, Redis  |
| Database | Postgres 15                                                         |
| Bank     | Teller (developer tier, mTLS + Basic auth)                          |
| Auth     | Custom JWT (HS256), bcrypt password hashing                         |
| iOS      | Swift 6 / SwiftUI / iOS 17+ (project targets iOS 26.4)              |
| Dev env  | Docker Compose                                                      |

## Prerequisites

- Docker Desktop (or compatible)
- Xcode 16 or newer
- Python 3.11 (only needed for running tests outside Docker)

## First-time setup

```bash
# 1. Get the env file ready
cp .env.example .env

# 2. Generate real secrets (paste these into .env)
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(48))"
python3 -c "import os,base64; print('TELLER_TOKEN_ENC_KEY=' + base64.b64encode(os.urandom(32)).decode())"

# 3. Set TELLER_APP_ID in .env (from https://teller.io/dashboard)

# 4. Make sure the Teller mTLS certs are in ./certs/ (already extracted from teller.zip)
ls certs/   # certificate.pem  private_key.pem

# 5. Bring everything up and run migrations
make up
make migrate
```

The API is now serving on `http://localhost:8000` with a Celery worker + beat scheduler running. Hit `http://localhost:8000/` for a healthcheck and `http://localhost:8000/docs` for the OpenAPI explorer.

## Running the iOS app

```bash
make ios          # opens RichRank.xcodeproj
```

In Xcode, pick any iPhone simulator and press Run. Debug builds inject `RankAPIBaseURL` from `Config/Debug.xcconfig` (`http://127.0.0.1:8000`). URLs there must be **double-quoted**; otherwise xcconfig treats `//` as a comment and the host/port is chopped off (requests wrongly go to port 80).

**Physical device:** copy `Config/Local.xcconfig.example` to `Config/Local.xcconfig` (gitignored) and set `RANK_API_BASE_URL` to `http://<your-mac-LAN-ip>:8000`. On a phone, `localhost` is the device itself, not your computer.

Release builds use `Config/Release.xcconfig`; replace the placeholder production URL before shipping.

### End-to-end Teller test

1. Set **`TELLER_ENVIRONMENT=sandbox`** in `.env`, recreate the API/worker containers (`docker compose up -d --force-recreate api worker beat`) so Connect uses the same env as [Sandbox] banks.
2. Sign up in the app (any email, password ≥ 8 chars, any DOB ≥ 18 years ago).
2. After the welcome card showing your generated handle, tap **Connect Bank**.
3. In the Teller Connect web sheet, pick **Capital One** (or any institution flagged as `[Sandbox]`) and use Teller's sandbox creds: username `username_good`, password `password_good`.
4. Pick a checking account → finish.
5. Your initial balance is fetched immediately. The leaderboard appears.

To trigger an out-of-band leaderboard refresh without waiting for 04:00 UTC:

```bash
docker compose exec worker python -c "from app.workers.refresh_balances import refresh_all_balances; refresh_all_balances()"
```

## Teller environments (Connect + API)

`/bank/connect-token` returns **`TELLER_ENVIRONMENT`** from `.env`. It must align with **how you enroll** in Connect:

| `TELLER_ENVIRONMENT` | Use when |
| -------------------- | --------- |
| `sandbox` | [Sandbox]-labeled institutions only; synthetic data, never hits live banks. Typical iOS onboarding against `username_good` / `password_good`. |
| `development` | Real institutions **without** sandbox billing limits (100 enrollment cap); not billed. |
| `production` | Live paid traffic. |

A mismatch here (sandbox institution + `development` server env, etc.) produces confusing failures before or during `/accounts` linkage.

When `TELLER_CONNECT_SIGNING_PUBLIC_KEY` is set in `.env`, the API issues a **server nonce** for Connect and verifies enrollment **Ed25519 signatures** on `/bank/link` (see [Connect signing](https://teller.io/docs/guides/connect)). For native iOS you may also evaluate Teller’s [TellerKit](https://github.com/tellerhq/tellerkit) instead of embedding `connect.js` in WKWebView.

## Inspecting Postgres (Docker)

PostgreSQL maps to `localhost:5432` unless you remap it in Compose. Credentials default to `rank` / `rank` / database `rank`.

```bash
cd RichRank
docker compose exec db psql -U rank -d rank -c "\\dt"
docker compose exec db psql -U rank -d rank -c "SELECT COUNT(*) AS users FROM users; SELECT COUNT(*) AS bank_accounts FROM bank_accounts;"
```

Data persists in the Docker volume named in `docker-compose.yml` (e.g. `pgdata`); removing the volume wipes local data.

## Common dev commands

```bash
make up                    # start db, redis, api, worker, beat
make down                  # stop everything
make logs                  # tail api/worker/beat
make migrate               # alembic upgrade head
make revision m="msg"      # autogenerate a new migration
make test                  # run backend pytest suite
```

## Project layout

```
RichRank/
├── docker-compose.yml
├── .env.example
├── Makefile
├── README.md
├── certs/                 # gitignored — teller mTLS cert + key
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── db.py
│       ├── models/
│       ├── schemas/
│       ├── services/
│       ├── api/
│       ├── workers/
│       └── tests/
├── RichRank.xcodeproj/
└── RichRank/              # iOS source (Xcode 16 synchronized group)
    ├── RichRankApp.swift
    ├── Theme/
    ├── State/
    ├── Models/
    ├── Networking/
    ├── Auth/
    ├── Onboarding/
    ├── Leaderboard/
    └── Settings/
```

## Notes & TODOs

- Set `TELLER_APP_ID` in `.env`. Without it, `POST /bank/connect-token` and the iOS Connect sheet won't load a real institution list.
- **Teller Connect signing (recommended for production):** set `TELLER_CONNECT_SIGNING_PUBLIC_KEY` to the **Token Signing** public key (PEM) from the Teller dashboard. When set, `POST /bank/connect-token` returns a server-issued `nonce` (stored in Redis ~15m); the iOS client passes it into Connect and `/bank/link` verifies Teller’s `signatures` over `nonce`, `accessToken`, `user.id`, `enrollment.id`, and `environment` (see [Connect docs](https://teller.io/docs/guides/connect)). Omit the env var only for local/dev without signature enforcement.
- **Auth:** access JWTs are short-lived (`JWT_ACCESS_TTL_MINUTES`, default 15). Clients receive a **refresh token** (stored hashed in Postgres) and should call `POST /auth/refresh`. `POST /auth/logout` with a bearer token revokes **all** refresh sessions and bumps `token_version` so existing access JWTs stop working; send `{"refresh_token":"..."}` to revoke a single session.
- **CORS / hosts:** leave `CORS_ORIGINS` empty for iOS-only. Set `TRUSTED_HOSTS` behind a reverse proxy. Terminate TLS at the load balancer and enable **HSTS** there.
- **Rate limits:** `slowapi` limits auth + bank + leaderboard routes. For multiple API replicas, set `RATE_LIMIT_STORAGE_URI` (e.g. `redis://redis:6379/1`).
- `slowapi` defaults to in-memory storage when `RATE_LIMIT_STORAGE_URI` is unset.
- `crypto.py` uses AES-256-GCM. The `TELLER_TOKEN_ENC_KEY` must be 32 raw bytes, base64-encoded — rotating it invalidates every stored Teller token.
- The daily refresh runs at 04:00 UTC. Adjust in `app/workers/celery_app.py`.
- **Production Compose reference:** [docker-compose.prod.yml](docker-compose.prod.yml) (no code bind-mount, no `--reload`, DB/Redis not published). Dev stack keeps hot-reload via [docker-compose.yml](docker-compose.yml).
- **Secret scanning:** see [.github/workflows/secrets.yml](../../.github/workflows/secrets.yml) and [docs/SECURITY_SECRETS.md](../../docs/SECURITY_SECRETS.md).
