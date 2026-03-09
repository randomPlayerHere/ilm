from fastapi import FastAPI

from app.domains.admin.router import router as admin_router
from app.domains.auth.router import router as auth_router
from app.domains.courses.router import router as courses_router

app = FastAPI(title="TeacherOS API", version="0.1.0")
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(courses_router)
