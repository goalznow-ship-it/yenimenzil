from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    agency,
    agent,
    analytics,
    appointments,
    auth,
    favorite,
    health,
    location,
    messaging,
    moderation,
    notification,
    price_history,
    properties,
    report,
    saved_search,
    users,
    wallet,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(properties.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(saved_search.router)
api_router.include_router(agency.router)
api_router.include_router(agent.router)
api_router.include_router(favorite.router)
api_router.include_router(notification.router)
api_router.include_router(price_history.router)
api_router.include_router(analytics.router)
api_router.include_router(moderation.router)
api_router.include_router(report.router)
api_router.include_router(location.router)
api_router.include_router(messaging.router)
api_router.include_router(appointments.router)
api_router.include_router(wallet.router)
api_router.include_router(admin.admin_router)
