#!/bin/bash
# Start the FastAPI server and Celery worker together.
# Both processes are killed when this script exits (Ctrl+C).

set -e

cd "$(dirname "$0")"

source .venv/bin/activate

# server/ for config.*, ml.*, tasks.*
# server/app/ for models.*, repositories.*
export PYTHONPATH="$PWD:$PWD/app"
# PyTorch + macOS fork safety — prevents SIGABRT when loading the model in a worker
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

cleanup() {
    echo ""
    echo "Shutting down..."
    kill "$UVICORN_PID" "$CELERY_PID" "$BEAT_PID" 2>/dev/null
    wait "$UVICORN_PID" "$CELERY_PID" "$BEAT_PID" 2>/dev/null
}
trap cleanup EXIT INT TERM

echo "Starting Celery worker..."
celery -A config.celery_app.celery_app worker --loglevel=info --pool=solo &
CELERY_PID=$!

echo "Starting Celery beat..."
celery -A config.celery_app.celery_app beat --loglevel=info &
BEAT_PID=$!

echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 ${RELOAD:+--reload} &
UVICORN_PID=$!

echo "All processes running. Press Ctrl+C to stop."
wait
