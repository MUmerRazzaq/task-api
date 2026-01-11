# CORS Configuration in FastAPI

## Basic Setup

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Configuration Options

| Parameter | Type | Description |
|-----------|------|-------------|
| `allow_origins` | list[str] | Origins allowed to make requests |
| `allow_origin_regex` | str | Regex pattern for allowed origins |
| `allow_credentials` | bool | Allow cookies/auth headers (default: False) |
| `allow_methods` | list[str] | HTTP methods allowed (default: ["GET"]) |
| `allow_headers` | list[str] | Headers allowed in requests |
| `expose_headers` | list[str] | Headers accessible to browser |
| `max_age` | int | Preflight cache time in seconds (default: 600) |

---

## Environment-Based Configuration

### Development

```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True

settings = Settings()
```

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Staging

```python
# staging settings
CORS_ORIGINS = [
    "https://staging.example.com",
    "https://preview-*.example.com",  # Use regex for this
]
```

### Production

```python
# production settings - be restrictive!
CORS_ORIGINS = [
    "https://example.com",
    "https://www.example.com",
    "https://app.example.com",
]
```

---

## Origin Patterns

### Exact Match

```python
allow_origins=["https://example.com", "https://app.example.com"]
```

### Wildcard (Development Only!)

```python
# NEVER use in production!
allow_origins=["*"]
```

### Regex Pattern

```python
# Allow all subdomains
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.example\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Dynamic Origins

```python
from fastapi import Request

ALLOWED_ORIGINS = {
    "https://example.com",
    "https://app.example.com",
}

# Custom middleware for complex logic
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")

    response = await call_next(request)

    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response
```

---

## Credentials Handling

### With Cookies

```python
# When using cookies for auth
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],  # Must be specific, not "*"
    allow_credentials=True,                  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Important**: When `allow_credentials=True`, you CANNOT use `allow_origins=["*"]`

### With Authorization Header

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## Preflight Requests

Browsers send OPTIONS preflight requests for:
- Methods other than GET, HEAD, POST
- Custom headers
- Content-Type other than form-data, text/plain, application/x-www-form-urlencoded

### Preflight Flow

```
Browser                          Server
   |                                |
   |--- OPTIONS /api/users -------->|  (Preflight)
   |   Origin: https://app.com      |
   |   Access-Control-Request-Method: POST
   |   Access-Control-Request-Headers: Content-Type
   |                                |
   |<-- 200 OK --------------------|
   |   Access-Control-Allow-Origin: https://app.com
   |   Access-Control-Allow-Methods: POST
   |   Access-Control-Allow-Headers: Content-Type
   |   Access-Control-Max-Age: 600
   |                                |
   |--- POST /api/users ----------->|  (Actual request)
   |   Origin: https://app.com      |
   |   Content-Type: application/json
   |                                |
   |<-- 201 Created ----------------|
```

### Cache Preflight

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)
```

---

## CORS Error Debugging

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "No 'Access-Control-Allow-Origin'" | Origin not in allow list | Add origin to `allow_origins` |
| "Credentials not supported" | Using `*` with credentials | Use specific origins |
| "Method not allowed" | Method not in allow list | Add to `allow_methods` |
| "Header not allowed" | Header not in allow list | Add to `allow_headers` |

### Debug Middleware

```python
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def debug_cors(request: Request, call_next):
    origin = request.headers.get("origin")
    method = request.method

    logger.debug(f"Request: {method} {request.url.path}")
    logger.debug(f"Origin: {origin}")

    if method == "OPTIONS":
        logger.debug(f"Preflight for: {request.headers.get('access-control-request-method')}")

    response = await call_next(request)

    logger.debug(f"CORS headers in response:")
    for header in response.headers:
        if header.lower().startswith("access-control"):
            logger.debug(f"  {header}: {response.headers[header]}")

    return response
```

### Check Configuration

```python
@app.get("/debug/cors")
async def debug_cors():
    """Endpoint to check CORS configuration."""
    return {
        "origins": settings.CORS_ORIGINS,
        "credentials": True,
        "methods": ["*"],
        "headers": ["*"],
    }
```

---

## Security Best Practices

### DO

```python
# Specific origins
allow_origins=["https://example.com", "https://app.example.com"]

# Specific methods when possible
allow_methods=["GET", "POST", "PUT", "DELETE"]

# Only headers you need
allow_headers=["Authorization", "Content-Type", "X-Request-ID"]

# Expose only necessary headers
expose_headers=["X-Request-ID", "X-RateLimit-Remaining"]
```

### DON'T

```python
# Never in production!
allow_origins=["*"]

# Don't expose sensitive headers
expose_headers=["Set-Cookie", "X-Internal-Token"]
```

### Environment Check

```python
from app.config import settings

def get_cors_origins() -> list[str]:
    if settings.ENVIRONMENT == "development":
        return ["*"]  # OK for local dev
    return settings.CORS_ORIGINS  # Strict for staging/prod

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=settings.ENVIRONMENT != "development",
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Complete Production Example

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-CSRF-Token",
    ],
    expose_headers=[
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
    max_age=3600,
)
```

```ini
# .env.production
CORS_ORIGINS=["https://example.com","https://www.example.com"]
CORS_ORIGIN_REGEX=
```

```ini
# .env.development
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
CORS_ORIGIN_REGEX=
```
