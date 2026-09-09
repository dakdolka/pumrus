#!/bin/sh
set -eu

backup_path="${1:?Pass a .sql.gz backup path}"
restore_database="pumrus_restore_check_$$"
sql_temporary="/tmp/pumrus-restore-check-$$.sql"

cleanup() {
  dropdb --if-exists "${restore_database}" >/dev/null 2>&1 || true
  rm -f "${sql_temporary}"
}
trap cleanup EXIT INT TERM

gzip -t "${backup_path}"
gzip -dc "${backup_path}" > "${sql_temporary}"
test -s "${sql_temporary}"

dropdb --if-exists "${restore_database}"
createdb "${restore_database}"
psql --set ON_ERROR_STOP=1 --dbname "${restore_database}" --file "${sql_temporary}" >/dev/null

table_count="$(psql --tuples-only --no-align --dbname "${restore_database}" \
  --command "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")"
test "${table_count}" -gt 0

echo "Backup restore verified: ${table_count} public tables"
