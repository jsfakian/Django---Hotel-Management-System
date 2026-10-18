"""
Live hotel KPIs computed from bookings and payments.

Room revenue is attributed per night: a booking's ``base_price`` (stay
subtotal before VAT / climate fee) divided by its number of nights. Occupancy
counts every sold night, including stays that have already checked out.
"""

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from room.models import Booking, Room

REVENUE_STATUSES = ("confirmed", "checked_in", "checked_out")
PERIOD_DAYS = {"day": 1, "week": 7, "month": 30, "year": 365}
SOURCE_LABELS = dict(Booking.BOOKING_SOURCE_CHOICES)
ZERO = Decimal("0")
YOY_METRICS = (
    ("Revenue (€)", "total_revenue"),
    ("Occupancy %", "occupancy_rate"),
    ("ADR (€)", "adr"),
    ("RevPAR (€)", "revpar"),
    ("Bookings", "bookings"),
)


def period_window(period, today=None):
    """Inclusive (start, end) window of ``period`` ending today."""
    today = today or timezone.localdate()
    days = PERIOD_DAYS.get(period, PERIOD_DAYS["month"])
    return today - timedelta(days=days - 1), today


def daterange(start, end):
    """Inclusive date range."""
    for offset in range((end - start).days + 1):
        yield start + timedelta(days=offset)


def pct(part, whole, digits=1):
    return round(float(part) / float(whole) * 100, digits) if whole else 0.0


def change_pct(current, previous):
    if not previous:
        return None
    return round((float(current) - float(previous)) / float(previous) * 100, 1)


def money(value):
    return round(float(value or 0), 2)


def nightly_room_revenue(booking):
    nights = (booking.check_out_date - booking.check_in_date).days
    if nights <= 0:
        return ZERO
    return (booking.base_price or ZERO) / nights


def room_count(properties):
    """Sellable physical rooms, falling back to the declared total per property."""
    counts = dict(
        Room.objects.filter(property__in=properties)
        .values_list("property_id")
        .annotate(n=Count("id"))
    )
    return sum(counts.get(p.id) or p.total_rooms or 0 for p in properties)


class NightLedger:
    """Sold room-nights (and their revenue) for some properties over a window."""

    def __init__(self, properties, start, end):
        self.properties = list(properties)
        self.start, self.end = start, end
        self.days = (end - start).days + 1
        self.rooms = room_count(self.properties)
        self.bookings = list(
            Booking.objects.filter(
                room__property__in=self.properties,
                status__in=REVENUE_STATUSES,
                check_in_date__lte=end,
                check_out_date__gt=start,
            ).select_related("room", "guest")
        )
        # (date, booking, revenue) for each night inside the window
        self.nights = []
        for booking in self.bookings:
            rate = nightly_room_revenue(booking)
            first = max(booking.check_in_date, start)
            last = min(booking.check_out_date - timedelta(days=1), end)
            for night in daterange(first, last):
                self.nights.append((night, booking, rate))

    def kpis(self, nights=None, rooms=None, days=None):
        nights = self.nights if nights is None else nights
        rooms = self.rooms if rooms is None else rooms
        available = rooms * (self.days if days is None else days)
        revenue = sum((rate for _, _, rate in nights), ZERO)
        sold = len(nights)
        return {
            "total_revenue": money(revenue),
            "occupancy_rate": pct(sold, available),
            "adr": money(revenue / sold) if sold else 0.0,
            "revpar": money(revenue / available) if available else 0.0,
            "rooms_sold": sold,
            "bookings": len({b.id for _, b, _ in nights}),
        }

    def series(self, monthly=False):
        """Per-day (or per-month) revenue, occupancy, ADR and arrivals."""
        key = (lambda d: d.strftime("%Y-%m")) if monthly else (lambda d: d.isoformat())
        buckets = defaultdict(list)
        days_in = defaultdict(int)
        for day in daterange(self.start, self.end):
            days_in[key(day)] += 1
            buckets[key(day)]  # every bucket appears, even without sales
        for night in self.nights:
            buckets[key(night[0])].append(night)
        arrivals = defaultdict(int)
        for booking in self.bookings:
            if self.start <= booking.check_in_date <= self.end:
                arrivals[key(booking.check_in_date)] += 1
        rows = []
        for bucket in sorted(buckets):
            k = self.kpis(buckets[bucket], days=days_in[bucket])
            rows.append(
                {
                    "date": bucket,
                    "revenue": k["total_revenue"],
                    "occupancy": k["occupancy_rate"],
                    "adr": k["adr"],
                    "revpar": k["revpar"],
                    "rooms_sold": k["rooms_sold"],
                    "bookings": arrivals[bucket],
                }
            )
        return rows

    def per_property(self):
        rows = []
        for prop in self.properties:
            nights = [n for n in self.nights if n[1].room.property_id == prop.id]
            k = self.kpis(nights, rooms=room_count([prop]))
            rows.append(
                {
                    "id": prop.id,
                    "name": prop.name,
                    "revenue": k["total_revenue"],
                    "occupancy": k["occupancy_rate"],
                    "adr": k["adr"],
                    "revpar": k["revpar"],
                }
            )
        return sorted(rows, key=lambda r: r["revenue"], reverse=True)

    def by_source(self):
        revenue, bookings = defaultdict(lambda: ZERO), defaultdict(set)
        for _, booking, rate in self.nights:
            source = booking.booking_source or "other"
            revenue[source] += rate
            bookings[source].add(booking.id)
        total = sum(revenue.values(), ZERO)
        rows = [
            {
                "source": s,
                "label": SOURCE_LABELS.get(s, s.title()),
                "revenue": money(r),
                "pct": pct(r, total),
                "bookings": len(bookings[s]),
            }
            for s, r in revenue.items()
        ]
        return sorted(rows, key=lambda r: r["revenue"], reverse=True)


