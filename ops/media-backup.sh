#!/bin/sh
set -eu

mkdir -p /backups

while true; do
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  target="/backups/pumrus-media-${stamp}.tar.gz"
  temporary="${target}.tmp"

  if tar -C /media -czf "${temporary}" .; then
    mv "${temporary}" "${target}"
    echo "Media backup created: ${target}"
  else
    rm -f "${temporary}"
    echo "Media backup failed" >&2
  fi

  find /backups -type f -name 'pumrus-media-*.tar.gz' \
    -mtime "+${BACKUP_RETENTION_DAYS:-14}" -delete
  sleep 86400
done
