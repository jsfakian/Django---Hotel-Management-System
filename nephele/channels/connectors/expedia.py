# nephele/channels/connectors/expedia.py
"""Expedia connector skeleton — next OTA by demand (not implemented)."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from .base import ChannelConnector


class ExpediaConnector(ChannelConnector):
    """
    Thin stub for Expedia Partner Solutions / EQC.

    Registered for discovery and roadmap planning; all operations return
    not_implemented with a clear demand-driven message (never fake success).
    """

    channel_name = "expedia"
    DEMAND_MESSAGE = "next OTA by demand"

    def _stub(self, operation: str) -> Dict[str, Any]:
        result = self.not_implemented(operation)
        result["message"] = self.DEMAND_MESSAGE
        return result

    def push_availability(
        self, channel, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        return self._stub("push_availability")

    def push_rates(
        self, channel, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        return self._stub("push_rates")

    def pull_bookings(self, channel) -> Dict[str, Any]:
        return self._stub("pull_bookings")

    def receive_webhook(self, channel, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._stub("receive_webhook")
