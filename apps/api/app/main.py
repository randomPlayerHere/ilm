from fastapi import FastAPI

from app.domains.admin.router import router as admin_router
from app.domains.auth.router import router as auth_router
from app.domains.courses.router import router as courses_router
from app.domains.grading.router import router as grading_router
from app.domains.notifications.router import router as notifications_router
from app.domains.progress.router import router as progress_router
from app.domains.students.router import router as students_router

app = FastAPI(title="TeacherOS API", version="0.1.0")
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(courses_router)
app.include_router(grading_router)
app.include_router(students_router)
app.include_router(notifications_router)
app.include_router(progress_router)
