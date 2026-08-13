from .agency import admin_agencies_router
from .analytics import admin_analytics_router
from .audit import admin_audit_router
from .dashboard import admin_router
from .detail import admin_detail_router
from .features import admin_features_router
from .intelligence import admin_intelligence_router
from .listings import admin_listings_router
from .locations import admin_locations_router
from .promotions import admin_promotions_router
from .report import admin_reports_router
from .users import admin_users_router
from .wallet import router as admin_wallet_router

__all__ = [
    "admin_agencies_router",
    "admin_analytics_router",
    "admin_audit_router",
    "admin_detail_router",
    "admin_features_router",
    "admin_intelligence_router",
    "admin_listings_router",
    "admin_locations_router",
    "admin_promotions_router",
    "admin_reports_router",
    "admin_router",
    "admin_users_router",
    "admin_wallet_router",
]
