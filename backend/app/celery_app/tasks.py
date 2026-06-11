import uuid
import logging
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from celery.exceptions import MaxRetriesExceededError
from app.celery_app.celery import celery
from app.config import SQLITE_SYNC
from app.models.task import Task
from app.models.file import File

logger = logging.getLogger("celery")

# 同步 SQLite 引擎 + WAL 模式
sync_engine = create_engine(SQLITE_SYNC)

@event.listens_for(sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

SyncSession = sessionmaker(bind=sync_engine)


def _do_process(task_id: str):
    """实际数据处理逻辑（可被 Celery 任务或同步调用复用）"""
    db: Session = SyncSession()
    try:
        task = db.get(Task, uuid.UUID(task_id))
        if not task:
            return {"error": "Task not found"}

        task.status = "RUNNING"
        db.commit()

        f = db.get(File, task.file_id)
        if not f:
            raise ValueError("File not found")

        file_path = f.file_path
        if f.file_type in ("xlsx", "xls"):
            df = pd.read_excel(file_path)
        elif f.file_type == "csv":
            df = pd.read_csv(file_path)
        elif f.file_type == "json":
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {f.file_type}")

        result = {
            "row_count": len(df),
            "column_count": len(df.columns),
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
                col_data = df[col].dropna()
                result["numeric_stats"][col] = {
                    "mean": round(float(col_data.mean()), 4),
                    "std": round(float(col_data.std()), 4),
                    "min": round(float(col_data.min()), 4),
                    "max": round(float(col_data.max()), 4),
                }

            if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
                value_counts = df[col].value_counts().head(10)
                result["top_values"][col] = [
                    {"value": str(k), "count": int(v)} for k, v in value_counts.items()
                ]

        task.status = "SUCCESS"
        task.result_data = result
        task.completed_at = datetime.now(timezone.utc)
        db.commit()

        return {"status": "success", "task_id": task_id}

    except Exception as exc:
        task = db.get(Task, uuid.UUID(task_id))
        if task:
            task.status = "FAILED"
            task.error_message = str(exc)[:1000]
            task.completed_at = datetime.now(timezone.utc)
            db.commit()
        raise

    finally:
        db.close()


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_file(self, task_id: str):
    """Celery 任务入口"""
    db: Session = SyncSession()
    try:
        task = db.get(Task, uuid.UUID(task_id))
        if task:
            task.retry_count = self.request.retries
            db.commit()
    finally:
        db.close()

    try:
        return _do_process(task_id)
    except MaxRetriesExceededError:
        db = SyncSession()
        try:
            task = db.get(Task, uuid.UUID(task_id))
            if task:
                task.status = "FAILED"
                task.error_message = "已达最大重试次数"
                task.completed_at = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()
        raise
    except Exception as exc:
        db = SyncSession()
        try:
            task = db.get(Task, uuid.UUID(task_id))
            if task:
                task.retry_count = self.request.retries
                task.error_message = str(exc)[:1000]
                db.commit()
        finally:
            db.close()
        raise
