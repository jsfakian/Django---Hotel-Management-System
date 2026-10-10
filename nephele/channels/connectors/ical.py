# nephele/channels/connectors/ical.py
"""iCal export / import connector (stdlib VEVENT parser; icalendar optional)."""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from django.db import transaction
from django.utils import timezone

from .base import ChannelConnector

logger = logging.getLogger(__name__)

try:
    from icalendar import Calendar as ICalendar  # type: ignore

    HAS_ICALENDAR = True
except ImportError:  # pragma: no cover
    ICalendar = None
    HAS_ICALENDAR = False


def _parse_ical_date(value: str) -> Optional[date]:
    value = (value or "").strip()
    if not value:
        return None
    # VALUE=DATE:20260315 or 20260315T120000Z
    value = value.split(":")[-1] if ":" in value and "T" not in value[:10] else value
    value = re.sub(r"^.*:", "", value) if value.startswith("TZID") else value
    m = re.match(r"(\d{8})(?:T(\d{6})Z?)?", value)
    if not m:
        return None
    d = datetime.strptime(m.group(1), "%Y%m%d").date()
    return d


def parse_vevents(ical_text: str) -> List[Dict[str, Any]]:
    """Parse VEVENT blocks using icalendar if present, else a minimal stdlib parser."""
    if HAS_ICALENDAR:
        return _parse_with_icalendar(ical_text)
    return _parse_with_stdlib(ical_text)


def _parse_with_icalendar(ical_text: str) -> List[Dict[str, Any]]:
    cal = ICalendar.from_ical(ical_text)
    events = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        dtstart = component.get("dtstart")
        dtend = component.get("dtend")
        uid = str(component.get("uid") or "")
        summary = str(component.get("summary") or "")
        start = dtstart.dt if dtstart else None
        end = dtend.dt if dtend else None
        if hasattr(start, "date"):
            start = start.date()
        if hasattr(end, "date"):
            end = end.date()
        events.append(
            {
                "uid": uid,
                "summary": summary,
                "check_in": start,
                "check_out": end,
            }
        )
    return events


def _unfold_ical(text: str) -> str:
    return re.sub(r"\r?\n[ \t]", "", text)


def _parse_with_stdlib(ical_text: str) -> List[Dict[str, Any]]:
    text = _unfold_ical(ical_text or "")
    blocks = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, flags=re.S | re.I)
    events = []
    for block in blocks:
        fields: Dict[str, str] = {}
        for line in block.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.split(";")[0].upper()
            fields[key] = val
        events.append(
            {
                "uid": fields.get("UID", ""),
                "summary": fields.get("SUMMARY", ""),
                "check_in": _parse_ical_date(fields.get("DTSTART", "")),
                "check_out": _parse_ical_date(fields.get("DTEND", "")),
            }
        )
    return events


def _ical_summary(booking) -> str:
    """Privacy-safe SUMMARY — room type or 'Reserved', never guest names."""
    room_type = getattr(booking, "room_type", None)
    if room_type is not None and getattr(room_type, "name", None):
        return str(room_type.name)
    return "Reserved"


def ensure_ical_token(channel) -> str:
    """Return mapping_config.ical_token, generating and persisting one if missing."""
    import secrets

    cfg = dict(channel.mapping_config or {})
    token = cfg.get("ical_token") or ""
    if token:
        return str(token)
    token = secrets.token_urlsafe(24)
    cfg["ical_token"] = token
    channel.mapping_config = cfg
    channel.save(update_fields=["mapping_config", "updated_at"])
    return token


