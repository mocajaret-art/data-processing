from app.api.auth import router as auth_router
from app.api.files import router as files_router
from app.api.tasks import router as tasks_router

routers = [auth_router, files_router, tasks_router]