def _properties_payload(properties):
    return [{"id": p.id, "name": p.name} for p in properties]


def _window_payload(period, start, end, properties):
    return {
        "period": period,
        "from_date": start.isoformat(),
        "to_date": end.isoformat(),
        "properties": _properties_payload(properties),
    }


def executive_overview(all_properties, properties, period):
    start, end = period_window(period)
    span = end - start + timedelta(days=1)
    current = NightLedger(properties, start, end)
    previous = NightLedger(properties, start - span, end - span).kpis()
    last_year = NightLedger(
        properties, start - timedelta(days=365), end - timedelta(days=365)
    ).kpis()
    kpis = current.kpis()
    for name in ("total_revenue", "occupancy_rate", "adr", "revpar"):
        trend_key = (
            "revenue_trend_pct"
            if name == "total_revenue"
            else f"{name.split('_')[0]}_trend_pct"
        )
        kpis[trend_key] = change_pct(kpis[name], previous[name])
    return {
        **_window_payload(period, start, end, all_properties),
        "kpis": kpis,
        "revenue_trend": current.series(monthly=period == "year"),
        "top_properties": current.per_property(),
        "year_over_year": [
            {
                "metric": label,
                "this_year": kpis[key],
                "last_year": last_year[key],
                "change_pct": change_pct(kpis[key], last_year[key]),
            }
            for label, key in YOY_METRICS
        ],
    }


def revenue_overview(all_properties, properties, period):
    from payments.models import Payment

    start, end = period_window(period)
    ledger = NightLedger(properties, start, end)
    payments = Payment.objects.filter(
        booking__room__property__in=properties,
        created_at__date__gte=start,
        created_at__date__lte=end,
    )

    def total(qs):
        return money(qs.aggregate(s=Sum("amount"))["s"])

    kpis = ledger.kpis()
    kpis.update(
        {
            "collected": total(payments.filter(status="completed")),
            "outstanding": total(payments.filter(status__in=["pending", "processing"])),
            "refunded": total(payments.filter(status="refunded")),
        }
    )
    by_method = (
        payments.filter(status="completed")
        .values("payment_method__name")
        .annotate(count=Count("id"), amount=Sum("amount"))
        .order_by("-amount")
    )
    return {
        **_window_payload(period, start, end, all_properties),
        "kpis": kpis,
        "revenue_by_source": ledger.by_source(),
        "adr_trend": ledger.series(monthly=period == "year"),
        "payments_by_method": [
            {
                "method": row["payment_method__name"] or "Unknown",
                "count": row["count"],
                "amount": money(row["amount"]),
            }
            for row in by_method
        ],
    }


def _segment(booking):
    if booking.children:
        return "Family"
    adults = booking.adults or booking.number_of_guests or 1
    if adults >= 3:
        return "Group"
    return "Couple" if adults == 2 else "Solo"


def _stay_nights(booking):
    return (booking.check_out_date - booking.check_in_date).days


def _returning_guest_ids(guest_ids, stays, start):
    returning = set(
        Booking.objects.filter(
            guest_id__in=guest_ids, status__in=REVENUE_STATUSES, check_in_date__lt=start
        ).values_list("guest_id", flat=True)
    )
    stay_counts = defaultdict(int)
    for booking in stays:
        stay_counts[booking.guest_id] += 1
    returning |= {guest for guest, count in stay_counts.items() if count > 1}
    return returning


def _avg_or_zero(values, digits=1):
    return round(sum(values) / len(values), digits) if values else 0.0


def _guest_kpis(guest_ids, returning, stays, properties, leads):
    return {
        "total_guests": len(guest_ids),
        "new_guests": len(guest_ids - returning),
        "repeat_guests": len(guest_ids & returning),
        "repeat_rate": pct(len(guest_ids & returning), len(guest_ids)),
        "avg_stay": _avg_or_zero([_stay_nights(b) for b in stays]),
        "avg_lead_time": _avg_or_zero(leads),
        "in_house": Booking.objects.filter(
            room__property__in=properties, status="checked_in"
        ).count(),
    }


