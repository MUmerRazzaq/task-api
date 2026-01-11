# File Uploads in FastAPI

## Basic File Upload

```python
from fastapi import FastAPI, File, UploadFile
from typing import Annotated

app = FastAPI()

@app.post("/upload")
async def upload_file(file: Annotated[UploadFile, File()]):
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size
    }
```

---

## File vs UploadFile

### bytes with File()

```python
# Reads entire file into memory - use for small files only
@app.post("/upload-bytes")
async def upload_bytes(file: Annotated[bytes, File()]):
    return {"size": len(file)}
```

### UploadFile (Recommended)

```python
# Spooled to disk if large, async methods
@app.post("/upload")
async def upload_file(file: UploadFile):
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}
```

**UploadFile attributes:**
- `filename`: Original filename
- `content_type`: MIME type
- `size`: File size (may be None)
- `file`: SpooledTemporaryFile

**UploadFile methods:**
- `read(size)`: Read bytes
- `seek(offset)`: Move to position
- `write(data)`: Write data
- `close()`: Close file

---

## Multiple Files

```python
@app.post("/upload-multiple")
async def upload_multiple(files: list[UploadFile]):
    return {
        "filenames": [f.filename for f in files],
        "count": len(files)
    }
```

---

## File with Form Data

```python
from fastapi import Form

@app.post("/upload-with-data")
async def upload_with_data(
    file: UploadFile,
    description: Annotated[str, Form()],
    tags: Annotated[list[str], Form()] = []
):
    return {
        "filename": file.filename,
        "description": description,
        "tags": tags
    }
```

---

## File Validation

### Size Limit

```python
from fastapi import HTTPException

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@app.post("/upload")
async def upload_file(file: UploadFile):
    # Check size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    # Reset file position for further processing
    await file.seek(0)

    return {"size": len(contents)}
```

### Content Type Validation

```python
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif"}

@app.post("/upload-image")
async def upload_image(file: UploadFile):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {ALLOWED_TYPES}"
        )
    return {"filename": file.filename}
```

### Extension Validation

```python
import os

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}

@app.post("/upload-image")
async def upload_image(file: UploadFile):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    return {"filename": file.filename}
```

---

## Saving Files

### To Local Filesystem

```python
import os
import uuid
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/upload")
async def upload_file(file: UploadFile):
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / unique_name

    # Save file
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    return {"filename": unique_name, "path": str(file_path)}
```

### Streaming Large Files

```python
import shutil

@app.post("/upload-large")
async def upload_large_file(file: UploadFile):
    file_path = UPLOAD_DIR / file.filename

    # Stream to disk without loading into memory
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": file.filename}
```

### To Cloud Storage (S3)

```python
import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client("s3")
BUCKET_NAME = "my-bucket"

@app.post("/upload-s3")
async def upload_to_s3(file: UploadFile):
    try:
        key = f"uploads/{uuid.uuid4()}/{file.filename}"
        s3_client.upload_fileobj(
            file.file,
            BUCKET_NAME,
            key,
            ExtraArgs={"ContentType": file.content_type}
        )
        return {
            "key": key,
            "url": f"https://{BUCKET_NAME}.s3.amazonaws.com/{key}"
        }
    except ClientError as e:
        raise HTTPException(status_code=500, detail="Upload failed")
```

---

## Serving Files

### Static Files

```python
from fastapi.staticfiles import StaticFiles

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Access via: /uploads/filename.jpg
```

### File Response

```python
from fastapi.responses import FileResponse

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )
```

### Streaming Response

```python
from fastapi.responses import StreamingResponse

@app.get("/stream/{filename}")
async def stream_file(filename: str):
    file_path = UPLOAD_DIR / filename

    def iterfile():
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return StreamingResponse(
        iterfile(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

---

## Image Processing

```python
from PIL import Image
import io

@app.post("/upload-image")
async def upload_image(file: UploadFile):
    contents = await file.read()

    # Open with Pillow
    image = Image.open(io.BytesIO(contents))

    # Create thumbnail
    thumbnail_size = (128, 128)
    image.thumbnail(thumbnail_size)

    # Save thumbnail
    thumb_path = UPLOAD_DIR / f"thumb_{file.filename}"
    image.save(thumb_path)

    return {
        "original_size": image.size,
        "thumbnail": str(thumb_path)
    }
```

---

## Background Processing

```python
from fastapi import BackgroundTasks

def process_file(file_path: str, file_id: str):
    # Heavy processing
    pass

@app.post("/upload-async")
async def upload_async(
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    # Save file
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    # Process in background
    background_tasks.add_task(process_file, str(file_path), file_id)

    return {"file_id": file_id, "status": "processing"}
```

---

## Complete Upload Endpoint

```python
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from typing import Annotated
import os
import uuid
from pathlib import Path

UPLOAD_DIR = Path("uploads")
MAX_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "application/pdf"}

async def validate_file(file: UploadFile) -> bytes:
    """Validate and read file."""
    # Check content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Type {file.content_type} not allowed")

    # Read and check size
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(413, "File too large")

    return contents

def save_file(contents: bytes, filename: str) -> str:
    """Save file to disk."""
    ext = os.path.splitext(filename)[1]
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / unique_name

    with open(file_path, "wb") as f:
        f.write(contents)

    return unique_name

@app.post("/files")
async def upload_file(
    file: Annotated[UploadFile, File(description="File to upload")],
    background_tasks: BackgroundTasks
):
    # Validate
    contents = await validate_file(file)

    # Save
    saved_name = save_file(contents, file.filename)

    # Background processing if needed
    background_tasks.add_task(index_file, saved_name)

    return {
        "id": saved_name,
        "original_name": file.filename,
        "size": len(contents),
        "content_type": file.content_type,
        "url": f"/uploads/{saved_name}"
    }
```
