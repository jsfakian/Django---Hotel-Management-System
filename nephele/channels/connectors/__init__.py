# nephele/channels/connectors/__init__.py
"""OTA / channel connector registry."""

from __future__ import annotations

from typing import Dict, Optional, Type

from .base import ChannelConnector
from .booking_com import BookingComConnector
from .expedia import ExpediaConnector
from .ical import ICalConnector

_REGISTRY: Dict[str, Type[ChannelConnector]] = {
    "ical": ICalConnector,
    "booking_com": BookingComConnector,
    "expedia": ExpediaConnector,
}


def get_connector(channel_name: str) -> Optional[ChannelConnector]:
    """Return a connector instance for channel_name, or None if unknown."""
    cls = _REGISTRY.get(channel_name)
    if cls is None:
        return None
    return cls()


def register_connector(channel_name: str, connector_cls: Type[ChannelConnector]) -> None:
    _REGISTRY[channel_name] = connector_cls


__all__ = [
    "ChannelConnector",
    "ICalConnector",
    "BookingComConnector",
    "ExpediaConnector",
    "get_connector",
    "register_connector",
]
