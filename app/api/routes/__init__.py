from .health import router as health_router
from .symptoms import router as symptoms_router
from .predictions import router as predictions_router
from .pages import router as pages_router

__all__ = [
    "health_router",
    "symptoms_router",
    "predictions_router",
    "pages_router",
]
