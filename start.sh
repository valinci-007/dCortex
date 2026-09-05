#!/usr/bin/env bash
# Start (or restart) the Crew Ops Advisor on this laptop, in the foreground, with the
# console audit trail visible.
#
#   ./start.sh                 stop any running instance, build what is missing, serve on :8010
#   ./start.sh --stop          just stop the running instance
#   ./start.sh --quiet         no audit console (CREW_OPS_AUDIT_LOG=0)
#   ./start.sh --full          PII mode "full" (names sent to the model as-is)
#   ./start.sh --port 9000     another port
#   ./start.sh --rebuild       force a fresh database and frontend build first
#
# Environment variables still win over the defaults set here (e.g. CREW_OPS_LLM_PROVIDER,
# CREW_OPS_STT_PROVIDER=sarvam, SARVAM_API_KEY); backend/.env is read by the app itself.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
BIN="$BACKEND/.venv/bin"

PORT="${PORT:-8010}"
PII_MODE="${CREW_OPS_PII_MODE:-minimal}"
AUDIT="${CREW_OPS_AUDIT_LOG:-1}"
REBUILD=0
STOP_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stop) STOP_ONLY=1 ;;
    --quiet) AUDIT=0 ;;
    --full) PII_MODE=full ;;
    --port) PORT="$2"; shift ;;
    --rebuild) REBUILD=1 ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "unknown option: $1 (try --help)" >&2; exit 2 ;;
  esac
  shift
done

say() { printf '\033[1;36m▸ %s\033[0m\n' "$*"; }

# ---- stop whatever is running ----------------------------------------------------------
if pgrep -f "crew-ops serve" >/dev/null 2>&1; then
  say "stopping the running Crew Ops Advisor"
  pkill -f "crew-ops serve" || true
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    pgrep -f "crew-ops serve" >/dev/null 2>&1 || break
    sleep 0.5
  done
fi
if [[ $STOP_ONLY -eq 1 ]]; then
  say "stopped"
  exit 0
fi

# ---- first-time setup ------------------------------------------------------------------
if [[ ! -x "$BIN/crew-ops" ]]; then
  say "backend virtualenv not found — running make setup (one-off, a few minutes)"
  make -C "$ROOT" setup
fi
if [[ ! -d "$FRONTEND/node_modules" ]]; then
  say "frontend dependencies not found — npm install"
  (cd "$FRONTEND" && npm install --no-audit --no-fund)
fi

# ---- database: build when missing, forced, or older than the dataset --------------------
DB="$BACKEND/var/crew_ops.db"
if [[ $REBUILD -eq 1 || ! -f "$DB" ]] || [[ -n "$(find "$BACKEND/data" -name '*.json' -newer "$DB" 2>/dev/null | head -1)" ]]; then
  say "building the database from backend/data"
  make -C "$BACKEND" db
fi

# ---- frontend: build when missing, forced, or older than its sources --------------------
DIST="$FRONTEND/dist/index.html"
if [[ $REBUILD -eq 1 || ! -f "$DIST" ]] || [[ -n "$(find "$FRONTEND/src" -type f -newer "$DIST" 2>/dev/null | head -1)" ]]; then
  say "building the frontend"
  (cd "$FRONTEND" && npm run build)
fi

# ---- port check ------------------------------------------------------------------------
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "port $PORT is in use by another process:" >&2
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >&2
  echo "pick another with: ./start.sh --port <n>" >&2
  exit 1
fi

# ---- go --------------------------------------------------------------------------------
say "Crew Ops Advisor → http://127.0.0.1:$PORT   (PII mode: $PII_MODE · audit console: $AUDIT · Ctrl+C to stop)"
cd "$BACKEND"
exec env CREW_OPS_PII_MODE="$PII_MODE" CREW_OPS_AUDIT_LOG="$AUDIT" "$BIN/crew-ops" serve --port "$PORT"
