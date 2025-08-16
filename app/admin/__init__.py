from fastapi import APIRouter
from .home import router as home_router
from .upload import router as upload_router
from .schools import router as schools_router
from .students import router as students_router
from .points import router as points_router
from .settings import router as settings_router
from ..maintenance import router as maintenance_router

router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(home_router)
router.include_router(upload_router)
router.include_router(schools_router)
router.include_router(students_router)
router.include_router(points_router)
router.include_router(settings_router)
router.include_router(maintenance_router)
