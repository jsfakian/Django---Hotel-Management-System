# nephele/channels/mapping_utils.py
"""Canonical channel mapping_config helpers (room/rate key aliases)."""

from __future__ import annotations

from typing import Any, Dict


def normalize_mapping_config(cfg: Dict[str, Any] | None) -> Dict[str, Dict[str, Any]]:
    """
    Accept both legacy and catalog keys; return one internal shape:

    - room_type_mappings  (aliases: room_mappings)
    - rate_plan_mappings  (aliases: rate_mappings)
    """
    raw = cfg or {}
    room = (
        raw.get("room_type_mappings")
        or raw.get("room_mappings")
        or {}
    )
    rate = (
        raw.get("rate_plan_mappings")
        or raw.get("rate_mappings")
        or {}
    )
    return {
        "room_type_mappings": {str(k): v for k, v in dict(room).items()},
        "rate_plan_mappings": {str(k): v for k, v in dict(rate).items()},
    }


def reverse_room_type_map(cfg: Dict[str, Any] | None) -> Dict[str, int]:
    """remote room type id → local room type id."""
    room = normalize_mapping_config(cfg)["room_type_mappings"]
    out: Dict[str, int] = {}
    for local_id, remote_id in room.items():
        if remote_id in (None, ""):
            continue
        try:
            out[str(remote_id)] = int(local_id)
        except (TypeError, ValueError):
            continue
    return out
