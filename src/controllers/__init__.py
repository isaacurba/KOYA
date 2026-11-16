from src.controllers.booking_controller import router as booking_router
from src.controllers.frontend_controller import router as frontend_router
from src.controllers.slot_controller import router as slot_router

__all__ = ["slot_router", "booking_router", "frontend_router"]
