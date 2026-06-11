import uuid
import logging
from datetime import datetime, timezone
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.task import Task
from app.models.file import File
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskDetail
from app.auth.dependencies import get_current_user
from app.config import PAGE_SIZE

logger = logging.getLogger("uvicorn")
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    f = await db.get(File, data.file_id)
    if not f or f.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    task = Task(user_id=current_user.id, file_id=data.file_id, status="RUNNING")
    db.add(task)
    await db.commit()

    file_path = f.file_path
    try:
        # Pandas 同步读取文件
        if f.file_type in ("xlsx", "xls"):
            df = pd.read_excel(file_path)
        elif f.file_type == "csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_json(file_path)

        result = {
            "row_count": int(len(df)),
            "column_count": int(len(df.columns)),
            "columns": list(df.columns),
            "missing_values": {},
            "numeric_stats": {},
            "top_values": {},
        }
        for col in df.columns:
            missing = int(df[col].isna().sum())
            if missing > 0:
                result["missing_values"][col] = missing
            if pd.api.types.is_numeric_dtype(df[col]):
                cd = df[col].dropna()
                result["numeric_stats"][col] = {
                    "mean": round(float(cd.mean()), 4),
                    "std": round(float(cd.std()), 4),
                    "min": round(float(cd.min()), 4),
                    "max": round(float(cd.max()), 4),
                }
            if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
                vc = df[col].value_counts().head(10)
                result["top_values"][col] = [{"value": str(k), "count": int(v)} for k, v in vc.items()]

        task.status = "SUCCESS"
        task.result_data = result
        task.completed_at = datetime.now(timezone.utc)
        await db.commit()

    except Exception as exc:
        task.status = "FAILED"
        task.error_message = str(exc)[:1000]
        task.completed_at = datetime.now(timezone.utc)
        await db.commit()

    await db.refresh(task)
    return TaskResponse.model_validate(task)


@router.get("/", response_model=dict)
async def list_tasks(
    page: int = Query(1, ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * PAGE_SIZE
    total = await db.scalar(select(func.count()).select_from(Task).where(Task.user_id == current_user.id))
    result = await db.execute(
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(Task.created_at.desc())
        .offset(offset)
        .limit(PAGE_SIZE)
    )
    tasks = result.scalars().all()
    return {
        "items": [TaskResponse.model_validate(t) for t in tasks],
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
    }


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id, Task.user_id == current_user.id)
        .options(selectinload(Task.file))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    file_data = None
    if task.file:
        file_data = {
            "id": str(task.file.id),
            "original_filename": task.file.original_filename,
            "file_type": task.file.file_type,
            "file_size": task.file.file_size,
        }

    return TaskDetail(
        id=task.id, user_id=task.user_id, file_id=task.file_id,
        status=task.status, celery_task_id=task.celery_task_id,
        result_data=task.result_data, error_message=task.error_message,
        retry_count=task.retry_count,
        created_at=task.created_at, updated_at=task.updated_at, completed_at=task.completed_at,
        file=file_data,
    )


@router.get("/{task_id}/result")
async def download_result(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    if task.status != "SUCCESS":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="任务未完成")
    if not task.result_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="无结果数据")
    return JSONResponse(content=task.result_data)
