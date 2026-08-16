from .advertising import router as admin_advertising_router
from .dashboard import admin_router

__all__ = [
    "admin_agencies_router",
    "admin_analytics_router",
    "admin_audit_router",
    "admin_advertising_router",
    "admin_detail_router",
    "admin_features_router",
    "admin_intelligence_router",
    "admin_listings_router",
    "admin_locations_router",
    "admin_platform_router",
    "admin_promotions_router",
    "admin_reports_router",
    "admin_router",
    "admin_users_router",
    "admin_wallet_router",
]