def _guest_segment_rows(stays, revenue_by_booking):
    segments = defaultdict(list)
    for booking in stays:
        segments[_segment(booking)].append(booking)
    rows = [
        {
            "segment": name,
            "count": len(items),
            "revenue": money(sum((revenue_by_booking[b.id] for b in items), ZERO)),
            "avg_stay": round(sum(map(_stay_nights, items)) / len(items), 1),
        }
        for name, items in segments.items()
    ]
    return sorted(rows, key=lambda row: row["count"], reverse=True)


def _nationality_rows(stays, guest_ids):
    countries = defaultdict(set)
    for booking in stays:
        country = booking.guest.country or booking.guest.nationality or "Unknown"
        countries[country].add(booking.guest_id)
    rows = [
        {"country": country, "guests": len(guests), "pct": pct(len(guests), len(guest_ids))}
        for country, guests in countries.items()
    ]
    return sorted(rows, key=lambda row: row["guests"], reverse=True)


def guest_overview(all_properties, properties, period):
    start, end = period_window(period)
    ledger = NightLedger(properties, start, end)
    stays = [b for b in ledger.bookings if b.guest_id]
    guest_ids = {b.guest_id for b in stays}
    returning = _returning_guest_ids(guest_ids, stays, start)
    leads = [
        (b.check_in_date - b.date_of_reservation).days
        for b in stays
        if b.date_of_reservation
    ]
    revenue_by_booking = defaultdict(lambda: ZERO)
    for _, booking, rate in ledger.nights:
        revenue_by_booking[booking.id] += rate
    return {
        **_window_payload(period, start, end, all_properties),
        "kpis": _guest_kpis(guest_ids, returning, stays, properties, leads),
        "guest_segments": _guest_segment_rows(stays, revenue_by_booking),
        "nationalities": _nationality_rows(stays, guest_ids),
    }


def _movement(booking, multi):
    guest_name = "Guest"
    if booking.guest:
        guest_name = f"{booking.guest.first_name} {booking.guest.last_name}".strip()
    room_number = booking.room.room_number if booking.room else "—"
    property_name = ""
    if booking.room and multi:
        property_name = booking.room.property.name
    return {
        "booking_id": booking.id,
        "guest_name": guest_name,
        "room_number": room_number,
        "property_name": property_name,
        "status": booking.status,
    }


def _room_status_payload(rooms):
    counts = defaultdict(int)
    for room in rooms:
        key = "blocked" if room.status == "reserved" else room.status
        counts[key] += 1
    return {
        "occupied": counts["occupied"],
        "available": counts["available"],
        "cleaning": counts["cleaning"],
        "maintenance": counts["maintenance"],
        "blocked": counts["blocked"],
        "total": len(rooms),
    }


def _staff_task_row(task):
    employee_name = "—"
    if task.employee and task.employee.user:
        employee_name = (
            task.employee.user.get_full_name() or task.employee.user.username
        )
    due_time = ""
    if task.end_time:
        due_time = timezone.localtime(task.end_time).strftime("%H:%M")
    return {
        "id": task.id,
        "title": task.title,
        "employee_name": employee_name,
        "priority": task.priority,
        "status": task.status,
        "due_time": due_time,
        "property_name": task.property.name if task.property else "",
    }


def operational_overview(all_properties, properties):
    from accounts.models import Task

    today = timezone.localdate()
    multi = len(properties) > 1
    rooms = list(
        Room.objects.filter(property__in=properties)
        .select_related("property")
        .order_by("property__name", "room_number")
    )
    movements = (
        Booking.objects.filter(room__property__in=properties)
        .exclude(status__in=["cancelled", "no_show", "held"])
        .select_related("guest", "room__property")
        .order_by("room__room_number")
    )
    tasks = (
        Task.objects.filter(property__in=properties)
        .filter(Q(start_time__date=today) | Q(status__in=["pending", "in_progress"]))
        .select_related("employee__user", "property")
        .order_by("start_time")[:50]
    )
    return {
        "date": today.isoformat(),
        "properties": _properties_payload(all_properties),
        "room_status": _room_status_payload(rooms),
        "checkins_today": [
            _movement(b, multi) for b in movements.filter(check_in_date=today)
        ],
        "checkouts_today": [
            _movement(b, multi) for b in movements.filter(check_out_date=today)
        ],
        "staff_tasks": [_staff_task_row(t) for t in tasks],
        "rooms": [
            {
                "id": r.id,
                "room_number": r.room_number,
                "status": r.status,
                "property_name": r.property.name,
            }
            for r in rooms
        ],
    }
