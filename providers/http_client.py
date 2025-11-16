# providers/http_client.py
import time
import httpx

RATE_HEADERS = [
    "x-ratelimit-limit", "x-rate-limit-limit", "ratelimit-limit",
    "x-ratelimit-remaining", "x-rate-limit-remaining", "ratelimit-remaining",
    "x-ratelimit-reset", "x-rate-limit-reset", "ratelimit-reset",
    "retry-after",
]

class ApiError(Exception):
    def __init__(self, message: str, perf_row: dict):
        super().__init__(message)
        self.perf = perf_row

async def api_get(
    client: httpx.AsyncClient,
    url: str,
    *,
    params=None,
    headers=None,
    provider: str,
    endpoint: str,
    honor_retry_after: bool = True,
    parse_json_when="application/json",
):
    """
    Perform GET, capture latency/size/status and any rate-limit headers.
    Returns (data, perf_row, response) on success.
    Raises ApiError on 429 with perf info attached.
    """
    t0 = time.perf_counter()
    resp = await client.get(url, params=params, headers=headers)
    latency_ms = (time.perf_counter() - t0) * 1000.0
    body_bytes = len(resp.content or b"")

    # case-insensitive header capture for a wide range of rate-limit keys
    h = resp.headers
    def pick(name: str):
        return h.get(name) or h.get(name.title()) or h.get(name.upper())

    perf_row = {
        "ts": time.time(),
        "provider": provider,
        "endpoint": endpoint,
        "status": resp.status_code,
        "latency_ms": round(latency_ms, 1),
        "bytes": body_bytes,
        "ratelimit_limit": pick("x-ratelimit-limit") or pick("x-rate-limit-limit") or pick("ratelimit-limit"),
        "ratelimit_remaining": pick("x-ratelimit-remaining") or pick("x-rate-limit-remaining") or pick("ratelimit-remaining"),
        "ratelimit_reset": pick("x-ratelimit-reset") or pick("x-rate-limit-reset") or pick("ratelimit-reset"),
        "retry_after": pick("retry-after"),
        "url": url,
    }

    if resp.status_code == 429 and honor_retry_after:
        # include perf in the exception so callers can log it
        raise ApiError(f"429 from {provider}:{endpoint}", perf_row)

    data = None
    if (
        resp.status_code == 200
        and parse_json_when
        and resp.headers.get("content-type", "").startswith(parse_json_when)
    ):
        data = resp.json()

    return data, perf_row, resp
