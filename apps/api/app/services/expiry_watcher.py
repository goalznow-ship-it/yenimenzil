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
