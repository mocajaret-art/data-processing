import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text, event
from app.config import PG_ASYNC, SQLITE_ASYNC

logger = logging.getLogger("uvicorn")

DATABASE_ENGINE_URL = SQLITE_ASYNC

# SQLite 异步引擎 + WAL 模式
engine = create_async_engine(DATABASE_ENGINE_URL, echo=False)

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """启用 WAL 模式，允许并发读写"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def try_postgres():
    """启动时尝试连接 PostgreSQL，成功则切换引擎"""
    global engine, async_session, DATABASE_ENGINE_URL
    pg_engine = create_async_engine(PG_ASYNC, echo=False)
    try:
        async with pg_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        engine = pg_engine
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        DATABASE_ENGINE_URL = PG_ASYNC
        logger.info("Using PostgreSQL")
    except Exception:
        await pg_engine.dispose()
        logger.warning("PostgreSQL unavailable, using SQLite")


async def get_db():
    async with async_session() as session:
        yield session
