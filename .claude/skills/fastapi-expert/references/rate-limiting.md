# Rate Limiting in FastAPI

## Libraries

| Library | Best For | Backend |
|---------|----------|---------|
| `slowapi` | Simple setups, decorator-based | In-memory, Redis, Memcached |
| `fastapi-limiter` | Redis-native, async-first | Redis only |
| Custom middleware | Full control, specific needs | Any |

---

## SlowAPI Setup

### Installation

```bash
pip install slowapi
```

### Basic Configuration

```python
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/items")
@limiter.limit("100/minute")
async def list_items(request: Request):
    return {"items": [...]}
```

### Rate Limit Formats

```python
"5/second"      # 5 requests per second
"100/minute"    # 100 requests per minute
"1000/hour"     # 1000 requests per hour
"10000/day"     # 10000 requests per day
"2/5seconds"    # 2 requests per 5 seconds
```

### Multiple Limits

```python
@app.get("/data")
@limiter.limit("5/second")
@limiter.limit("100/minute")
@limiter.limit("1000/hour")
async def get_data(request: Request):
    return {"data": "..."}
```

---

## Redis-Based Rate Limiting

### SlowAPI with Redis

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)
```

### fastapi-limiter Setup

```python
import redis.asyncio as redis
from fastapi import FastAPI, Depends
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

app = FastAPI()

@app.on_event("startup")
async def startup():
    redis_connection = redis.from_url(
        "redis://localhost:6379",
        encoding="utf-8",
        decode_responses=True
    )
    await FastAPILimiter.init(redis_connection)

@app.get("/items")
async def list_items(_: None = Depends(RateLimiter(times=100, seconds=60))):
    return {"items": [...]}
```

---

## Rate Limiting Algorithms

### Fixed Window

Counts requests in fixed time intervals (e.g., every minute resets).

```
| 00:00 - 00:59 | 01:00 - 01:59 |
| 95 requests   | reset to 0    |
```

**Pros**: Simple, memory efficient
**Cons**: Burst at window boundaries

### Sliding Window

Counts requests over a rolling time period.

```
Current time: 01:30
Window: 00:30 - 01:30 (last 60 seconds)
```

**Pros**: Smoother rate limiting, no boundary bursts
**Cons**: More memory, slightly more complex

### Token Bucket

Tokens added at fixed rate, consumed per request.

```python
# Token bucket concept
bucket_size = 10      # Max tokens
refill_rate = 1       # Tokens per second
tokens = 10           # Current tokens

# On request:
if tokens > 0:
    tokens -= 1
    allow_request()
else:
    deny_request()
```

**Pros**: Allows bursts up to bucket size, smooth long-term rate
**Cons**: More complex implementation

---

## Key Functions

### By IP Address (Default)

```python
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

### By User ID

```python
def get_user_id(request: Request) -> str:
    # From JWT token or session
    user = request.state.user
    return str(user.id) if user else get_remote_address(request)

limiter = Limiter(key_func=get_user_id)
```

### By API Key

```python
def get_api_key(request: Request) -> str:
    api_key = request.headers.get("X-API-Key")
    return api_key or get_remote_address(request)

limiter = Limiter(key_func=get_api_key)
```

### Composite Key

```python
def get_composite_key(request: Request) -> str:
    ip = get_remote_address(request)
    endpoint = request.url.path
    return f"{ip}:{endpoint}"

limiter = Limiter(key_func=get_composite_key)
```

---

## Endpoint-Specific Limits

### Strict for Auth Endpoints

```python
@app.post("/auth/login")
@limiter.limit("5/minute")  # Prevent brute force
async def login(request: Request, credentials: LoginRequest):
    return authenticate(credentials)

@app.post("/auth/register")
@limiter.limit("3/hour")  # Prevent spam accounts
async def register(request: Request, user: UserCreate):
    return create_user(user)

@app.post("/auth/password-reset")
@limiter.limit("3/hour")  # Prevent enumeration
async def password_reset(request: Request, email: str):
    return send_reset_email(email)
```

### Relaxed for Read Operations

```python
@app.get("/items")
@limiter.limit("1000/minute")
async def list_items(request: Request):
    return {"items": [...]}

@app.get("/items/{id}")
@limiter.limit("1000/minute")
async def get_item(request: Request, id: int):
    return {"item": {...}}
```

### Moderate for Write Operations

