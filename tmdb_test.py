from dotenv import load_dotenv
load_dotenv()

import os
import requests

TMDB_KEY = os.getenv("TMDB_API_KEY")
print("Using key:", TMDB_KEY[:6], "...")  # only first few chars for sanity check

url = "https://api.themoviedb.org/3/trending/all/day"

if TMDB_KEY.startswith("ey"):  # v4 token
    headers = {"Authorization": f"Bearer {TMDB_KEY}"}
    params = {}
else:                          # v3 key
    headers = {}
    params = {"api_key": TMDB_KEY}

r = requests.get(url, headers=headers, params=params)
print("Status:", r.status_code)
print("Body:", r.text[:300])
