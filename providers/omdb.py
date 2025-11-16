# providers/omdb.py
import os, json, aiohttp
from dotenv import load_dotenv
from etl_fetch import timed_get, append_perf
load_dotenv()
OMDB_KEY = os.getenv("OMDB_API_KEY")

async def fetch_omdb_rating(imdb_id: str):
    if not OMDB_KEY or not imdb_id:
        return {}
    url = "https://www.omdbapi.com/"
    params = {"i": imdb_id, "apikey": OMDB_KEY}
    async with aiohttp.ClientSession() as session:
        status, payload, latency, size, rl = await timed_get(session, url, params=params)
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


# providers/omdb.py  (instrumented helper)
import os
import httpx
from providers.http_client import api_get

OMDB_BASE = "https://www.omdbapi.com/"
OMDB_KEY = os.getenv("OMDB_API_KEY")

async def i_omdb_rating(imdb_id: str):
    params = {"i": imdb_id, "apikey": OMDB_KEY}
    async with httpx.AsyncClient(timeout=20) as client:
        data, perf, _ = await api_get(
            client, OMDB_BASE,
            params=params, headers=None,
            provider="omdb", endpoint="rating_lookup"
        )
    return data, perf
