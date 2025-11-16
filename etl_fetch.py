# etl_fetch.py
import time
from datetime import datetime, timezone
import pathlib
import json
import aiohttp
import pandas as pd

DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

async def timed_get(session, url, headers=None, params=None):
    """GET with latency & payload metrics."""
    t0 = time.perf_counter()
    async with session.get(url, headers=headers, params=params) as resp:
        payload = await resp.read()
        latency = time.perf_counter() - t0
        size = len(payload)
        rate_headers = {
            "x-ratelimit-limit": resp.headers.get("x-ratelimit-limit"),
            "x-ratelimit-remaining": resp.headers.get("x-ratelimit-remaining"),
            "retry-after": resp.headers.get("retry-after"),
        }
        return resp.status, payload, latency, size, rate_headers

def append_perf(provider, endpoint_key, status, latency_s, bytes_len, rl_dict):
    """Append one perf row to data/perf_log.parquet (creates if missing)."""
    df = pd.DataFrame([{
        "ts": now_iso(),
        "provider": provider,
        "endpoint": endpoint_key,
        "status": status,
        "latency_ms": round(latency_s * 1000, 1),
        "bytes": bytes_len,
        "ratelimit_limit": rl_dict.get("x-ratelimit-limit"),
        "ratelimit_remaining": rl_dict.get("x-ratelimit-remaining"),
        "retry_after": rl_dict.get("retry-after"),
    }])
    out = DATA_DIR / "perf_log.parquet"
    if out.exists():
        old = pd.read_parquet(out)
        df = pd.concat([old, df], ignore_index=True)
    df.to_parquet(out, index=False)
