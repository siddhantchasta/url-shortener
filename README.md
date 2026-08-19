# URL Shortener

A URL shortener built with FastAPI, PostgreSQL, and Redis — custom aliases,
configurable link expiration, Redis-backed rate limiting, API-key-gated write
endpoints, and health/debug monitoring.

## Architecture

Postgres is the source of truth; Redis is a cache-aside layer in front of it
for low-latency redirects. Writes go to Postgres and immediately populate
Redis. Reads check Redis first and only fall back to Postgres on a cache
miss, repopulating the cache afterward. In production this points at a
managed Redis Cloud instance rather than a local container.

The service is stateless — all state lives in Postgres/Redis — so it runs as
three replicas behind an nginx load balancer (see `docker-compose.yml`).

## Quick Start

```bash
cp .env.example .env
# set API_KEY to a real value before running
docker-compose up --build
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Authentication

Write endpoints (`POST`/`PUT`/`DELETE` on `/api/v1/urls`, and all `/debug/*`
routes) require an `X-API-Key` header matching `API_KEY` in `.env`. Reads and
redirects stay public.

## API Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /api/v1/urls | required | Create a short URL |
| GET | /api/v1/urls/{short_code} | none | Get metadata for a short URL |
| PUT | /api/v1/urls/{short_code} | required | Update target URL / expiry |
| DELETE | /api/v1/urls/{short_code} | required | Delete a short URL |
| GET | /{short_code} | none | Redirect to the original URL |
| GET | /health | none | Postgres + Redis connectivity check |
| GET | /debug/stats | required | URL/click/cache stats (debug mode only) |
| GET | /debug/cache/{short_code} | required | Cache status for a code (debug mode only) |

## Security

- Redirect targets are validated at creation/update time to reject
  private/internal/loopback IP ranges, preventing the service from being used
  as an open redirector into internal infrastructure.
- Write and debug endpoints require an API key.
- `DEBUG_MODE` defaults to `false`; debug routes 404 unless explicitly enabled.
- Fixed-window rate limiting per client IP (known trade-off: allows a burst at
  the window boundary — a token-bucket limiter would avoid that).

## Performance

Load tested with k6 (`loadtest/redirect.js`), 50 concurrent VUs, 30s, against
the redirect hot path (cache hit):

| Metric | Value |
|---|---|
| p50 latency | 8.19 ms |
| p95 latency | 186.52 ms |
| Requests/sec | 364.5 req/s (10,976 total requests, 0% failure) |

## Tests

```bash
pip install -r requirements.txt
pytest
```
