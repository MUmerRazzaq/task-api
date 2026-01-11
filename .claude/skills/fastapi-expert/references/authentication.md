# Authentication in FastAPI

## OAuth2 with Password Flow

### Basic Setup

```python
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = "your-secret-key"  # Use env variable!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()
```

### Token Models

```python
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []
```

### Password Utilities

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)
```

### Token Creation

```python
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### User Authentication

```python
def authenticate_user(db, username: str, password: str):
    user = db.get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user
```

### Login Endpoint

```python
@app.post("/token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return Token(access_token=access_token, token_type="bearer")
```

### Get Current User Dependency

```python
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.get_user(username)
    if user is None:
        raise credentials_exception
    return user

# Type alias for clean endpoints
CurrentUser = Annotated[User, Depends(get_current_user)]
```

### Protected Endpoints

```python
@app.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: CurrentUser):
    return current_user

@app.get("/items")
async def read_items(current_user: CurrentUser):
    return {"owner": current_user.username, "items": [...]}
```

---

## JWT with Refresh Tokens

```python
REFRESH_TOKEN_EXPIRE_DAYS = 7

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/token", response_model=TokenPair)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return TokenPair(
        access_token=create_access_token({"sub": user.username}),
        refresh_token=create_refresh_token({"sub": user.username})
    )

@app.post("/token/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    return Token(
        access_token=create_access_token({"sub": username}),
        token_type="bearer"
    )
```

---

## API Key Authentication

```python
from fastapi.security import APIKeyHeader, APIKeyQuery

# Header-based API key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Query-based API key (less secure, for testing)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)

async def get_api_key(
    api_key_header: str = Depends(api_key_header),
    api_key_query: str = Depends(api_key_query),
) -> str:
    api_key = api_key_header or api_key_query
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    # Validate against database
    if not db.validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key

@app.get("/data")
async def get_data(api_key: str = Depends(get_api_key)):
    return {"data": "..."}
```

---

## Role-Based Access Control (RBAC)

```python
from enum import Enum
from functools import wraps

class Role(str, Enum):
    user = "user"
    admin = "admin"
    superadmin = "superadmin"

class User(BaseModel):
    id: int
    username: str
    role: Role

def require_role(allowed_roles: list[Role]):
    """Dependency factory for role checking."""
    async def role_checker(current_user: CurrentUser):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Usage
AdminUser = Annotated[User, Depends(require_role([Role.admin, Role.superadmin]))]

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, admin: AdminUser):
    return {"deleted": user_id}

@app.get("/admin/stats")
async def admin_stats(admin: AdminUser):
    return {"stats": "..."}
```

---

## OAuth2 Scopes

```python
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "users:read": "Read user information",
        "users:write": "Create and update users",
        "items:read": "Read items",
        "items:write": "Create and update items",
    }
)

async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)]
):
    authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        token_scopes = payload.get("scopes", [])
    except JWTError:
        raise credentials_exception

    # Check required scopes
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return db.get_user(username)

# Usage with Security dependency
from fastapi import Security

@app.get("/users", dependencies=[Security(get_current_user, scopes=["users:read"])])
async def list_users():
    return {"users": [...]}

@app.post("/users", dependencies=[Security(get_current_user, scopes=["users:write"])])
async def create_user(user: UserCreate):
    return {"user": user}
```

---

## Complete Auth Module

```python
# auth/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AUTH_")

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

auth_settings = AuthSettings()

# auth/dependencies.py
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    # ... token validation
    pass

async def get_current_active_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

# Type aliases
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]

# auth/router.py
from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    pass

@router.post("/register", response_model=UserOut, status_code=201)
async def register(user: UserCreate):
    pass

@router.post("/refresh", response_model=Token)
async def refresh(refresh_token: str):
    pass
```
