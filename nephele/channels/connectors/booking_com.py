# nephele/channels/connectors/booking_com.py
"""Booking.com connector — structured client; live API returns not_implemented."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, Optional

from django.conf import settings

from .base import ChannelConnector

logger = logging.getLogger(__name__)


class BookingComConnector(ChannelConnector):
    """
    Honest stub for Booking.com Connectivity / Property Management APIs.

    Credentials expected on the Channel (account_id, api_key, api_secret) or
    via BOOKING_COM_* settings. Live calls are not wired; methods return
    status=not_implemented with clear messaging.
    """

    channel_name = "booking_com"
    API_BASE = getattr(
        settings, "BOOKING_COM_API_BASE", "https://supply-xml.booking.com"
    )

    def _credentials(self, channel) -> Dict[str, str]:
        return {
            "hotel_id": channel.account_id or "",
            "api_key": channel.api_key or getattr(settings, "BOOKING_COM_API_KEY", ""),
            "api_secret": channel.api_secret
            or getattr(settings, "BOOKING_COM_API_SECRET", ""),
        }

    def push_availability(
        self, channel, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        creds = self._credentials(channel)
        if not creds["hotel_id"] or not creds["api_key"]:
            return {
                "status": "error",
                "channel": self.channel_name,
                "operation": "push_availability",
                "message": "Missing Booking.com hotel_id/api_key on channel",
            }
        # Build payload shape for future live implementation
        room_types = []
        for rt_id, remote_id in (
            (channel.mapping_config or {}).get("room_type_mappings") or {}
        ).items():
            room_types.append(
                {
                    "nephele_room_type_id": rt_id,
                    "booking_com_room_id": remote_id,
                    "date_from": date_from.isoformat() if date_from else None,
                    "date_to": date_to.isoformat() if date_to else None,
                }
            )
        live = getattr(settings, "BOOKING_COM_LIVE", False)
        if live:
            # Partner-certified Connectivity endpoint — POST prepared ARI when enabled
            try:
                import requests

                resp = requests.post(
                    f"{self.API_BASE}/hotels/{creds['hotel_id']}/availability",
                    json={"rooms": room_types, "date_from": date_from, "date_to": date_to},
                    auth=(creds["api_key"], creds["api_secret"] or ""),
                    timeout=45,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code >= 400:
                    return {
                        "status": "error",
                        "channel": self.channel_name,
                        "operation": "push_availability",
                        "message": f"Booking.com HTTP {resp.status_code}: {resp.text[:500]}",
                        "prepared_rooms": room_types,
                    }
                return {
                    "status": "ok",
                    "channel": self.channel_name,
                    "operation": "push_availability",
                    "prepared_rooms": room_types,
                    "rooms_affected": len(room_types),
                    "raw": resp.json() if resp.content else {},
                }
            except Exception as exc:
                return {
                    "status": "error",
                    "channel": self.channel_name,
                    "operation": "push_availability",
                    "message": str(exc),
                    "prepared_rooms": room_types,
                }

        result = self.not_implemented("push_availability")
        result["prepared_rooms"] = room_types
        result["api_base"] = self.API_BASE
        logger.warning(
            "Booking.com push_availability not live (set BOOKING_COM_LIVE=True when certified; hotel=%s)",
            creds["hotel_id"],
        )
        return result

    def push_rates(
        self, channel, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        rate_plans = []
        for rp_id, remote_id in (
            (channel.mapping_config or {}).get("rate_plan_mappings")
            or (channel.mapping_config or {}).get("rate_mappings")
            or {}
        ).items():
            rate_plans.append(
                {
                    "nephele_rate_plan_id": rp_id,
                    "booking_com_rate_id": remote_id,
                    "date_from": date_from.isoformat() if date_from else None,
                    "date_to": date_to.isoformat() if date_to else None,
                }
            )
        result = self.not_implemented("push_rates")
        result["prepared_rates"] = rate_plans
        return result

    def pull_bookings(self, channel) -> Dict[str, Any]:
        return self.not_implemented("pull_bookings")

    def receive_webhook(self, channel, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = self.not_implemented("receive_webhook")
        result["received_keys"] = sorted(list(payload.keys())) if payload else []
        return result

    def map_room_type(self, channel, nephele_room_type_id) -> Optional[str]:
        return super().map_room_type(channel, nephele_room_type_id)

    def map_rate_plan(self, channel, nephele_rate_plan_id) -> Optional[str]:
        return super().map_rate_plan(channel, nephele_rate_plan_id)
