#!/bin/sh
set -eu

mkdir -p /backups

while true; do
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  target="/backups/pumrus-${stamp}.sql.gz"
  temporary="${target}.tmp"

  if pg_dump --no-owner --no-acl | gzip -9 > "${temporary}"; then
    mv "${temporary}" "${target}"
    echo "Database backup created: ${target}"
  else
    rm -f "${temporary}"
    echo "Database backup failed" >&2
  fi

  find /backups -type f -name 'pumrus-*.sql.gz' \
    -mtime "+${BACKUP_RETENTION_DAYS:-14}" -delete
  sleep 86400
done
