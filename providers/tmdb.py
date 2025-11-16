# providers/tmdb.py
import os
import json
import pandas as pd
import aiohttp

from dotenv import load_dotenv
from etl_fetch import timed_get, append_perf, DATA_DIR

# Load .env here so this module always sees the right key
load_dotenv()

TMDB_KEY = os.getenv("TMDB_API_KEY")


def _tmdb_headers_and_params():
    """
    Decide between v4 bearer token and v3 api_key, robustly.
    Supports any of these envs:
      TMDB_BEARER      -> v4 token (do NOT include the word 'Bearer ')
      TMDB_V4_TOKEN    -> v4 token (same as above)
      TMDB_API_KEY     -> either v4 token (starts with 'ey') OR a v3 key
      TMDB_V3_KEY      -> v3 key explicitly
    """
    # read all possible envs (strip whitespace/quotes)
    def _env(name):
        v = os.getenv(name)
        return v.strip().strip('"').strip("'") if v else None

    v4_candidate = _env("TMDB_BEARER") or _env("TMDB_V4_TOKEN") or _env("TMDB_API_KEY")
    v3_candidate = _env("TMDB_V3_KEY")

    # If token contains 'Bearer ' already, drop it
    if v4_candidate and v4_candidate.lower().startswith("bearer "):
        v4_candidate = v4_candidate[7:].strip()

    # Prefer a real v4 token when it looks like one (JWTs start with 'ey')
    if v4_candidate and v4_candidate.startswith("ey"):
        headers = {
            "Authorization": f"Bearer {v4_candidate}",
            "accept": "application/json",
        }
        params = None
        # --- diagnostics (safe): prints mode & last 6 chars only
        print("[tmdb] auth=V4 bearer …" + v4_candidate[-6:])
        return headers, params

    # Otherwise fall back to a v3 key (explicit or via TMDB_API_KEY)
    key = v3_candidate or (v4_candidate if v4_candidate else None)
    if key:
        headers = {"accept": "application/json"}
        params = {"api_key": key}
        print("[tmdb] auth=V3 api_key …" + key[-6:])
        return headers, params

    raise RuntimeError(
        "No TMDB credentials. Provide TMDB_BEARER (v4 token without 'Bearer '), "
        "or TMDB_V4_TOKEN, or TMDB_V3_KEY, or TMDB_API_KEY."
    )


async def fetch_tmdb_trending(media_type="all", window="day"):
    """
    Fetch TMDB trending list:
      media_type: 'all' | 'movie' | 'tv'
      window: 'day' | 'week'
    Writes/updates data/tmdb_trending.parquet and returns the dataframe.
    """
    url = f"https://api.themoviedb.org/3/trending/{media_type}/{window}"
    headers, params = _tmdb_headers_and_params()

    async with aiohttp.ClientSession() as session:
        status, payload, latency, size, rl = await timed_get(
            session, url, headers=headers, params=params
        )

    append_perf("tmdb", f"trending_{media_type}_{window}", status, latency, size, rl)

    if status != 200:
        snippet = payload.decode("utf-8", errors="ignore")[:200]
        raise RuntimeError(f"TMDB error {status}: {snippet}")

    data = json.loads(payload.decode("utf-8"))

    # One timestamp per pull (so a batch stays together)
    pull_ts = pd.Timestamp.utcnow()

    rows = []
    for r in data.get("results", []):
        rows.append({
            "ts": pull_ts,
            "window": window,  # 'day' or 'week' so the app can filter
            "id": r.get("id"),
            "media_type": r.get("media_type"),
            "title": r.get("title") or r.get("name"),
            "overview": r.get("overview"),
            "popularity": r.get("popularity"),
            "vote_average": r.get("vote_average"),
            "vote_count": r.get("vote_count"),
            "release_date": r.get("release_date") or r.get("first_air_date"),
            "poster_path": r.get("poster_path"),
        })
    df = pd.DataFrame(rows)

    out = DATA_DIR / "tmdb_trending.parquet"
    if len(df):
        if out.exists():
            old = pd.read_parquet(out)
            df = pd.concat([old, df], ignore_index=True)
        df.to_parquet(out, index=False)

    return df
# --- Streaming availability (watch/providers) ---
# Docs: /movie/{movie_id}/watch/providers and /tv/{tv_id}/watch/providers

import aiohttp

async def fetch_tmdb_providers(item_id: int, media_type: str, region: str = "US"):
    """
    Return a dict: { 'flatrate': [(provider_name, logo_path), ...], 'rent': [...], 'buy': [...] }
    for the given TMDB item and region (country code like 'US', 'IN', 'GB').
    """
    headers, params = _tmdb_headers_and_params()
    url = f"https://api.themoviedb.org/3/{media_type}/{item_id}/watch/providers"

    async with aiohttp.ClientSession() as session:
        status, payload, latency, size, rl = await timed_get(session, url, headers=headers, params=params)

    append_perf("tmdb", f"watch_providers_{media_type}_{region}", status, latency, size, rl)

    if status != 200:
        return {}

    data = json.loads(payload.decode("utf-8")).get("results", {})
    region_block = data.get(region, {}) or {}
    out = {}
    for k in ("flatrate", "rent", "buy", "free", "ads"):
        providers = region_block.get(k) or []
        out[k] = [(p.get("provider_name"), p.get("logo_path")) for p in providers]
    return out
# at bottom of providers/tmdb.py
async def fetch_tmdb_external_ids(item_id: int, media_type: str):
    headers, params = _tmdb_headers_and_params()
    url = f"https://api.themoviedb.org/3/{media_type}/{item_id}/external_ids"
    async with aiohttp.ClientSession() as session:
        status, payload, latency, size, rl = await timed_get(session, url, headers=headers, params=params)
    append_perf("tmdb", f"external_ids_{media_type}", status, latency, size, rl)
    if status != 200:
        return {}
    return json.loads(payload.decode("utf-8", errors="ignore"))


# providers/tmdb.py  (instrumented helpers)
import os
import httpx
from providers.http_client import api_get, ApiError

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_TOKEN = os.getenv("TMDB_BEARER")

def _tmdb_headers():
    return {"Authorization": f"Bearer {TMDB_TOKEN}"} if TMDB_TOKEN else {}

async def i_tmdb_trending(media_type="all", window="day"):
    url = f"{TMDB_BASE}/trending/{media_type}/{window}"
    headers = _tmdb_headers()
    async with httpx.AsyncClient(timeout=20) as client:
        data, perf, _ = await api_get(
            client, url,
            params=None, headers=headers,
            provider="tmdb", endpoint=f"trending_{media_type}_{window}"
        )
    return data, perf

async def i_tmdb_external_ids(item_id: int, media_type: str):
    url = f"{TMDB_BASE}/{media_type}/{item_id}/external_ids"
    headers = _tmdb_headers()
    async with httpx.AsyncClient(timeout=20) as client:
        data, perf, _ = await api_get(
            client, url,
            params=None, headers=headers,
            provider="tmdb", endpoint="external_ids_movie" if media_type=="movie" else "external_ids_tv"
        )
    return data, perf

async def i_tmdb_watch_providers(item_id: int, media_type: str):
    url = f"{TMDB_BASE}/{media_type}/{item_id}/watch/providers"
    headers = _tmdb_headers()
    async with httpx.AsyncClient(timeout=20) as client:
        data, perf, _ = await api_get(
            client, url,
            params=None, headers=headers,
            provider="tmdb", endpoint=f"watch_providers_{media_type}"
        )
    return data, perf
