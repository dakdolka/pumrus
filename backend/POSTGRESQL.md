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
legacy MySQL database is a separate, optional stage.

## Import legacy content

The importer copies only learning content:

- theory and theory blocks;
- task theory groups and links;
- trainer tasks and task items;
- options and option sets.

It deliberately skips users, practice sessions, and mistakes.

The source MySQL database must remain available temporarily. If MySQL runs on
the Docker host, use `host.docker.internal` as its hostname.

First perform a dry run:

```bash
docker compose run --rm \
  -e LEGACY_DATABASE_URL='mysql+asyncmy://USER:PASSWORD@host.docker.internal:3306/pumrus_db' \
  backend \
  python -m app.scripts.import_legacy_content
```

The command prints source table counts and verifies that the target content
tables are empty. It does not write anything.

If the summary is correct, execute the import:

```bash
docker compose run --rm \
  -e LEGACY_DATABASE_URL='mysql+asyncmy://USER:PASSWORD@host.docker.internal:3306/pumrus_db' \
  backend \
  python -m app.scripts.import_legacy_content --execute
```

The import is performed in one PostgreSQL transaction. Any failure rolls back
all inserted content. A second import into non-empty tables is rejected.

## Transform theory into the v2 model

After the legacy content import succeeds, rebuild the backend image so the
latest Alembic migration and transformer are available:

```bash
docker compose build backend
docker compose up -d backend
```

Run the transformation plan first:

```bash
docker compose run --rm backend \
  python -m app.scripts.transform_legacy_theory
```

The plan:

- creates empty catalog entries for exam tasks 1–27;
- ignores legacy documents named `№N Общее`;
- turns confirmed learning materials into topics;
- prints every theory-to-task association;
- refuses execution if an unresolved theory remains.

When the plan is correct:

```bash
docker compose run --rm backend \
  python -m app.scripts.transform_legacy_theory --execute
```

The default active course version is `2026`. Override it when needed:

```bash
docker compose run --rm backend \
  python -m app.scripts.transform_legacy_theory \
  --course-version 2027 \
  --execute
```

The command is transactional and refuses to run if legacy theory has already
been transformed.
