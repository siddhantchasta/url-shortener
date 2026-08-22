# URL Shortener & High-Throughput Redirection Engine

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg?style=flat&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com)
[![Nginx](https://img.shields.io/badge/Nginx-Load%20Balanced-009639.svg?style=flat&logo=nginx&logoColor=white)](https://nginx.org)
[![k6](https://img.shields.io/badge/Load%20Tested-k6-7D64FF.svg?style=flat&logo=k6&logoColor=white)](https://k6.io)

A high-performance, containerized URL Shortener and redirection service engineered with **FastAPI**, **PostgreSQL**, and **Redis**. Designed for high concurrency and ultra-low latency redirect paths using a dual **Cache-Aside + Write-Back (Write-Behind) Caching** architecture.

**Live Deployment:** [Render Hosted Service](https://url-shortener-zaqb.onrender.com)

---

## Architecture Overview

```
                         ┌─────────────────────────┐
Client Traffic ─────────►│  Nginx Load Balancer    │ (Port 8000)
(50+ Concurrent VUs)     └────────────┬────────────┘
                                      │
                   ┌──────────────────┼──────────────────┐
                   ▼                  ▼                  ▼
             ┌───────────┐      ┌───────────┐      ┌───────────┐
             │   api1    │      │   api2    │      │   api3    │ (FastAPI Workers)
             └─────┬─────┘      └─────┬─────┘      └─────┬─────┘
                   │                  │                  │
                   ├──────────────────┴──────────────────┤
                   │                                     │
   [Hot-Path Redirect]                                   │
   1. Cache Lookup (O(1))                                │ [Async Lifespan Sync Worker]
   2. In-Memory Atomic INCR                              │ Periodic 10s Batched Flush
                   ▼                                     ▼
          ┌─────────────────┐                  ┌──────────────────┐
          │   Redis (RAM)   │                  │ PostgreSQL (Disk)│
          │  url:{code}     │                  │  Primary Source  │
          │  clicks:{code}  │                  │     of Truth     │
          └─────────────────┘                  └──────────────────┘
```

### Key Architectural Patterns
1. **Cache-Aside Read Path (`GET /{short_code}`)**: Redirect lookups hit Redis in memory (<1ms). Only cache misses fall back to PostgreSQL, dynamically repopulating Redis.
2. **Write-Back Analytics Buffering**: Click increments use atomic in-memory Redis `INCR` operations. An asynchronous background sync worker flushes counts in single batched transactions to PostgreSQL every 10 seconds, eliminating relational database row-locking bottlenecks.
3. **Stateless Horizontal Scaling**: 3 containerized FastAPI worker replicas load-balanced behind an Nginx reverse proxy using round-robin distribution.
4. **Real-time Data Consistency**: Metadata endpoints (`GET /api/v1/urls/{code}`) seamlessly aggregate persistent PostgreSQL clicks with pending in-memory Redis counts for instant 100% accuracy.

---

## Performance & Optimization Case Study

We benchmarked the service using **Grafana k6** (`loadtest/redirect.js`) under a sustained load of **50 concurrent Virtual Users (VUs) for 30 seconds** on the redirect hot-path.

### The Optimization: Resolving Database Row-Lock Contention
* **Before (DB BackgroundTask per request):** Every redirect spawned a background task that executed an SQL `UPDATE` against PostgreSQL. Under 50 concurrent VUs targeting the same link, thousands of simultaneous row-level locks on the exact same row saturated the database pool, spiking tail latency (`p95 = 136.98ms`).
* **After (Write-Back Caching with Redis `INCR`):** We replaced per-request database updates with atomic Redis `INCR` operations and a periodic batch sync worker.

### Benchmark Results (Before vs. After)

| Metric | Before Optimization (DB Writes on Hot Path) | After Optimization (Redis Write-Back Caching) | Impact / Gain |
|---|---|---|---|
| **p95 Tail Latency** | `136.98 ms` | **`26.71 ms`** | ⚡ **80.5% Faster (5x reduction)** |
| **p90 Latency** | `81.41 ms` | **`19.53 ms`** | ⚡ **76.0% Faster (4x reduction)** |
| **Average Latency** | `31.51 ms` | **`10.93 ms`** | ⚡ **65.3% Faster (3x reduction)** |
| **Max Latency Spike** | `821.70 ms` | **`183.35 ms`** | ⚡ **77.7% Lower Spikes** |
| **Minimum Latency** | `1.09 ms` | **`935 µs (0.93 ms)`** | ⚡ **Sub-millisecond floor** |
| **Throughput** | `375.98 req/s` | **`446.66 req/s`** | 🚀 **+18.8% Higher Throughput** |
| **Total Requests (30s)** | `11,316 reqs` | **`13,454 reqs`** | 🚀 **+2,138 more requests handled** |
| **HTTP Error Rate** | `0.00%` (0 errors) | **`0.00%` (0 errors)** | 🟢 **100% Success Rate (13,454/13,454)** |

---

### Load Test Terminal Proof

#### 1. Optimized Run Output (Write-Back Caching) — `p95 = 26.71ms`, `446.66 req/s`
```text
         /\      Grafana   /‾‾/  
    /\  /  \     |\  __   /  /   
   /  \/    \    | |/ /  /   ‾‾\ 
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/ 

     execution: local
        script: loadtest/redirect.js
     scenarios: (100.00%) 1 scenario, 50 max VUs, 1m0s max duration (incl. graceful stop):
              * redirect_hot_path: 50 looping VUs for 30s (gracefulStop: 30s)

  █ THRESHOLDS 
    http_req_duration
    ✓ 'p(95)<200' p(95)=26.71ms

  █ TOTAL RESULTS 
    checks_total.......: 13454   446.661677/s
    checks_succeeded...: 100.00% 13454 out of 13454
    checks_failed......: 0.00%   0 out of 13454

    ✓ status is 307

    HTTP
    http_req_duration..............: avg=10.93ms  min=935µs    med=7.43ms   max=183.35ms p(90)=19.53ms p(95)=26.71ms 
      { expected_response:true }...: avg=10.93ms  min=935µs    med=7.43ms   max=183.35ms p(90)=19.53ms p(95)=26.71ms 
    http_req_failed................: 0.00%  0 out of 13454
    http_reqs......................: 13454  446.661677/s

    EXECUTION
    iteration_duration.............: avg=111.59ms min=101.15ms med=108.11ms max=283.51ms p(90)=120.27ms p(95)=128.05ms
    iterations.....................: 13454  446.661677/s
    vus............................: 50     min=50         max=50
    vus_max........................: 50     min=50         max=50

running (0m30.1s), 00/50 VUs, 13454 complete and 0 interrupted iterations
redirect_hot_path ✓ [======================================] 50 VUs  30s
```

#### 2. Baseline Run Output (Before Optimization) — `p95 = 136.98ms`, `375.98 req/s`
```text
  █ THRESHOLDS 
    http_req_duration
    ✓ 'p(95)<200' p(95)=136.98ms

  █ TOTAL RESULTS 
    checks_total.......: 11316   375.976085/s
    checks_succeeded...: 100.00% 11316 out of 11316
    checks_failed......: 0.00%   0 out of 11316

    ✓ status is 307

    HTTP
    http_req_duration..............: avg=31.51ms  min=1.09ms   med=6.49ms  max=821.7ms  p(90)=81.41ms  p(95)=136.98ms
    http_reqs......................: 11316  375.976085/s
```

---

## Security & Defense-in-Depth

* **SSRF Protection (Server-Side Request Forgery)**: Destination URLs are validated against private, reserved, loopback (`127.0.0.1`, `localhost`), and internal RFC-1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) to prevent using the shortener as an open proxy into internal infrastructure.
* **API Key Gating**: Administrative write endpoints (`POST`/`PUT`/`DELETE`) and `/debug/*` inspection routes require a valid `X-API-Key` request header. Public redirects and metadata queries remain open.
* **Redis-Backed Rate Limiting**: Per-client IP rate limiting on link creation to protect the system against denial-of-service and database flooding.
* **Safe Debug Mode**: System diagnostic routes 404 by default unless explicitly enabled via environment configuration (`DEBUG_MODE=true`).

---

## API Reference

| Method | Path | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/v1/urls` | `X-API-Key` | Create short URL (custom alias & expiry optional) |
| `GET` | `/api/v1/urls/{short_code}` | Public | Retrieve URL metadata and real-time click statistics |
| `PUT` | `/api/v1/urls/{short_code}` | `X-API-Key` | Update target URL or extend expiration |
| `DELETE` | `/api/v1/urls/{short_code}` | `X-API-Key` | Delete short URL and invalidate Redis cache |
| `GET` | `/{short_code}` | Public | Fast `HTTP 307` redirect to destination |
| `GET` | `/health` | Public | Readiness probe (checks Postgres + Redis health) |
| `GET` | `/debug/stats` | `X-API-Key` | URL, click, and cache statistics (debug mode) |
| `GET` | `/debug/cache/{short_code}` | `X-API-Key` | Inspect Redis key status and TTL (debug mode) |

---

## Quick Start (Local Setup)

### 1. Configure Environment
```bash
cp .env.example .env
# Edit .env to set your desired API_KEY
```

### 2. Start the Stack (Nginx + 3 App Replicas + Postgres + Redis)
```bash
docker compose up --build -d
```
* **API Gateway / Base URL:** `http://localhost:8000`
* **Interactive Swagger Docs:** `http://localhost:8000/docs`

### 3. Verify Health
```bash
curl http://localhost:8000/health
# {"status":"ok","postgres":"connected","redis":"connected"}
```

---

## Re-Running the Load Test

1. **Install k6**:
   ```bash
   brew install k6
   ```

2. **Create a short URL**:
   ```bash
   curl -s -X POST http://localhost:8000/api/v1/urls \
     -H "Content-Type: application/json" \
     -H "X-API-Key: my-secret-key" \
     -d '{"url": "https://example.com"}'
   ```
   *(Note the returned `short_code`, e.g. `kzUFpD`)*

3. **Warm the cache (once)**:
   ```bash
   curl -i http://localhost:8000/<your_code>
   ```

4. **Run the k6 benchmark**:
   ```bash
   SHORT_CODE=<your_code> k6 run loadtest/redirect.js
   ```

---

## Automated Testing

Run the test suite with `pytest`:
```bash
pytest
```