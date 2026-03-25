from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.domains.admin.router import router as admin_router
from app.domains.auth.router import router as auth_router
from app.domains.courses.router import router as courses_router
from app.domains.onboarding.router import router as onboarding_router
from app.domains.grading.router import router as grading_router
from app.domains.health.router import router as health_router
from app.domains.notifications.router import router as notifications_router
from app.domains.progress.router import router as progress_router
from app.domains.push.router import router as push_router
from app.domains.storage.router import router as storage_router
from app.domains.students.router import router as students_router

app = FastAPI(title="TeacherOS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "http://localhost:19006"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(admin_router)
app.include_router(courses_router)
app.include_router(grading_router)
app.include_router(students_router)
app.include_router(storage_router)
app.include_router(push_router)
app.include_router(notifications_router)
app.include_router(progress_router)
