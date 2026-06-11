import os
from pathlib import Path

# 从项目根目录加载 .env（如果存在）
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

# 数据库
PG_ASYNC = os.getenv("DATABASE_URL", "postgresql+asyncpg://fbs:fbs123@localhost:5432/fbs")
PG_SYNC = os.getenv("DATABASE_URL_SYNC", "postgresql://fbs:fbs123@localhost:5432/fbs")
SQLITE_ASYNC = "sqlite+aiosqlite:///./fbs.db"
SQLITE_SYNC = "sqlite:///./fbs.db"

DATABASE_URL = PG_ASYNC
DATABASE_URL_SYNC = PG_SYNC

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# 上传
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}
PAGE_SIZE = 20
