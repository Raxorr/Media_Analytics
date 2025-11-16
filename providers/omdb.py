# providers/omdb.py

import os
import json
import aiohttp
from dotenv import load_dotenv

from etl_fetch import timed_get, append_perf

# Load .env locally (no effect on Streamlit Cloud)
load_dotenv()

# Try to import streamlit (present on Streamlit Cloud, not required locally)
try:
    import streamlit as st  # type: ignore
except ImportError:
    st = None


# ---------- API KEY RESOLUTION (env + secrets) ----------

def _get_omdb_key() -> str:
    """
    Look for OMDb API key in:
      1) Environment variables: OMDB_API_KEY or OMDB_KEY
      2) Streamlit secrets: OMDB_API_KEY or OMDB_KEY

    Raises RuntimeError if nothing is found.
    """
    # 1) Environment variables (works locally with .env)
    for name in ("OMDB_API_KEY", "OMDB_KEY"):
        val = os.getenv(name)
        if val:
            return val

    # 2) Streamlit secrets (works on Streamlit Cloud)
    if st is not None:
        try:
            secrets_obj = st.secrets
        except Exception:
            secrets_obj = None

        if secrets_obj is not None:
            for name in ("OMDB_API_KEY", "OMDB_KEY"):
                try:
                    val = secrets_obj.get(name)
                except Exception:
                    val = None
                if val:
                    return val

    raise RuntimeError(
        "OMDB API key not set. Please provide OMDB_API_KEY (or OMDB_KEY) "
        "via environment variable or Streamlit secrets."
    )


OMDB_KEY = _get_omdb_key()

# ---------------------------------------------------------------------
#  A) Original helper used by your ETL: fetch_omdb_rating(imdb_id)
# ---------------------------------------------------------------------

async def fetch_omdb_rating(imdb_id: str) -> dict:
    """
    Simple OMDb lookup used in the ETL. Returns a dict like:
      {
        'imdbRating': '7.6',
        'imdbVotes': '123,456'
      }
    or {} if lookup fails.
    """
    if not OMDB_KEY or not imdb_id:
        return {}

    url = "http://www.omdbapi.com/"
    params = {"i": imdb_id, "apikey": OMDB_KEY}

    async with aiohttp.ClientSession() as session:
        status, payload, latency, size, rl = await timed_get(
            session, url, params=params
        )
        append_perf("omdb", "rating_lookup", status, latency, size, rl)

    if status != 200:
        return {}

    data = json.loads(payload.decode("utf-8", errors="ignore"))
    if data.get("Response") != "True":
        return {}

    return {
        "imdbRating": data.get("imdbRating"),
        "imdbVotes": data.get("imdbVotes"),
    }


# ---------------------------------------------------------------------
#  B) Instrumented helper used by API_counter / perf logging:
#     i_omdb_rating(imdb_id)
# ---------------------------------------------------------------------

import httpx
from providers.http_client import api_get

OMDB_BASE = "http://www.omdbapi.com/"  # OMDb docs use http


async def i_omdb_rating(imdb_id: str):
    """
    Instrumented OMDb lookup used by the perf logger.
    Returns (data, perf) exactly like your existing version.
    """
    params = {"i": imdb_id, "apikey": OMDB_KEY}

    async with httpx.AsyncClient(timeout=20) as client:
        data, perf = await api_get(
            client,
            OMDB_BASE,
            params=params,
            headers=None,
            provider="omdb",
            endpoint="rating_lookup",
        )

    return data, perf
