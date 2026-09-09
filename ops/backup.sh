#!/bin/sh
set -eu

mkdir -p /backups

while true; do
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  target="/backups/pumrus-${stamp}.sql.gz"
  dump_temporary="/backups/.pumrus-${stamp}.sql.tmp"
  archive_temporary="${target}.tmp"

  if pg_dump --no-owner --no-acl --file="${dump_temporary}" \
    && test -s "${dump_temporary}" \
    && gzip -9 -c "${dump_temporary}" > "${archive_temporary}" \
    && test -s "${archive_temporary}" \
    && gzip -t "${archive_temporary}"; then
    mv "${archive_temporary}" "${target}"
    rm -f "${dump_temporary}"
    echo "Database backup created: ${target}"
  else
    rm -f "${dump_temporary}" "${archive_temporary}"
    echo "Database backup failed" >&2
  fi

  find /backups -type f -name 'pumrus-*.sql.gz' \
    -mtime "+${BACKUP_RETENTION_DAYS:-14}" -delete
  sleep 86400
done
