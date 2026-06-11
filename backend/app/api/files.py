import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.file import File
from app.models.user import User
from app.schemas.file import FileResponse
from app.auth.dependencies import get_current_user
from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE, PAGE_SIZE

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type {ext} not allowed")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    stored_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 50MB)")

    with open(file_path, "wb") as f:
        f.write(content)

    db_file = File(
        user_id=current_user.id,
        filename=stored_name,
        original_filename=file.filename or "unknown",
        file_path=file_path,
        file_size=len(content),
        file_type=ext.lstrip("."),
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)

    return FileResponse.model_validate(db_file)


@router.get("/", response_model=dict)
async def list_files(
    page: int = Query(1, ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * PAGE_SIZE
    total = await db.scalar(select(func.count()).select_from(File).where(File.user_id == current_user.id))
    result = await db.execute(
        select(File).where(File.user_id == current_user.id).order_by(File.created_at.desc()).offset(offset).limit(PAGE_SIZE)
    )
    files = result.scalars().all()
    return {
        "items": [FileResponse.model_validate(f) for f in files],
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
    }


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(File).where(File.id == file_id, File.user_id == current_user.id))
    f = result.scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse.model_validate(f)
