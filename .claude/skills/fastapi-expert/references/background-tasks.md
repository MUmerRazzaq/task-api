# Background Tasks in FastAPI

## Built-in BackgroundTasks

### Basic Usage

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

def write_log(message: str):
    with open("log.txt", "a") as f:
        f.write(f"{message}\n")

def send_email(email: str, message: str):
    # Simulate email sending
    print(f"Sending email to {email}: {message}")

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, email, "Welcome!")
    background_tasks.add_task(write_log, f"Email sent to {email}")
    return {"message": "Notification scheduled"}
```

### Multiple Tasks

```python
@app.post("/process")
async def process_data(data: DataInput, background_tasks: BackgroundTasks):
    # Tasks run in order they're added
    background_tasks.add_task(validate_data, data)
    background_tasks.add_task(save_to_database, data)
    background_tasks.add_task(notify_subscribers, data)
    background_tasks.add_task(update_cache, data)
    return {"status": "processing"}
```

### With Dependencies

```python
from typing import Annotated
from fastapi import Depends

def get_email_service():
    return EmailService()

@app.post("/users")
async def create_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    email_service: Annotated[EmailService, Depends(get_email_service)]
):
    new_user = db.create_user(user)

    # Use injected service in background task
    background_tasks.add_task(
        email_service.send_welcome_email,
        new_user.email
    )

    return new_user
```

---

## Async Background Tasks

```python
import asyncio

async def async_task(data: str):
    await asyncio.sleep(2)  # Simulate async work
    print(f"Processed: {data}")

@app.post("/async-process")
async def async_process(data: str, background_tasks: BackgroundTasks):
    # BackgroundTasks handles both sync and async functions
    background_tasks.add_task(async_task, data)
    return {"status": "scheduled"}
```

---

## Background Tasks in Dependencies

```python
async def log_request(
    request: Request,
    background_tasks: BackgroundTasks
):
    def log_to_file():
        with open("access.log", "a") as f:
            f.write(f"{request.method} {request.url}\n")

    background_tasks.add_task(log_to_file)

@app.get("/items", dependencies=[Depends(log_request)])
async def list_items():
    return {"items": [...]}
```

---

## When to Use BackgroundTasks

**Good for:**
- Sending emails/notifications
- Logging to external services
- Light data processing
- Cache updates
- Webhook calls

**Not good for:**
- Long-running tasks (>30 seconds)
- CPU-intensive operations
- Tasks that need retry logic
- Tasks that need to survive server restart

---

## For Heavy Tasks: Celery

### Setup

```python
# celery_app.py
from celery import Celery

celery = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

@celery.task
def process_video(video_id: str):
    # Long-running task
    pass

@celery.task
def generate_report(user_id: int, report_type: str):
    # CPU-intensive task
    pass
```

### Integration with FastAPI

```python
from celery_app import process_video, generate_report

@app.post("/videos/{video_id}/process")
async def start_video_processing(video_id: str):
    task = process_video.delay(video_id)
    return {"task_id": task.id, "status": "processing"}

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = celery.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }
```

---

## For Moderate Tasks: ARQ (Async Redis Queue)

```python
# tasks.py
from arq import create_pool
from arq.connections import RedisSettings

async def send_email_task(ctx, email: str, subject: str, body: str):
    # Async task
    await email_service.send(email, subject, body)

class WorkerSettings:
    functions = [send_email_task]
    redis_settings = RedisSettings(host="localhost", port=6379)

# main.py
from arq import create_pool

@app.on_event("startup")
async def startup():
    app.state.arq_pool = await create_pool(RedisSettings())

@app.post("/send-email")
async def send_email(email: EmailRequest):
    await app.state.arq_pool.enqueue_job(
        "send_email_task",
        email.recipient,
        email.subject,
        email.body
    )
    return {"status": "queued"}
```

---

## Error Handling in Background Tasks

```python
import logging

logger = logging.getLogger(__name__)

def safe_background_task(task_func):
    """Wrapper to catch exceptions in background tasks."""
    def wrapper(*args, **kwargs):
        try:
            return task_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Background task failed: {e}", exc_info=True)
            # Optionally: send to error tracking service
    return wrapper

@safe_background_task
def send_email(email: str, message: str):
    # If this fails, it's logged but doesn't crash the request
    email_service.send(email, message)

@app.post("/notify")
async def notify(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, email, "Hello!")
    return {"status": "scheduled"}
```

---

## Task with Cleanup

```python
from contextlib import contextmanager

@contextmanager
def temporary_file():
    import tempfile
    f = tempfile.NamedTemporaryFile(delete=False)
    try:
        yield f
    finally:
        import os
        os.unlink(f.name)

def process_with_cleanup(data: bytes):
    with temporary_file() as f:
        f.write(data)
        f.flush()
        # Process file...
        result = process_file(f.name)
    # File is automatically deleted
    return result

@app.post("/process-file")
async def process_file_endpoint(
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    content = await file.read()
    background_tasks.add_task(process_with_cleanup, content)
    return {"status": "processing"}
```

---

## Comparison

| Feature | BackgroundTasks | Celery | ARQ |
|---------|-----------------|--------|-----|
| Setup | Built-in | Complex | Moderate |
| Persistence | No | Yes | Yes |
| Retries | No | Yes | Yes |
| Monitoring | No | Yes (Flower) | Basic |
| Best for | Light tasks | Heavy/complex | Async tasks |
| Dependencies | None | Redis/RabbitMQ | Redis |
