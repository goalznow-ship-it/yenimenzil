"""Daily saved-search email digest with deduplication.

Matches new active listings against saved searches, creates in-app
notifications (deduplicated) and sends one HTML email digest per user with
a signed one-click unsubscribe link.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from urllib.parse import urlencode

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.session import async_session_factory
from app.models.enums import PropertyStatus
from app.models.notification import Notification
from app.models.property import Property, PropertyLocation
from app.models.saved_search import SavedSearch
from app.models.user import User
from app.models.verification import NotificationPreference
from app.services.email import send_email
from app.services.expiry_watcher import ALERT_INTERVAL

logger = logging.getLogger(__name__)

_LAST_RUN_KEY = "saved_search_alerts:last_run"
_last_alert_run: datetime | None = None


async def _is_due(now: datetime) -> bool:
    """Throttle to one run per 24h; Redis key survives restarts."""
    global _last_alert_run
    if _last_alert_run is not None and now - _last_alert_run < ALERT_INTERVAL:
        return False
    try:
        settings = get_settings()
        client = aioredis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=True,
        )
        last = await client.get(_LAST_RUN_KEY)
        if last:
            last_dt = datetime.fromisoformat(last)
            if now - last_dt < ALERT_INTERVAL:
                _last_alert_run = last_dt
                await client.aclose()
                return False
        await client.set(_LAST_RUN_KEY, now.isoformat(), ex=60 * 60 * 24 * 2)
        await client.aclose()
    except Exception as exc:  # noqa: BLE001 - best-effort dedup
        logger.debug("Alert dedup Redis unavailable: %s", exc)
        if _last_alert_run is None:
            # No Redis and no in-memory marker: still run once per process.
            pass
    _last_alert_run = now
    return True


async def _already_notified_ids(
    session, user_id: uuid.UUID, search_id: uuid.UUID
) -> set:
    """Property ids already alerted for this search (dedup window)."""
    rows = (
        (
            await session.execute(
                select(Notification).where(
                    Notification.user_id == user_id,
                    Notification.kind == "saved_search",
                    Notification.created_at >= datetime.now(UTC) - ALERT_INTERVAL,
                )
            )
        )
        .scalars()
        .all()
    )
    seen: set = set()
    for n in rows:
        payload = n.payload or {}
        if payload.get("search_id") == str(search_id):
            seen.update(payload.get("property_ids", []))
    return seen


async def _email_preference(session, user_id: uuid.UUID) -> bool:
    """Whether the user wants alert emails (defaults to enabled)."""
    rows = (
        (
            await session.execute(
                select(NotificationPreference).where(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.kind.in_(["listing", "general"]),
                )
            )
        )
        .scalars()
        .all()
    )
    if not rows:
        return True
    return any(r.email_enabled for r in rows)


def _digest_html(
    items: list[tuple[str, str, str, str]], unsubscribe_url: str, app_url: str
) -> str:
    rows = "".join(
        f"""
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid #eef0f2;">
            <a href="{url}" style="color:#0a7d5c;font-weight:600;text-decoration:none;">{title}</a>
            <div style="color:#5b6570;font-size:13px;margin-top:2px;">{meta}</div>
          </td>
        </tr>"""
        for title, meta, url, _ in items
    )
    return f"""<!DOCTYPE html>
<html><body style="margin:0;background:#f4f6f8;font-family:Arial,sans-serif;">
<div style="max-width:560px;margin:24px auto;background:#fff;border-radius:12px;overflow:hidden;">
  <div style="background:#0a7d5c;padding:20px 24px;">
    <span style="color:#fff;font-size:18px;font-weight:700;">YeniMenzil.az</span>
  </div>
  <div style="padding:24px;">
    <h2 style="margin:0 0 8px;font-size:18px;color:#141a17;">Yeni elanlar tapıldı</h2>
    <p style="color:#5b6570;font-size:14px;margin:0 0 16px;">
      Saxladığınız axtarışlara uyğun yeni elanlar dərc olunub.
    </p>
    <table style="width:100%;border-collapse:collapse;">{rows}</table>
    <p style="margin-top:20px;color:#8a939b;font-size:12px;">
      <a href="{unsubscribe_url}" style="color:#8a939b;">E-poçt bildirişlərindən imtina et</a>
    </p>
  </div>
