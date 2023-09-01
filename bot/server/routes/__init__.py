from .api import router as api_router
from .static import router as static_router


__all__ = (
    "api_router",
    "static_router",
)
