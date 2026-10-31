from datetime import datetime, timedelta
from pathlib import Path
import secrets

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import FileShare

PROJECT_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = PROJECT_DIR / "uploads"
FRONTEND_DIR = PROJECT_DIR / "frontend"
MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_EXPIRY_HOURS = {1, 6, 24, 168}

UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="QuickDrop API",
    description="Temporary file sharing with expiring download links.",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


def remove_expired_files(db: Session) -> None:
    """Delete expired file records and their stored files."""
    now = datetime.utcnow()
    expired_items = (
        db.query(FileShare)
        .filter(FileShare.expires_at <= now)
        .all()
    )

    for item in expired_items:
        file_path = UPLOAD_DIR / item.stored_filename
        if file_path.exists():
            file_path.unlink()
        db.delete(item)

    if expired_items:
        db.commit()


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        remove_expired_files(db)
    finally:
        db.close()


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "QuickDrop"}


@app.post("/api/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    expires_in_hours: int = Form(24),
    db: Session = Depends(get_db)
):
    remove_expired_files(db)

    if expires_in_hours not in ALLOWED_EXPIRY_HOURS:
        raise HTTPException(
            status_code=400,
            detail="Choose an expiry of 1, 6, 24 or 168 hours."
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="Please choose a file.")

    token = secrets.token_urlsafe(18)
    suffix = Path(file.filename).suffix[:15]
    stored_filename = f"{token}{suffix}"
    destination = UPLOAD_DIR / stored_filename

    total_size = 0
    try:
        with destination.open("wb") as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break

                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File is too large. Maximum size is 50 MB."
                    )
                output.write(chunk)
    except Exception:
        if destination.exists():
            destination.unlink()
        raise
    finally:
        await file.close()

    now = datetime.utcnow()
    record = FileShare(
        token=token,
        original_filename=Path(file.filename).name[:255],
        stored_filename=stored_filename,
        content_type=file.content_type or "application/octet-stream",
        file_size=total_size,
        created_at=now,
        expires_at=now + timedelta(hours=expires_in_hours)
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        if destination.exists():
            destination.unlink()
        raise

    return {
        "message": "File uploaded successfully.",
        "token": record.token,
        "filename": record.original_filename,
        "file_size": record.file_size,
        "expires_at": record.expires_at.isoformat() + "Z",
        "download_url": str(request.base_url).rstrip("/") + f"/download/{record.token}"
    }


@app.get("/api/files/{token}")
def get_file_info(token: str, db: Session = Depends(get_db)):
    remove_expired_files(db)
    record = db.query(FileShare).filter(FileShare.token == token).first()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="This link is invalid or has expired."
        )

    return {
        "filename": record.original_filename,
        "file_size": record.file_size,
        "created_at": record.created_at.isoformat() + "Z",
        "expires_at": record.expires_at.isoformat() + "Z"
    }


@app.get("/download/{token}")
def download_file(token: str, db: Session = Depends(get_db)):
    remove_expired_files(db)
    record = db.query(FileShare).filter(FileShare.token == token).first()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="This link is invalid or has expired."
        )

    file_path = UPLOAD_DIR / record.stored_filename
    if not file_path.is_file():
        db.delete(record)
        db.commit()
        raise HTTPException(status_code=404, detail="The file is no longer available.")

    return FileResponse(
        path=file_path,
        filename=record.original_filename,
        media_type=record.content_type or "application/octet-stream"
    )
