# PostgreSQL data lifecycle

The legacy MySQL import and v2 transformations are complete historical rollout
steps. New installations use only PostgreSQL and Alembic.

## Schema updates

The backend starts with `alembic upgrade head`. Preview a migration before a
release by reading its file in `alembic/versions_postgresql`; never edit an
already deployed revision.

```bash
docker compose run --rm backend alembic current
docker compose run --rm backend alembic heads
```

## Content updates

Theory, practice, demo membership, pricing and public application copy are
managed through `/form/`. Curated publication scripts are not part of normal
startup and must not be used after editors have changed live content unless a
specific one-time data migration has been reviewed.

## Backup and restore drill

The `postgres_backup` service writes daily compressed plain-SQL dumps to its
named volume. Copy a dump to the host and restore it to a separate database:

```bash
gunzip -c pumrus-YYYYMMDD-HHMMSS.sql.gz | \
  docker compose exec -T postgres psql -U pumrus -d pumrus_restore_test
```

Compare record counts and open the application against the test database before
any production switch. A backup that has never been restored is not considered
verified.

The old importer scripts remain for provenance only. They are not safe as a
routine synchronization mechanism and should not be run against the active v2
database.