</div>
</body></html>"""


def _digest_text(items: list[tuple[str, str, str, str]], unsubscribe_url: str) -> str:
    lines = ["Saxladığınız axtarışlara uyğun yeni elanlar:", ""]
    for title, meta, url, _ in items:
        lines.append(f"- {title} ({meta})\n  {url}")
    lines.extend(["", f"İmtina: {unsubscribe_url}"])
    return "\n".join(lines)


async def _run_saved_search_alerts() -> bool:
    """Run the daily digest; returns True when a run was performed."""
    now = datetime.now(UTC)
    if not await _is_due(now):
        return False

    settings = get_settings()
    app_url = settings.PUBLIC_APP_URL.rstrip("/")

    async with async_session_factory() as session:
        since = now - ALERT_INTERVAL
        searches = (
            (
                await session.execute(
                    select(SavedSearch).where(SavedSearch.is_active.is_(True))
                )
            )
            .scalars()
            .all()
        )

        # group matches per user for the email digest
        per_user: dict[uuid.UUID, list[tuple[str, str, str, str]]] = {}
        notified_searches = 0

        for search in searches:
            filters = search.filters or {}
            stmt = (
                select(Property)
                .options(selectinload(Property.location))
                .where(
                    Property.status == PropertyStatus.ACTIVE.value,
                    Property.published_at >= since,
                )
            )
            deal_type = filters.get("deal_type")
            if deal_type:
                stmt = stmt.where(Property.deal_type == deal_type)
            property_type = filters.get("property_type")
            if property_type:
                stmt = stmt.where(Property.property_type == property_type)
            price_min = filters.get("price_min")
            if isinstance(price_min, (int, float)):
                stmt = stmt.where(Property.price >= float(price_min))
            price_max = filters.get("price_max")
            if isinstance(price_max, (int, float)):
                stmt = stmt.where(Property.price <= float(price_max))
            rooms = filters.get("rooms")
            if rooms is not None and str(rooms).isdigit():
                stmt = stmt.where(Property.rooms == int(rooms))
            city = filters.get("city") or filters.get("location_city")
            district = filters.get("district")
            metro = filters.get("metro")
            if city or district or metro:
                stmt = stmt.join(
                    PropertyLocation, PropertyLocation.property_id == Property.id
                )
                if city:
                    stmt = stmt.where(PropertyLocation.city == city)
                if district:
                    stmt = stmt.where(PropertyLocation.district == district)
                if metro:
                    stmt = stmt.where(PropertyLocation.metro == metro)

            matches = (await session.execute(stmt)).scalars().all()
            if not matches:
                continue

            already = await _already_notified_ids(session, search.user_id, search.id)
            fresh = [p for p in matches if str(p.id) not in already]
            if not fresh:
                continue

            query = urlencode(
                {key: str(value) for key, value in filters.items() if value is not None}
            )
            session.add(
                Notification(
                    user_id=search.user_id,
                    title=f"{search.name}: {len(fresh)} yeni elan",
                    message=(f"Axtarışınıza uyğun {len(fresh)} yeni elan dərc olundu."),
                    kind="saved_search",
                    link=f"/search?{query}",
                    payload={
                        "search_id": str(search.id),
                        "property_ids": [str(p.id) for p in fresh],
                    },
                )
            )
            notified_searches += 1

            if search.email_enabled:
                for p in fresh:
                    location = p.location
                    meta_parts = [
                        f"{p.price:,.0f} AZN",
                        f"{p.rooms} otaq",
                        f"{float(p.area_total):.0f} m²",
                    ]
                    if location and location.city:
                        meta_parts.append(location.city)
                    url = f"{app_url}/property/{p.id}"
                    per_user.setdefault(search.user_id, []).append(
                        (p.title, " · ".join(meta_parts), url, str(p.id))
                    )

        if notified_searches:
            await session.commit()
            logger.info("Saved-search alerts: %s search(es)", notified_searches)

        # Email digests (one per user)
        email_sent = 0
        for user_id, items in per_user.items():
            if not await _email_preference(session, user_id):
                continue
            user = await session.get(User, user_id)
            if user is None or not user.email:
                continue
            # One unsubscribe token per search the user has
            user_searches = (
                (
                    await session.execute(
                        select(SavedSearch).where(SavedSearch.user_id == user_id)
                    )
                )
                .scalars()
                .all()
            )
            if not user_searches:
                continue
            from app.api.v1.endpoints.saved_search import unsubscribe_token

            search_id = user_searches[0].id
            token = unsubscribe_token(search_id, user_id)
            unsubscribe_url = f"{app_url}/saved-searches/unsubscribe?search_id={search_id}&token={token}"
            send_email(
                to=user.email,
                subject=f"YeniMenzil.az: {len(items)} yeni elan tapıldı",
                text_body=_digest_text(items, unsubscribe_url),
                html_body=_digest_html(items, unsubscribe_url, app_url),
            )
            email_sent += 1

        if email_sent:
            logger.info("Saved-search digest emails sent: %s", email_sent)
    return True
