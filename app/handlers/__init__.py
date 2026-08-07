from app.handlers.start import router as start_router
from app.handlers.admin import router as admin_router
from app.handlers.attendance import router as attendance_router

__all__ = ["start_router", "admin_router", "attendance_router"]
