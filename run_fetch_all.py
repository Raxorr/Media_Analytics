# run_fetch_all.py
import asyncio
from providers.tmdb import fetch_tmdb_trending

async def main():
    df = await fetch_tmdb_trending(media_type="all", window="day")
    print("Fetched rows:", len(df))

if __name__ == "__main__":
    asyncio.run(main())
