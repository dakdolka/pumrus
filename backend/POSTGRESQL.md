# PostgreSQL rollout

The application now creates a clean PostgreSQL database. The legacy `dump.sql`
is not imported during this stage.

## Required environment

Add these values to the server `.env`:

```dotenv
POSTGRES_DB=pumrus
POSTGRES_USER=pumrus
POSTGRES_PASSWORD=replace-with-a-long-random-password
```

Keep the existing Telegram variables unchanged. `BOT_MODE` defaults to
`polling`, so the bot continues to run as before.

## Deploy

```bash
docker compose build backend
docker compose up -d postgres backend
docker compose logs -f backend
```

The backend container runs `alembic upgrade head` before starting the API.

## Verify

The backend log must contain the successful Alembic revision:

```text
20260724_0001
```

Then check:

```bash
curl http://127.0.0.1:8000/healthz
```

Expected response:

```json
{"status":"ok","database":"postgresql"}
```

The content tables are initially empty. Importing selected content from the
legacy MySQL dump is a separate, optional stage.
