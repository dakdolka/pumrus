# UmRus backend

FastAPI + PostgreSQL backend for the Telegram WebApp and browser client.

## Active architecture

- `/api/v2/*` is the only public product API.
- `/api/v2/admin/*` is the owner form API and requires `ADMIN_TOKEN`.
- `/api/v2/internal/*` is server-to-server API and requires `BACKEND_INTERNAL_TOKEN`.
- legacy MySQL-era routers remain only for migration history and are not mounted.
- Alembic is the only schema migration mechanism.
- theory and exercises are versioned; old attempts keep their original version.

Telegram `initData` is validated on the server. A client-supplied Telegram ID is
never proof of identity. Anonymous browser practice is isolated by a random
browser client ID.

## Start

```bash
docker compose up -d --build postgres backend tg_bot
docker compose logs -f backend
```

Startup runs `alembic upgrade head` and then starts the API. Content scripts are
intentionally not run on restart: `/form/` owns content and deployment cannot
silently overwrite manual publications.

## Required secrets

Copy `.env.example` to `.env` and set `POSTGRES_PASSWORD`, `TOKEN`,
`ADMIN_TOKEN` and `BACKEND_INTERNAL_TOKEN`. Use different long random values.
Never enable `ALLOW_INSECURE_ADMIN` on an internet-facing server.

## Verification

```bash
curl http://127.0.0.1:8000/healthz
docker compose exec backend alembic current
```

## Backups

`postgres_backup` and `media_backup` create database and image archives on
startup and daily. Retention defaults to 14 days.

```bash
docker compose exec postgres_backup ls -lh /backups
docker compose cp postgres_backup:/backups/pumrus-YYYYMMDD-HHMMSS.sql.gz ./
docker compose exec media_backup ls -lh /backups
```

Test restoration in a separate database before replacing the active one.

## Quality checks

```bash
docker compose run --rm backend python -m unittest discover -s tests -v
python -m compileall -q backend/app backend/alembic/versions_postgresql
```

CI also runs frontend lint/build and validates Docker Compose.
