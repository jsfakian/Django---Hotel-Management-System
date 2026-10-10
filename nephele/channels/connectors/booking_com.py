# nephele/channels/connectors/booking_com.py
"""Booking.com connector — live HTTP when BOOKING_COM_LIVE + credentials."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

from django.conf import settings

from channels.mapping_utils import normalize_mapping_config

from .base import ChannelConnector

logger = logging.getLogger(__name__)


def _daterange(date_from: Optional[date], date_to: Optional[date]):
    if not date_from or not date_to or date_to <= date_from:
        return []
    cur = date_from
    while cur < date_to:
        yield cur
        cur += timedelta(days=1)


def _allotment_rows(room_type_id: int, date_from, date_to) -> List[Dict[str, Any]]:
    """Build per-night allotment payload from RoomTypeAvailability."""
    try:
        from inventory.models import RoomTypeAvailability
    except Exception:
        return []
    qs = RoomTypeAvailability.objects.filter(room_type_id=room_type_id)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lt=date_to)
    rows = []
    for avail in qs.order_by("date"):
        rows.append(
            {
                "date": avail.date.isoformat(),
                "allotment": avail.allotment,
                "booked": avail.booked,
                "available": avail.available_units,
                "stop_sell": bool(avail.stop_sell or avail.closed),
                "min_stay": avail.min_stay,
                "max_stay": avail.max_stay,
                "cta": avail.cta,
                "ctd": avail.ctd,
            }
        )
    if rows or not date_from or not date_to:
        return rows
    # No calendar rows yet — emit zero allotment placeholders for the range
    return [
        {
            "date": d.isoformat(),
            "allotment": 0,
            "booked": 0,
            "available": 0,
            "stop_sell": False,
        }
        for d in _daterange(date_from, date_to)
    ]


def _rate_price_rows(
    rate_plan_id: int, date_from, date_to, room_type_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Build per-night price payload from RatePlanPrice."""
    try:
        from inventory.models import RatePlanPrice
        from inventory.services import _occupancy_price
    except Exception:
        return []
    qs = RatePlanPrice.objects.filter(rate_plan_id=rate_plan_id)
    if room_type_id:
        qs = qs.filter(room_type_id=room_type_id)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lt=date_to)
    rows = []
    for price in qs.order_by("date"):
        nightly = _occupancy_price(price, 2) or price.price_1 or Decimal("0")
        rows.append(
            {
                "date": price.date.isoformat(),
                "room_type_id": price.room_type_id,
                "price": str(nightly),
                "price_1": str(price.price_1) if price.price_1 is not None else None,
                "price_2": str(price.price_2) if price.price_2 is not None else None,
                "currency": "EUR",
            }
        )
    return rows


def _api_base() -> str:
    return getattr(
        settings, "BOOKING_COM_API_BASE", "https://supply-xml.booking.com"
    ).rstrip("/")


def _parse_http_body(resp) -> Dict[str, Any]:
    body: Any
    try:
        body = resp.json() if resp.content else {}
    except ValueError:
        body = {"raw": resp.text[:2000]}
    return {"status_code": resp.status_code, "body": body, "text": resp.text[:500]}


