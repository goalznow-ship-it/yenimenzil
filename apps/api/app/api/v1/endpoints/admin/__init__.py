from .dashboard import admin_router
from .listings import admin_listings_router
from .detail import admin_detail_router

__all__ = ["admin_router", "admin_listings_router", "admin_detail_router"]
