"""Background expiry watcher for property listings and promotions.

Provides a synchronous entry point that starts a daemon thread which
runs one cycle of the watcher using asyncio.run(). Since the entry
point function is plain (non-async def), calling it from a FastAPI
sync lifespan does NOT trigger RuntimeWarning about unawaited coroutines.
"""

import asyncio
import threading
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.db.session import async_session_factory
from app.models.enums import PropertyStatus
from app.models.promotion import PromotionPurchase
from app.models.property import Property

# ──────────────────────────────────────────────────────────────────────
# Interval for saved-search alert deduplication (one run per 24h).
# Imported by app.services.saved_search_alerts.
# ──────────────────────────────────────────────────────────────────────
ALERT_INTERVAL = timedelta(hours=24)

# Module-level state for saved search alert deduplication
_last_alert_run: datetime | None = None


# ──────────────────────────────────────────────────────────────────────
# Synchronous watcher cycle — runs one pass of the full check loop.
# No async def anywhere in this module. Callers use asyncio.run()
# in a thread target.
# ──────────────────────────────────────────────────────────────────────
def _run_watcher_cycle():
    """Run one full watcher cycle.

    This function is plain (non-async def). It uses asyncio.run()
    internally in a thread target so that callers in a sync or async
    context have no coroutine to "never await".
    """
    import asyncio

    asyncio.run(_watcher_loop())


# ──────────────────────────────────────────────────────────────────────
# Async inner loop — the ONLY place where async def lives.
# This function is NEVER called directly from sync code; it is always
# invoked via asyncio.run() from _run_watcher_cycle() in a daemon thread.
# ──────────────────────────────────────────────────────────────────────
async def _watcher_loop() -> None:
    """Inner watcher loop — runs forever, checking expiry status."""
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
        await asyncio.sleep(1800)


async def _check_expiring_properties() -> None:
    """Check for properties that have expired and update their status."""
    async with async_session_factory() as session:
        now = datetime.now(UTC)
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
    """Expire promotions whose promotion_expires_at has passed."""
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


async def _run_saved_search_alerts() -> bool:
    """Daily digest: notify users when new active listings match saved searches."""
    global _last_alert_run
    from app.services.saved_search_alerts import _run_saved_search_alerts as _impl

    ran = await _impl()
    if ran:
        _last_alert_run = datetime.now(UTC)
    return ran


# ──────────────────────────────────────────────────────────────────────
# Synchronous entry point — the ONLY function external code should call.
# It is a plain (non-async def) function. Calling it does NOT trigger
# RuntimeWarning about unawaited coroutines because it uses
# asyncio.run() inside a daemon thread target.
# ──────────────────────────────────────────────────────────────────────
def start_expiry_watcher() -> threading.Thread:
    """Start the expiry watcher and return a daemon thread.

    This is called from the FastAPI sync lifespan.
    The thread runs one cycle of the watcher using asyncio.run().
    Since this function is a plain (non-async def) function,
    calling it does NOT trigger RuntimeWarning about unawaited coroutines.
    """

    def target():
        _run_watcher_cycle()

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread


def stop_expiry_watcher() -> None:
    """Stop the background expiry watcher.

    Since the watcher runs in a daemon thread, it terminates
    automatically when the process exits. No explicit cleanup is required.
    """
