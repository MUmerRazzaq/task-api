# FastAPI Project Structure

## Minimal (Hello World)

```
project/
├── main.py
└── requirements.txt
```

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

## Small Project

```
project/
├── main.py
├── config.py
├── schemas.py
├── routers/
│   └── items.py
└── requirements.txt
```

## Production Project

```
app/
├── __init__.py
├── main.py                 # App factory, lifespan, middleware
├── config.py               # Settings management
├── dependencies.py         # Shared DI (db sessions, current_user)
├── exceptions.py           # Custom exceptions + handlers
├── routers/
│   ├── __init__.py
│   ├── users.py
│   ├── items.py
│   └── auth.py
├── schemas/                # Pydantic models
│   ├── __init__.py
│   ├── base.py            # Shared base schemas
│   ├── user.py
│   └── item.py
├── models/                 # Database ORM models
│   ├── __init__.py
│   ├── base.py
│   ├── user.py
│   └── item.py
├── services/               # Business logic layer
│   ├── __init__.py
│   ├── user_service.py
│   └── item_service.py
├── repositories/           # Data access layer (optional)
│   ├── __init__.py
│   └── user_repository.py
├── utils/
│   ├── __init__.py
│   └── security.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_users.py
    └── test_items.py
```

---

## Key Files

### main.py

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import users, items, auth
from app.exceptions import register_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize resources
    print("Starting up...")
    yield
    # Shutdown: cleanup resources
    print("Shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="Production API",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Routers
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(items.router)

    return app

app = create_app()
```

### config.py

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "My API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/db"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### dependencies.py

```python
from typing import Annotated, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.models.base import SessionLocal
from app.models.user import User
from app.utils.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Type aliases for cleaner endpoint signatures
DB = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
```

---

## Router Organization

### By Resource (Recommended)

```
routers/
├── users.py      # /users endpoints
├── items.py      # /items endpoints
├── orders.py     # /orders endpoints
└── auth.py       # /auth endpoints
```

### By Version

```
routers/
├── v1/
│   ├── __init__.py
│   ├── users.py
│   └── items.py
└── v2/
    ├── __init__.py
    └── users.py
```

```python
# main.py
from app.routers.v1 import users as users_v1
from app.routers.v2 import users as users_v2

app.include_router(users_v1.router, prefix="/api/v1")
app.include_router(users_v2.router, prefix="/api/v2")
```

---

## Schema Organization

### Separate Input/Output Models

```python
# schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime

# Base with shared fields
class UserBase(BaseModel):
    email: EmailStr
    username: str

# Create - what client sends
class UserCreate(UserBase):
    password: str

# Update - partial updates allowed
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None

# Response - what API returns
class UserOut(UserBase):
    id: int
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}

# Internal - includes sensitive data
class UserInDB(UserOut):
    hashed_password: str
```

---

## Service Layer Pattern

```python
# services/user_service.py
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import hash_password

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def create(self, user_data: UserCreate) -> User:
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hash_password(user_data.password)
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, user_data: UserUpdate) -> User:
        update_data = user_data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = hash_password(update_data.pop("password"))
        for field, value in update_data.items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user
```

```python
# routers/users.py
@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: DB):
    service = UserService(db)
    user = service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```
