from fastapi import APIRouter

from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.history import router as history_router
from app.routers.knowledge import router as knowledge_router
from app.routers.resume import router as resume_router

router = APIRouter()
router.include_router(health_router, tags=["system"])
router.include_router(auth_router, tags=["auth"])
router.include_router(history_router, tags=["history"])
router.include_router(chat_router, tags=["chat"])
router.include_router(resume_router, tags=["resume"])
router.include_router(knowledge_router, tags=["knowledge"])