```python
@app.post("/items")
@limiter.limit("100/minute")
async def create_item(request: Request, item: ItemCreate):
    return {"item": {...}}

@app.put("/items/{id}")
@limiter.limit("100/minute")
async def update_item(request: Request, id: int, item: ItemUpdate):
    return {"item": {...}}
```

---

## Rate Limit Headers

### Standard Headers

```
X-RateLimit-Limit: 100        # Max requests in window
X-RateLimit-Remaining: 95     # Requests left
X-RateLimit-Reset: 1609459200 # Window reset timestamp
Retry-After: 60               # Seconds until retry (on 429)
```

### Custom Middleware

```python
from fastapi import Request
from slowapi import Limiter

@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    response = await call_next(request)

    # SlowAPI adds these automatically, but for custom:
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = "95"
    response.headers["X-RateLimit-Reset"] = "60"

    return response
```

### Custom 429 Response

```python
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc.detail),
            "retry_after": 60
        },
        headers={
            "Retry-After": "60",
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "0"
        }
    )

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
```

---

## Dynamic Rate Limits

### By User Tier

```python
def get_rate_limit_by_tier(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if not user:
        return "10/minute"  # Anonymous

    tier_limits = {
        "free": "100/minute",
        "pro": "1000/minute",
        "enterprise": "10000/minute",
    }
    return tier_limits.get(user.tier, "100/minute")

@app.get("/api/data")
@limiter.limit(get_rate_limit_by_tier)
async def get_data(request: Request):
    return {"data": "..."}
```

### Admin Bypass

```python
def get_rate_limit_with_bypass(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user and user.is_admin:
        return "1000000/minute"  # Effectively unlimited
    return "100/minute"

@app.get("/admin/stats")
@limiter.limit(get_rate_limit_with_bypass)
async def admin_stats(request: Request):
    return {"stats": "..."}
```

---

## Distributed Rate Limiting

### Redis Configuration

```python
import redis

# Connection pool for efficiency
redis_pool = redis.ConnectionPool(
    host="redis-cluster.example.com",
    port=6379,
    password="your-password",
    max_connections=50
)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://:password@redis-cluster.example.com:6379"
)
```

### Cluster Support

```python
from redis.cluster import RedisCluster

# For Redis Cluster
startup_nodes = [
    {"host": "node1.example.com", "port": 6379},
    {"host": "node2.example.com", "port": 6379},
]

redis_cluster = RedisCluster(
    startup_nodes=startup_nodes,
    decode_responses=True
)
```

---

## Monitoring & Alerting

### Logging Rate Limit Events

```python
import logging
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

async def rate_limit_handler_with_logging(request: Request, exc: RateLimitExceeded):
    logger.warning(
        "Rate limit exceeded",
        extra={
            "client_ip": get_remote_address(request),
            "path": request.url.path,
            "limit": str(exc.detail),
        }
    )
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded"}
    )
```

### Prometheus Metrics

```python
from prometheus_client import Counter

rate_limit_exceeded = Counter(
    "rate_limit_exceeded_total",
    "Number of rate limit exceeded responses",
    ["endpoint", "client_type"]
)

async def rate_limit_handler_with_metrics(request: Request, exc: RateLimitExceeded):
    rate_limit_exceeded.labels(
        endpoint=request.url.path,
        client_type="anonymous" if not hasattr(request.state, "user") else "authenticated"
    ).inc()
    # ... rest of handler
```

---

## Complete Production Example

```python
from fastapi import FastAPI, Request, Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.dependencies import get_current_user_optional

def get_identifier(request: Request) -> str:
    """Get rate limit key: user ID if authenticated, IP otherwise."""
    user = getattr(request.state, "user", None)
    if user:
        return f"user:{user.id}"
    return f"ip:{get_remote_address(request)}"

limiter = Limiter(
    key_func=get_identifier,
    storage_uri=settings.REDIS_URL,
    strategy="moving-window"  # sliding window
)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Endpoints with appropriate limits
@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request):
    pass

@app.get("/api/items")
@limiter.limit("100/minute")
async def list_items(request: Request):
    pass

@app.post("/api/items")
@limiter.limit("30/minute")
async def create_item(request: Request):
    pass
```

---

## Best Practices

1. **Start conservative**, increase limits based on monitoring
2. **Use Redis** for anything beyond single-instance
3. **Different limits** for auth (strict) vs read (relaxed) endpoints
4. **Include headers** so clients can self-throttle
5. **Log exceeded events** for monitoring
6. **Consider user tiers** for fairness
7. **Avoid IP-only limits** in NAT environments (use API keys)
8. **Test under load** to verify limits work correctly
