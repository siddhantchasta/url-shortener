# URL Shortener

High-performance URL shortener built with FastAPI, PostgreSQL, and Redis — supports custom
aliases, configurable link expiration, rate limiting, and health/debug monitoring endpoints.

## Architecture

Postgres is the source of truth; Redis is a cache-aside layer in front of it for low-latency
redirects. Writes go to Postgres and immediately populate Redis. Reads check Redis first and
only fall back to Postgres on a cache miss, repopulating the cache afterward.

## Quick Start

```bash
cp .env.example .env
docker-compose up --build
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## API Reference

| Method | Path | Description |
|---|---|---|
| POST | /api/v1/urls | Create a short URL |
| GET | /api/v1/urls/{short_code} | Get metadata for a short URL |
| PUT | /api/v1/urls/{short_code} | Update target URL / expiry |
| DELETE | /api/v1/urls/{short_code} | Delete a short URL |
| GET | /{short_code} | Redirect to the original URL |
| GET | /health | Postgres + Redis connectivity check |
| GET | /debug/stats | URL/click/cache stats (debug mode only) |
| GET | /debug/cache/{short_code} | Cache status for a code (debug mode only) |

## Tests

```bash
pip install -r requirements.txt
pytest
```
