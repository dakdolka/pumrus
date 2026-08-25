# UmRus release and handover

## First deployment after this release

1. Make a database backup.
2. Add new values from `.env.example`, especially `ADMIN_TOKEN` and
   `BACKEND_INTERNAL_TOKEN`.
3. Pull and rebuild images.
4. Start PostgreSQL and backend first; Alembic applies migrations automatically.
5. Start the bot and verify `/start`.
6. Build/publish the frontend using the existing reverse proxy.

```bash
docker compose build backend tg_bot frontend
docker compose up -d postgres postgres_backup media_backup media_init backend tg_bot
docker compose run --rm frontend npm run build
docker compose logs --tail=200 backend tg_bot postgres_backup media_backup
```

## Acceptance checks

- `/api/healthz` returns `ok`;
- `/form/` rejects a wrong key and opens with `ADMIN_TOKEN`;
- the Overview page has no critical integrity warnings;
- create a hidden test topic, add a block, preview, publish, then archive it;
- edit one exercise and solve its new version as a learner;
- upload an image in the theory editor and open it in learner view;
- Telegram `/start` creates or updates the learner profile;
- an anonymous browser cannot open Telegram mistakes or another session;
- for enabled payments, complete a sandbox payment and verify access;
- `backups/postgres` contains a fresh non-empty `.sql.gz` and
  `backups/media` contains a fresh `.tar.gz`. Copy these directories to
  another machine or object storage: a backup on the same server is only the
  first line of defence.

## Rollback

Roll back the application image or commit normally. Do not blindly run Alembic
downgrade after the form has created settings, media or manual access grants.
Restore the pre-release dump into a separate PostgreSQL instance first.

## Reverse proxy contract

- `/api/*` → backend port 8000;
- `/form` redirects to `/form/`;
- `/form/*` and browser routes use the correct Vite HTML fallback;
- request bodies allow at least `MEDIA_MAX_BYTES`;
- HTTPS is mandatory for Telegram and payments.
