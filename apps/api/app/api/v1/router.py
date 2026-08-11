from fastapi import APIRouter

from app.api.v1.endpoints import (
    agency,
    agent,
    auth,
    favorite,
    health,
    location,
    notification,
    price_history,
    properties,
    saved_search,
    users,
    analytics,
    moderation,
    report,
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
