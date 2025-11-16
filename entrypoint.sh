#!/bin/sh
set -e

FETCH_INTERVAL_SECONDS=3600   # 3600 = 1 hour, change if you want

# Run fetch in a background loop
(
  while true; do
    echo "[entrypoint] Running periodic data fetch..."
    python run_fetch_all.py || echo "[entrypoint] Data fetch failed (will retry)"
    echo "[entrypoint] Sleeping for ${FETCH_INTERVAL_SECONDS}s..."
    sleep "$FETCH_INTERVAL_SECONDS"
  done
) &

echo "[entrypoint] Starting Streamlit..."
exec streamlit run app_streamlit.py \
    --server.port=8501 \
    --server.address=0.0.0.0
