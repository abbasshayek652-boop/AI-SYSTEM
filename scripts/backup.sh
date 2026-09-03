#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"

for db in "$ROOT_DIR"/*.db; do
  [ -f "$db" ] || continue
  name="$(basename "$db" .db)"
  cp -- "$db" "$BACKUP_DIR/${name}_${STAMP}.db"
done

find "$BACKUP_DIR" -type f -name '*.db' -mtime +14 -delete
printf 'Backups written to %s\n' "$BACKUP_DIR"