def build_ical_feed(channel, bookings) -> str:
    """Build a VCALENDAR string for the property's bookings."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Nephele HMS//iCal//EN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:Nephele {channel.property.name}",
    ]
    for booking in bookings:
        uid = f"nephele-booking-{booking.id}@nephele"
        summary = _ical_summary(booking)
        check_in = booking.check_in_date.strftime("%Y%m%d")
        check_out = booking.check_out_date.strftime("%Y%m%d")
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{timezone.now().strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART;VALUE=DATE:{check_in}",
                f"DTEND;VALUE=DATE:{check_out}",
                f"SUMMARY:{summary}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def _ical_event_stay(event):
    uid = event.get("uid") or ""
    check_in = event.get("check_in")
    check_out = event.get("check_out")
    if not uid or not check_in or not check_out:
        return None
    if check_out <= check_in:
        check_out = check_in + timedelta(days=1)
    return uid, check_in, check_out


def _get_or_create_ical_guest(uid):
    import secrets

    from django.contrib.auth.models import User

    from accounts.models import Guest

    email = f"ical+{uid[:40]}@nephele.local"
    existing = Guest.objects.filter(email__iexact=email).first()
    if existing and (existing.preferences or {}).get("channel_external_id") == uid:
        return existing
    user = User(username=f"ical_{secrets.token_hex(10)}", email=email)
    user.set_unusable_password()
    user.save()
    if existing:
        email = f"ical+{secrets.token_hex(8)}@nephele.local"
    return Guest.objects.create(
        user=user,
        email=email,
        first_name="iCal",
        last_name="Guest",
        preferences={"channel_external_id": uid},
    )


def _import_ical_event(channel, event, room) -> bool:
    from channels.models import ChannelBooking
    from room.models import Booking

    stay = _ical_event_stay(event)
    if stay is None:
        return False
    uid, check_in, check_out = stay
    if ChannelBooking.objects.filter(
        channel=channel, channel_booking_id=uid
    ).exists():
        return False
    with transaction.atomic():
        guest = _get_or_create_ical_guest(uid)
        price = room.base_price if room else 0
        booking = Booking.objects.create(
            room=room,
            guest=guest,
            check_in_date=check_in,
            check_out_date=check_out,
            number_of_guests=1,
            adults=1,
            base_price=price,
            actual_price=price,
            status="confirmed",
            booking_source="ical",
            notes=f"Imported from iCal UID={uid}",
        )
        ChannelBooking.objects.create(
            channel=channel,
            channel_booking_id=uid,
            nephele_booking=booking,
            sync_status="synced",
            channel_data={
                "uid": uid,
                "check_in": str(check_in),
                "check_out": str(check_out),
            },
        )
    return True


class ICalConnector(ChannelConnector):
    channel_name = "ical"

    def push_availability(
        self, channel, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        # iCal is pull-oriented; export feed is the "push"
        feed = self.export_feed(channel, date_from=date_from, date_to=date_to)
        return {
            "status": "ok",
            "channel": self.channel_name,
            "operation": "push_availability",
            "vevents": feed.count("BEGIN:VEVENT"),
            "feed_bytes": len(feed.encode("utf-8")),
        }

    def push_rates(
        self, channel, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        return {
            "status": "ok",
            "channel": self.channel_name,
            "operation": "push_rates",
            "message": "iCal does not carry rates; skipped",
        }

    def pull_bookings(self, channel) -> Dict[str, Any]:
        url = (channel.mapping_config or {}).get("ical_url") or channel.account_id
        if not url or not str(url).startswith(("http://", "https://")):
            return {
                "status": "error",
                "channel": self.channel_name,
                "operation": "pull_bookings",
                "message": "No ical_url configured (set mapping_config.ical_url or account_id)",
            }
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            return {
                "status": "error",
                "channel": self.channel_name,
                "operation": "pull_bookings",
                "message": str(exc),
            }
        imported = self.import_feed(channel, resp.text)
        return {
            "status": "ok",
            "channel": self.channel_name,
            "operation": "pull_bookings",
            "imported": imported,
        }

    def receive_webhook(self, channel, payload: Dict[str, Any]) -> Dict[str, Any]:
        ical_text = payload.get("ical") or payload.get("body") or ""
        if not ical_text:
            return {"status": "error", "message": "Missing ical payload"}
        imported = self.import_feed(channel, ical_text)
        return {"status": "ok", "imported": imported}

    def export_feed(
        self,
        channel,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> str:
        from room.models import Booking

        from django.db.models import Q

        qs = Booking.objects.filter(
            Q(room__property=channel.property) | Q(room_type__property=channel.property),
            status__in=["held", "pending", "confirmed", "checked_in"],
        ).select_related("guest", "room_type")
        if date_from:
            qs = qs.filter(check_out_date__gt=date_from)
        if date_to:
            qs = qs.filter(check_in_date__lt=date_to)
        return build_ical_feed(channel, qs)

    def import_feed(self, channel, ical_text: str) -> int:
        from room.models import Room

        events = parse_vevents(ical_text)
        room = Room.objects.filter(property=channel.property).order_by("id").first()
        imported = 0
        for event in events:
            if _import_ical_event(channel, event, room):
                imported += 1
        return imported

    def get_feed_url(self, channel) -> str:
        cfg = channel.mapping_config or {}
        return cfg.get("ical_url") or channel.account_id or ""

    def set_feed_url(self, channel, url: str) -> Dict[str, Any]:
        parsed = urlparse(url)
        if url and parsed.scheme not in ("http", "https"):
            raise ValueError("ical_url must be an http(s) URL")
        cfg = dict(channel.mapping_config or {})
        cfg["ical_url"] = url
        channel.mapping_config = cfg
        if not channel.account_id:
            channel.account_id = url[:255]
        channel.save(update_fields=["mapping_config", "account_id", "updated_at"])
        return {"ical_url": url}