def _http_post_json(url: str, payload: dict, creds: Dict[str, str]) -> Dict[str, Any]:
    import requests

    resp = requests.post(
        url,
        json=payload,
        auth=(creds["api_key"], creds["api_secret"] or ""),
        timeout=45,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    return _parse_http_body(resp)


def _http_put_json(url: str, payload: dict, creds: Dict[str, str]) -> Dict[str, Any]:
    import requests

    resp = requests.put(
        url,
        json=payload,
        auth=(creds["api_key"], creds["api_secret"] or ""),
        timeout=45,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    return _parse_http_body(resp)


def _http_get_json(url: str, creds: Dict[str, str], params: Optional[dict] = None) -> Dict[str, Any]:
    import requests

    resp = requests.get(
        url,
        params=params or {},
        auth=(creds["api_key"], creds["api_secret"] or ""),
        timeout=45,
        headers={"Accept": "application/json, application/xml"},
    )
    body: Any
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "xml" in ctype or (resp.content and resp.content[:1] == b"<"):
        body = {"raw_xml": resp.text[:5000]}
    else:
        try:
            body = resp.json() if resp.content else {}
        except ValueError:
            body = {"raw": resp.text[:2000]}
    return {"status_code": resp.status_code, "body": body, "text": resp.text[:500]}


def _error_result(
    channel_name: str, operation: str, message: str, **extra
) -> Dict[str, Any]:
    out = {
        "status": "error",
        "channel": channel_name,
        "operation": operation,
        "message": message,
    }
    out.update(extra)
    return out


def _ok_result(channel_name: str, operation: str, **extra) -> Dict[str, Any]:
    out = {"status": "ok", "channel": channel_name, "operation": operation}
    out.update(extra)
    return out


def _pick(payload: dict, *keys, default=""):
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return default


def _reservation_root(payload: Dict[str, Any]) -> Dict[str, Any]:
    return payload.get("reservation") or payload.get("booking") or payload


def _first_room(res: Dict[str, Any]) -> Dict[str, Any]:
    rooms = res.get("rooms") or res.get("room_stays") or []
    return rooms[0] if rooms else {}


def normalize_booking_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Map Booking.com webhook / reservation dict → Nephele normalized booking."""
    if not payload:
        return {}
    res = _reservation_root(payload)
    guest = res.get("guest") or res.get("customer") or {}
    first_room = _first_room(res)
    return {
        "external_id": str(
            _pick(res, "id", "reservation_id", "booking_id", "hotel_reservation_id")
        ),
        "status": str(_pick(res, "status", "reservation_status", default="confirmed")),
        "check_in": _pick(
            res, "checkin", "check_in", "arrival_date",
            default=_pick(first_room, "arrival_date"),
        ),
        "check_out": _pick(
            res, "checkout", "check_out", "departure_date",
            default=_pick(first_room, "departure_date"),
        ),
        "guest_first_name": _pick(guest, "first_name", "firstname", "given_name"),
        "guest_last_name": _pick(guest, "last_name", "lastname", "surname"),
        "guest_email": _pick(guest, "email", "email_address"),
        "room_type_remote_id": str(
            _pick(first_room, "room_id", "room_type_id", "roomreservation_id")
            or _pick(res, "room_id", "room_type_id")
        ),
        "rate_plan_remote_id": str(
            _pick(first_room, "rate_id", "rate_plan_id")
            or _pick(res, "rate_id", "rate_plan_id")
        ),
        "currency": _pick(res, "currency", "currencycode", default="EUR"),
        "total_amount": _pick(res, "total", "total_price", "price"),
        "raw": payload,
    }


def _parse_reservations_from_body(body: Any) -> List[Dict[str, Any]]:
    if isinstance(body, list):
        return [normalize_booking_payload(b) for b in body]
    if not isinstance(body, dict):
        return []
    if "raw_xml" in body:
        return _parse_reservations_xml(body["raw_xml"])
    for key in ("reservations", "bookings", "data", "results"):
        if isinstance(body.get(key), list):
            return [normalize_booking_payload(b) for b in body[key]]
    if any(k in body for k in ("id", "reservation_id", "booking_id", "reservation")):
        return [normalize_booking_payload(body)]
    return []


def _parse_reservations_xml(xml_text: str) -> List[Dict[str, Any]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    bookings = []
    for node in root.iter():
        tag = node.tag.split("}")[-1].lower()
        if tag not in ("reservation", "hotelreservation", "booking"):
            continue
        flat = {child.tag.split("}")[-1].lower(): (child.text or "") for child in node}
        flat.update({k.lower(): v for k, v in node.attrib.items()})
        bookings.append(normalize_booking_payload(flat))
    return bookings


class BookingComConnector(ChannelConnector):
    """
    Booking.com Connectivity client.

    When BOOKING_COM_LIVE is False (default), methods return status=not_implemented
    and never fake success. When live + credentials, real HTTP calls are made
    against BOOKING_COM_API_BASE (JSON preferred; XML pull accepted).
    """

    channel_name = "booking_com"

    @property
    def API_BASE(self) -> str:
        return _api_base()

    def _credentials(self, channel) -> Dict[str, str]:
        return {
            "hotel_id": channel.account_id or "",
            "api_key": channel.api_key or getattr(settings, "BOOKING_COM_API_KEY", ""),
            "api_secret": channel.api_secret
            or getattr(settings, "BOOKING_COM_API_SECRET", ""),
        }

    def _creds_ok(self, creds: Dict[str, str]) -> bool:
        return bool(creds["hotel_id"] and creds["api_key"])

    def _live_enabled(self) -> bool:
        return bool(getattr(settings, "BOOKING_COM_LIVE", False))

    def _prepared_room_types(
        self, channel, date_from: Optional[date], date_to: Optional[date]
    ) -> list:
        mappings = normalize_mapping_config(channel.mapping_config)[
            "room_type_mappings"
        ]
        room_types = []
        for rt_id, remote_id in mappings.items():
            try:
                local_id = int(rt_id)
            except (TypeError, ValueError):
                local_id = rt_id
            nights = _allotment_rows(
                int(local_id) if str(local_id).isdigit() else 0,
                date_from,
                date_to,
            )
            room_types.append(
                {
                    "nephele_room_type_id": rt_id,
                    "booking_com_room_id": remote_id,
                    "date_from": date_from.isoformat() if date_from else None,
                    "date_to": date_to.isoformat() if date_to else None,
                    "nights": nights,
                }
            )
        return room_types

    def _prepared_rate_plans(
        self, channel, date_from: Optional[date], date_to: Optional[date]
    ) -> list:
        cfg = normalize_mapping_config(channel.mapping_config)
        rate_mappings = cfg["rate_plan_mappings"]
        room_mappings = cfg["room_type_mappings"]
        # Prefer pairing each rate plan with mapped room types for ARI prices
        room_type_ids = [int(k) for k in room_mappings if str(k).isdigit()]
        rate_plans = []
        for rp_id, remote_id in rate_mappings.items():
            if not str(rp_id).isdigit():
                continue
            rp_int = int(rp_id)
            prices: List[Dict[str, Any]] = []
            if room_type_ids:
                for rt_id in room_type_ids:
                    prices.extend(
                        _rate_price_rows(rp_int, date_from, date_to, rt_id)
                    )
            else:
                prices = _rate_price_rows(rp_int, date_from, date_to)
            rate_plans.append(
                {
                    "nephele_rate_plan_id": rp_id,
                    "booking_com_rate_id": remote_id,
                    "date_from": date_from.isoformat() if date_from else None,
                    "date_to": date_to.isoformat() if date_to else None,
                    "prices": prices,
                }
            )
        return rate_plans

    @staticmethod
    def _availability_payload(creds, room_types, date_from, date_to) -> Dict[str, Any]:
        """Clear ARI availability JSON for Booking.com Connectivity."""
        return {
            "hotel_id": creds["hotel_id"],
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "rooms": [
                {
                    "room_id": rt.get("booking_com_room_id"),
                    "nephele_room_type_id": rt.get("nephele_room_type_id"),
                    "nights": [
                        {
                            "date": n.get("date"),
                            "rooms_to_sell": n.get("available", n.get("allotment", 0)),
                            "closed": bool(n.get("stop_sell")),
                            "min_stay": n.get("min_stay"),
                            "max_stay": n.get("max_stay"),
                            "cta": n.get("cta"),
                            "ctd": n.get("ctd"),
                        }
                        for n in (rt.get("nights") or [])
                    ],
                }
                for rt in room_types
            ],
        }

    @staticmethod
    def _rates_payload(creds, rate_plans, date_from, date_to) -> Dict[str, Any]:
        """Clear ARI rates JSON for Booking.com Connectivity."""
        return {
            "hotel_id": creds["hotel_id"],
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "rates": [
                {
                    "rate_id": rp.get("booking_com_rate_id"),
                    "nephele_rate_plan_id": rp.get("nephele_rate_plan_id"),
                    "prices": [
                        {
                            "date": p.get("date"),
                            "room_type_id": p.get("room_type_id"),
                            "price": p.get("price"),
                            "currency": p.get("currency") or "EUR",
                        }
                        for p in (rp.get("prices") or [])
                    ],
                }
                for rp in rate_plans
            ],
        }

    def _live_push_availability(
        self, creds: Dict[str, str], room_types: list, date_from, date_to
    ) -> Dict[str, Any]:
        payload = self._availability_payload(creds, room_types, date_from, date_to)
        try:
            url = f"{self.API_BASE}/hotels/{creds['hotel_id']}/availability"
            result = _http_post_json(url, payload, creds)
            if result["status_code"] >= 400:
                return _error_result(
                    self.channel_name,
                    "push_availability",
                    f"Booking.com HTTP {result['status_code']}: {result['text']}",
                    prepared_rooms=room_types,
                    request_payload=payload,
                )
            return _ok_result(
                self.channel_name,
                "push_availability",
                prepared_rooms=room_types,
                rooms_affected=len(room_types),
                request_payload=payload,
                raw=result["body"],
            )
        except Exception as exc:
            return _error_result(
                self.channel_name,
                "push_availability",
                str(exc),
                prepared_rooms=room_types,
                request_payload=payload,
            )

    def _live_push_rates(
        self, creds: Dict[str, str], rate_plans: list, date_from, date_to
    ) -> Dict[str, Any]:
        payload = self._rates_payload(creds, rate_plans, date_from, date_to)
        try:
            url = f"{self.API_BASE}/hotels/{creds['hotel_id']}/rates"
            # Rates use PUT (full replace for date window); availability uses POST.
            result = _http_put_json(url, payload, creds)
            if result["status_code"] >= 400:
                return _error_result(
                    self.channel_name,
                    "push_rates",
                    f"Booking.com HTTP {result['status_code']}: {result['text']}",
                    prepared_rates=rate_plans,
                    request_payload=payload,
                )
            return _ok_result(
                self.channel_name,
                "push_rates",
                prepared_rates=rate_plans,
                rates_affected=len(rate_plans),
                request_payload=payload,
                raw=result["body"],
            )
        except Exception as exc:
            return _error_result(
                self.channel_name,
                "push_rates",
                str(exc),
                prepared_rates=rate_plans,
                request_payload=payload,
            )

    def _live_pull_bookings(self, creds: Dict[str, str]) -> Dict[str, Any]:
        try:
            url = f"{self.API_BASE}/hotels/{creds['hotel_id']}/reservations"
            result = _http_get_json(url, creds)
            if result["status_code"] >= 400:
                return _error_result(
                    self.channel_name,
                    "pull_bookings",
                    f"Booking.com HTTP {result['status_code']}: {result['text']}",
                )
            bookings = _parse_reservations_from_body(result["body"])
            return _ok_result(
                self.channel_name,
                "pull_bookings",
                bookings=bookings,
                count=len(bookings),
                raw=result["body"],
            )
        except Exception as exc:
            return _error_result(self.channel_name, "pull_bookings", str(exc))

    def push_availability(
        self, channel, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        creds = self._credentials(channel)
        if not self._creds_ok(creds):
            return _error_result(
                self.channel_name,
                "push_availability",
                "Missing Booking.com hotel_id/api_key on channel",
            )
        room_types = self._prepared_room_types(channel, date_from, date_to)
        if self._live_enabled():
            return self._live_push_availability(creds, room_types, date_from, date_to)

        result = self.not_implemented("push_availability")
        result["prepared_rooms"] = room_types
        result["api_base"] = self.API_BASE
        logger.warning(
            "Booking.com push_availability not live (set BOOKING_COM_LIVE=True; hotel=%s)",
            creds["hotel_id"],
        )
        return result

    def push_rates(
        self, channel, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        creds = self._credentials(channel)
        rate_plans = self._prepared_rate_plans(channel, date_from, date_to)
        if not self._live_enabled():
            result = self.not_implemented("push_rates")
            result["prepared_rates"] = rate_plans
            result["api_base"] = self.API_BASE
            return result
        if not self._creds_ok(creds):
            return _error_result(
                self.channel_name,
                "push_rates",
                "Missing Booking.com hotel_id/api_key on channel",
                prepared_rates=rate_plans,
            )
        return self._live_push_rates(creds, rate_plans, date_from, date_to)

    def pull_bookings(self, channel) -> Dict[str, Any]:
        creds = self._credentials(channel)
        if not self._live_enabled():
            return self.not_implemented("pull_bookings")
        if not self._creds_ok(creds):
            return _error_result(
                self.channel_name,
                "pull_bookings",
                "Missing Booking.com hotel_id/api_key on channel",
            )
        return self._live_pull_bookings(creds)

    def receive_webhook(self, channel, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._live_enabled():
            result = self.not_implemented("receive_webhook")
            result["received_keys"] = sorted(list(payload.keys())) if payload else []
            return result
        booking = normalize_booking_payload(payload or {})
        if not booking.get("external_id"):
            return _error_result(
                self.channel_name,
                "receive_webhook",
                "Webhook payload missing reservation id",
                received_keys=sorted(list((payload or {}).keys())),
            )
        return _ok_result(
            self.channel_name,
            "receive_webhook",
            booking=booking,
            message="Normalized Booking.com reservation from webhook",
        )

    def map_room_type(self, channel, nephele_room_type_id) -> Optional[str]:
        return super().map_room_type(channel, nephele_room_type_id)

    def map_rate_plan(self, channel, nephele_rate_plan_id) -> Optional[str]:
        return super().map_rate_plan(channel, nephele_rate_plan_id)
