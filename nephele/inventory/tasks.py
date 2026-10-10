# nephele/inventory/tasks.py
"""Celery tasks for inventory / booking engine."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def expire_booking_holds(self):
    """Expire held bookings past TTL and restore room-type allotment."""
    try:
        from inventory.booking_engine import expire_holds

        count = expire_holds()
        return {"expired": count}
    except Exception as exc:
        logger.exception("expire_booking_holds failed")
        raise self.retry(exc=exc)
