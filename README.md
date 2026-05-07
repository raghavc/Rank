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

In Xcode, pick any iPhone simulator and press Run. The app reads `RankAPIBaseURL` from `Info.plist` (default `http://localhost:8000`), so the simulator hits the local API directly.

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

Production hardening omitted in this codebase (see [Connect signing](https://teller.io/docs/guides/connect)): Teller recommends a **server-issued nonce** and **Ed25519 verification** of enrollment `signatures`. For embedded iOS WKWebViews, consider Teller's first-party [TellerKit](https://github.com/tellerhq/tellerkit) if you migrate off `connect.js` in WKWebView.

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
- `slowapi` rate limiting is in-process; for multi-instance deploys, wire it to the Redis backend.
- `crypto.py` uses AES-256-GCM. The `TELLER_TOKEN_ENC_KEY` must be 32 raw bytes, base64-encoded — rotating it invalidates every stored Teller token.
- The daily refresh runs at 04:00 UTC. Adjust in `app/workers/celery_app.py`.
