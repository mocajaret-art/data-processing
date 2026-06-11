from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routers
from app.database import try_postgres, engine
from app.models.user import Base
import logging

logger = logging.getLogger("uvicorn")

app = FastAPI(title="FBS - File Batch System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router)


@app.on_event("startup")
async def startup():
    # 尝试 PostgreSQL，不可用则保持 SQLite
    await try_postgres()
    # 创建表
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ready")
    except Exception as e:
        logger.error(f"Table creation failed: {e}")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
