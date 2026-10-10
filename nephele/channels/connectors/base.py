# nephele/channels/connectors/base.py
"""Abstract channel connector interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, List, Optional


class ChannelConnector(ABC):
    """Interface every OTA / calendar connector must implement."""

    channel_name: str = "base"

    @abstractmethod
    def push_availability(
        self, channel, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Push allotment / availability to the remote channel."""

    @abstractmethod
    def push_rates(
        self, channel, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Push rate plan prices to the remote channel."""

    @abstractmethod
    def pull_bookings(self, channel) -> Dict[str, Any]:
        """Pull remote reservations into Nephele."""

    @abstractmethod
    def receive_webhook(self, channel, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an inbound webhook payload."""

    def map_room_type(self, channel, nephele_room_type_id) -> Optional[str]:
        """Map Nephele room type id → remote room type id via mapping_config."""
        mappings = (channel.mapping_config or {}).get("room_type_mappings") or {}
        if not mappings:
            # Fall back to legacy room_mappings keyed by physical room id
            mappings = (channel.mapping_config or {}).get("room_mappings") or {}
        return mappings.get(str(nephele_room_type_id))

    def map_rate_plan(self, channel, nephele_rate_plan_id) -> Optional[str]:
        """Map Nephele rate plan id → remote rate code via mapping_config."""
        mappings = (channel.mapping_config or {}).get("rate_plan_mappings") or {}
        if not mappings:
            mappings = (channel.mapping_config or {}).get("rate_mappings") or {}
        return mappings.get(str(nephele_rate_plan_id))

    def not_implemented(self, operation: str) -> Dict[str, Any]:
        return {
            "status": "not_implemented",
            "channel": self.channel_name,
            "operation": operation,
            "message": f"{self.channel_name} live API is not available for {operation}",
        }
