"""Background expiry watcher for property listings and promotions."""

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.db.session import async_session_factory
from app.models.enums import PropertyStatus
from app.models.promotion import PromotionPurchase
from app.models.property import Property


async def start_expiry_watcher() -> None:
    """Start the background expiry watcher loop."""

    async def watcher_loop() -> None:
        while True:
            try:
                await _check_expiring_properties()
            except Exception as e:  # noqa: BLE001 - watcher loop must never die
                print(f"Expiry watcher error: {e}")
            try:
                await _check_expiring_promotions()
            except Exception as e:  # noqa: BLE001 - watcher loop must never die
                print(f"Promotion expiry watcher error: {e}")
            try:
                await _run_saved_search_alerts()
            except Exception as e:  # noqa: BLE001 - watcher loop must never die
                print(f"Saved-search alert watcher error: {e}")
            await asyncio.sleep(1800)  # check every 30 minutes

    task = asyncio.create_task(watcher_loop())
    # Store reference so it doesn't get garbage collected
    start_expiry_watcher._task = task


async def stop_expiry_watcher() -> None:
    """Stop the background expiry watcher loop."""
    task = getattr(start_expiry_watcher, "_task", None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def _check_expiring_properties() -> None:
    """Check for properties that have expired and update their status."""
    async with async_session_factory() as session:
        now = datetime.now(UTC)

        # Find properties with expires_at in the past and status still active
        result = await session.execute(
            select(Property).where(
                Property.expires_at < now,
                Property.status == PropertyStatus.ACTIVE.value,
            )
        )
        expiring = result.scalars().all()

        for prop in expiring:
            prop.status = PropertyStatus.EXPIRED.value
            print(
                f"Property {prop.id} ({prop.title}) automatically expired at {prop.expires_at}"
            )

        if expiring:
            await session.commit()


async def _check_expiring_promotions() -> None:
    """Expire promotions whose promotion_expires_at has passed.

    Clears the promotion flags on the listing and marks matching
    promotion purchases as expired.
    """
    async with async_session_factory() as session:
        now = datetime.now(UTC)
        before = now - timedelta(minutes=5)

        result = await session.execute(
            update(Property)
            .where(
                Property.is_promoted.is_(True),
                Property.promotion_expires_at < before,
            )
            .values(
                is_promoted=False,
                is_premium=False,
                promotion_tier=None,
            )
            .returning(Property.id)
        )
        expired_ids = [row[0] for row in result.all()]

        if expired_ids:
            await session.execute(
                update(PromotionPurchase)
                .where(
                    PromotionPurchase.property_id.in_(expired_ids),
                    PromotionPurchase.status == "active",
                )
                .values(status="expired")
            )
            await session.commit()
            print(f"Expired {len(expired_ids)} promotion(s)")


_last_alert_run: datetime | None = None
ALERT_INTERVAL = timedelta(hours=24)


async def _run_saved_search_alerts() -> bool:
    """Daily digest: notify users when new active listings match saved searches.

    Returns True when a run was performed.
    """
    global _last_alert_run
    now = datetime.now(UTC)
    if _last_alert_run is not None and now - _last_alert_run < ALERT_INTERVAL:
        return False
    _last_alert_run = now

    from urllib.parse import urlencode

    from app.models.notification import Notification
    from app.models.property import PropertyLocation
    from app.models.saved_search import SavedSearch

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

        created = 0
        for search in searches:
            filters = search.filters or {}
            stmt = select(Property.id).where(
                Property.status == PropertyStatus.ACTIVE.value,
                Property.published_at >= since,
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

            query = urlencode(
                {key: str(value) for key, value in filters.items() if value is not None}
            )
            session.add(
                Notification(
                    user_id=search.user_id,
                    title=f"{search.name}: {len(matches)} yeni elan",
                    message=(
                        f"Axtarışınıza uyğun {len(matches)} yeni elan dərc olundu."
                    ),
                    kind="saved_search",
                    link=f"/search?{query}",
                )
            )
            created += 1

        if created:
            await session.commit()
            print(f"Saved-search alerts sent to {created} search(es)")
    return True
