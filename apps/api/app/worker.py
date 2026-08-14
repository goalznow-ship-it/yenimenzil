"""Background worker entrypoint for the Docker worker service.

Runs periodic maintenance jobs in a separate process so the API process can
stay focused on request handling. In production these jobs run only here to
avoid duplicate saved-search notifications.

Jobs:
- property listing auto-expiry
- promotion auto-expiry
"""

from __future__ import annotations

import asyncio
import logging
import signal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("yenimenzil.worker")


async def run_forever() -> None:
    from app.services.expiry_watcher import (
        _check_expiring_promotions,
        _check_expiring_properties,
        _run_saved_search_alerts,
    )

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # pragma: no cover - windows
            pass

    logger.info("Worker started")
    while not stop.is_set():
        for job, name in (
            (_check_expiring_properties, "property expiry"),
            (_check_expiring_promotions, "promotion expiry"),
            (_run_saved_search_alerts, "saved-search alerts"),
        ):
            try:
                await job()
            except Exception:
                logger.exception("Job '%s' failed", name)
        try:
            await asyncio.wait_for(stop.wait(), timeout=1800)
        except TimeoutError:
            continue
    logger.info("Worker stopped")


if __name__ == "__main__":
    try:
        asyncio.run(run_forever())
    except KeyboardInterrupt:
        pass
