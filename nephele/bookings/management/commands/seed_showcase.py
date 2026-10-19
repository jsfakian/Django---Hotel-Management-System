"""
Seed a realistic, self-consistent showcase dataset (safe to run on prod).

Everything created is tagged so it can be removed again without touching real
data:  properties listed in PROPERTIES, users prefixed ``demo_``, guests with
``@demo.nephele.example`` emails, travel agencies listed in AGENCIES.

Dates are relative to today, so re-running with ``--reset`` keeps the
dashboards (arrivals, departures, in-house, forecasts) looking live.

Role-user passwords come from ``--password`` or the DEMO_PASSWORD env var.

    python manage.py seed_showcase --reset
"""

import os
import random
import secrets
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Employee, Guest, Task, TravelAgentProfile
from bookings.models import CompetitorPrice, PricingHistory
from channels.models import Channel, ChannelBooking
from contracts.models import Contract
from hotel.models import Announcement, Event, FoodMenu, Storage
from inventory.booking_engine import compute_taxes
from inventory.models import (
    RatePlan, RatePlanPrice, RoomType, RoomTypeAvailability,
)
from inventory.services import recalculate_room_availability
from payments.models import Invoice, Payment, PaymentMethod, RefundRequest
from properties.models import (
    Property, PropertyAmenity, PropertyPolicy, TravelAgency,
)
from room.models import Booking, Room, RoomService

GUEST_DOMAIN = "demo.nephele.example"
TWO = Decimal("0.01")

PROPERTIES = [
    {
        "name": "Acropolis View Hotel",
        "location": "Plaka, Athens",
        "address": "18 Dionysiou Areopagitou",
        "city": "Athens",
        "postal_code": "11742",
        "star_rating": 5,
        "phone_number": "+30 210 000 1001",
        "email": "stay@acropolisview.demo.nephele.example",
        "price_factor": Decimal("1.00"),
        # (code, name, legacy room_type, capacity, beds, base price, count)
        "types": [
            ("STD", "Classic Double", "double", 2, 1, 140, 10),
            ("SUP", "Superior Acropolis View", "deluxe", 2, 1, 195, 8),
            ("FAM", "Family Room", "luxury", 4, 2, 230, 4),
            ("STE", "Parthenon Suite", "suite", 3, 1, 380, 2),
        ],
        "amenities": [
            "wifi",
            "restaurant",
            "bar",
            "gym",
            "concierge",
            "room_service",
            "elevator",
            "ac",
        ],
    },
    {
        "name": "Santorini Caldera Suites",
        "location": "Oia, Santorini",
        "address": "Nomikou Street 7",
        "city": "Oia",
        "postal_code": "84702",
        "star_rating": 5,
        "phone_number": "+30 22860 00102",
        "email": "hello@calderasuites.demo.nephele.example",
        "price_factor": Decimal("1.45"),
        "types": [
            ("CAV", "Cave Junior Suite", "deluxe", 2, 1, 260, 6),
            ("PLS", "Plunge Pool Suite", "suite", 2, 1, 420, 6),
            ("VIL", "Caldera Villa", "luxury", 4, 2, 690, 2),
        ],
        "amenities": ["wifi", "pool", "spa", "bar", "concierge", "room_service", "ac"],
    },
    {
        "name": "Chania Harbour Boutique",
        "location": "Old Venetian Harbour, Chania",
        "address": "Akti Koundourioti 33",
        "city": "Chania",
        "postal_code": "73131",
        "star_rating": 4,
        "phone_number": "+30 28210 00103",
        "email": "info@chaniaharbour.demo.nephele.example",
        "price_factor": Decimal("0.85"),
        "types": [
            ("ECO", "Cosy Single", "economic", 1, 1, 85, 4),
            ("STD", "Harbour Double", "double", 2, 1, 120, 8),
            ("FAM", "Family Loft", "luxury", 4, 2, 175, 3),
        ],
        "amenities": ["wifi", "bar", "parking", "laundry", "ac"],
    },
]

AGENCIES = [
    ("Aegean Dream Tours", "Eleni Papadaki", "Athens", "Greece", Decimal("12.00")),
    ("Nordic Sun Travel", "Lars Johansson", "Stockholm", "Sweden", Decimal("15.00")),
    ("Bella Vacanze", "Giulia Romano", "Milan", "Italy", Decimal("10.00")),
    ("Atlantic Getaways", "Michael Brooks", "Boston", "USA", Decimal("14.00")),
]

GUEST_POOL = {
    "Greece": (
        ["Giorgos", "Maria", "Nikos", "Eleni", "Dimitris", "Katerina"],
        ["Papadopoulos", "Georgiou", "Nikolaou", "Ioannou", "Vlachou"],
        "GR",
    ),
    "Germany": (
        ["Lukas", "Anna", "Felix", "Lena", "Jonas", "Sophie"],
        ["Müller", "Schmidt", "Weber", "Fischer", "Wagner"],
        "DE",
    ),
    "United Kingdom": (
        ["Oliver", "Emily", "Harry", "Charlotte", "Jack", "Amelia"],
        ["Smith", "Jones", "Taylor", "Brown", "Wilson"],
        "GB",
    ),
    "France": (
        ["Louis", "Camille", "Hugo", "Chloé", "Lucas", "Manon"],
        ["Martin", "Bernard", "Dubois", "Moreau", "Laurent"],
        "FR",
    ),
    "Italy": (
        ["Marco", "Giulia", "Luca", "Francesca", "Matteo"],
        ["Rossi", "Russo", "Ferrari", "Esposito", "Bianchi"],
        "IT",
    ),
    "USA": (
        ["James", "Olivia", "Ethan", "Ava", "Noah", "Mia"],
        ["Johnson", "Miller", "Davis", "Garcia", "Clark"],
        "US",
    ),
    "Netherlands": (
        ["Daan", "Emma", "Sem", "Julia"],
        ["de Jong", "Jansen", "de Vries", "Bakker"],
        "NL",
    ),
    "Sweden": (
        ["Erik", "Elsa", "Oscar", "Maja"],
        ["Andersson", "Karlsson", "Nilsson", "Larsson"],
        "SE",
    ),
    "Israel": (
        ["Noam", "Tamar", "Ariel", "Yael"],
        ["Cohen", "Levi", "Mizrahi", "Peretz"],
        "IL",
    ),
    "Australia": (
        ["Liam", "Isla", "Cooper", "Zoe"],
        ["Walker", "Harris", "King", "Wright"],
        "AU",
    ),
}

SOURCES = [
    ("booking_com", 34),
    ("direct_website", 18),
    ("booking_engine", 10),
    ("expedia", 14),
    ("airbnb", 6),
    ("travel_agency", 10),
    ("phone", 5),
    ("trivago", 3),
]

SPECIAL_REQUESTS = [
    "",
    "",
    "",
    "",
    "Late check-in around 23:00",
    "High floor please",
    "Celebrating anniversary",
    "Baby cot required",
    "Gluten-free breakfast",
    "Airport transfer needed",
    "Quiet room away from lift",
    "Early check-in if possible",
    "Twin beds instead of double",
]

COMPETITORS = {
    "Athens": ["Grande Bretagne", "Electra Palace", "Herodion"],
    "Oia": ["Canaves Oia", "Katikies", "Andronis"],
    "Chania": ["Casa Delfino", "Ambassadors Residence", "Domus Renier"],
}

ROLE_USERS = [
    # username, group, first, last, employee position, department, property index
    ("demo_manager", "manager", "Sofia", "Karras", "General Manager", "Management", 0),
    (
        "demo_receptionist",
        "receptionist",
        "Alexis",
        "Mavros",
        "Front Desk Agent",
        "Front Office",
        0,
    ),
    ("demo_staff", "staff", "Irini", "Lambrou", "Room Attendant", "Housekeeping", 0),
    (
        "demo_maintenance",
        "staff",
        "Kostas",
        "Petridis",
        "Maintenance Technician",
        "Engineering",
        0,
    ),
    (
        "demo_santorini_mgr",
        "manager",
        "Anna",
        "Sigala",
        "Resident Manager",
        "Management",
        1,
    ),
    (
        "demo_chania_desk",
        "receptionist",
        "Manos",
        "Daskalakis",
        "Night Auditor",
        "Front Office",
        2,
    ),
    ("demo_guest", "guest", "Emma", "Becker", None, None, None),
    ("demo_agent", "travel_agent", "Eleni", "Papadaki", None, None, None),
]


def money(value):
    return Decimal(value).quantize(TWO)


def season_factor(d):
    """Greek seasonality: peak Jul-Aug, high Jun/Sep, shoulder May/Oct, low winter."""
    return {
        1: 0.70,
        2: 0.70,
        3: 0.78,
        4: 0.92,
        5: 1.00,
        6: 1.18,
        7: 1.38,
        8: 1.42,
        9: 1.20,
        10: 0.98,
        11: 0.75,
        12: 0.85,
    }[d.month]


def season_label(d):
    f = season_factor(d)
    return (
        "peak" if f >= 1.35 else "high" if f >= 1.1 else "medium" if f >= 0.9 else "low"
    )


def nightly_rate(base, d):
    weekend = 1.12 if d.weekday() in (4, 5) else 1.0
    return money(Decimal(base) * Decimal(str(season_factor(d) * weekend)))


class Command(BaseCommand):
    help = "Seed a realistic showcase dataset (3 Greek hotels, ~5 months of activity)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true", help="Delete previous showcase data first"
        )
        parser.add_argument(
            "--only-clear", action="store_true", help="Delete showcase data and exit"
        )
        parser.add_argument(
            "--password", help="Password for demo_* users (default: $DEMO_PASSWORD)"
        )
        parser.add_argument("--days-back", type=int, default=90)
        parser.add_argument("--days-forward", type=int, default=75)
        parser.add_argument("--seed", type=int, default=2026)
        parser.add_argument("--skip-analytics", action="store_true")

    def handle(self, *args, **opts):
        self.rng = random.Random(opts["seed"])
        self.today = timezone.localdate()

        if opts["reset"] or opts["only_clear"]:
            self._clear()
            if opts["only_clear"]:
                return

        if Property.objects.filter(name__in=[p["name"] for p in PROPERTIES]).exists():
            raise CommandError(
                "Showcase data already present. Re-run with --reset to rebuild it."
            )

        password = opts["password"] or os.environ.get("DEMO_PASSWORD")
        if not password:
            raise CommandError(
                "Provide --password or set DEMO_PASSWORD for the demo_* users."
            )

        self.start = self.today - timedelta(days=opts["days_back"])
        self.end = self.today + timedelta(days=opts["days_forward"])

        with transaction.atomic():
            self._payment_methods()
            self._properties()
            self._agencies_and_contracts()
            self._users(password)
            self._guests()
            self._bookings()
            self._sync_inventory()
            self._room_statuses()
            self._payments_and_invoices()
            self._channels()
            self._pricing()
            self._operations()
            self._guest_stats()

        if not opts["skip_analytics"]:
            self._analytics(opts["days_back"])

        self._report()

    # ── clear ──────────────────────────────────────────────────────────────
    def _clear(self):
        names = [p["name"] for p in PROPERTIES]
        props = Property.objects.filter(name__in=names)
        guests = Guest.objects.filter(email__endswith=f"@{GUEST_DOMAIN}")
        with transaction.atomic():
            bookings = Booking.objects.filter(
                room__property__in=props
            ) | Booking.objects.filter(guest__in=guests)
            Invoice.objects.filter(booking__in=bookings).delete()
            Invoice.objects.filter(guest__in=guests).delete()
            RefundRequest.objects.filter(guest__in=guests).delete()
            Payment.objects.filter(guest__in=guests).delete()
            ChannelBooking.objects.filter(nephele_booking__in=bookings).delete()
            Task.objects.filter(property__in=props).delete()
            bookings.delete()
            Event.objects.filter(explanation__startswith="[demo]").delete()
            Announcement.objects.filter(content__startswith="[demo]").delete()
            FoodMenu.objects.filter(menuItems__startswith="[demo]").delete()
            Storage.objects.filter(itemName__startswith="[demo] ").delete()
            Employee.objects.filter(user__username__startswith="demo_").delete()
            props.delete()  # cascades rooms, room types, rate plans, inventory, analytics, channels
            TravelAgency.objects.filter(name__in=[a[0] for a in AGENCIES]).delete()
            guests.delete()
            User.objects.filter(username__startswith="demo_").delete()
        self.stdout.write(self.style.WARNING("Showcase data cleared."))

    # ── reference data ─────────────────────────────────────────────────────
    def _payment_methods(self):
        for name, ptype in [
            ("Credit Card", "card"),
            ("Bank Transfer", "bank_transfer"),
            ("Cash", "cash"),
            ("Viva Wallet", "wallet"),
        ]:
            PaymentMethod.objects.get_or_create(
                name=name, defaults={"payment_type": ptype, "is_active": True}
            )
        self.methods = {m.name: m for m in PaymentMethod.objects.filter(is_active=True)}

    def _create_property(self, idx, spec):
        room_count = sum(t[6] for t in spec["types"])
        prop = Property.objects.create(
            name=spec["name"],
            location=spec["location"],
            address=spec["address"],
            city=spec["city"],
            postal_code=spec["postal_code"],
            country="Greece",
            phone_number=spec["phone_number"],
            email=spec["email"],
            website=f"https://{spec['email'].split('@')[1]}",
            total_rooms=room_count,
            star_rating=spec["star_rating"],
            is_active=True,
            mhte_number=f"1167K0{idx + 1}3K0{idx + 4}21{idx}00",
            tax_id=f"80012345{idx}",
        )
        prop.price_factor = spec["price_factor"]
        for amenity in spec["amenities"]:
            PropertyAmenity.objects.create(property=prop, amenity_type=amenity)
        pet_policy = (
            "Small pets on request (€25/night)." if idx == 2 else "No pets allowed."
        )
        PropertyPolicy.objects.create(
            property=prop,
            check_in_time=time(15),
            check_out_time=time(11),
            cancellation_policy="Free cancellation up to 7 days before arrival; first night charged afterwards.",
            pet_policy=pet_policy,
            smoking_policy="Non-smoking property.",
            children_policy="Children of all ages welcome; cots free.",
        )
        return prop

    def _create_rate_plans(self, prop):
        plans = [
            RatePlan.objects.create(
                property=prop,
                code="BAR",
                name="Flexible – Breakfast included",
                meal_plan="BB",
                is_refundable=True,
                cancellation_policy="Free cancellation until 7 days before arrival.",
            ),
            RatePlan.objects.create(
                property=prop,
                code="NRF",
                name="Non-refundable – Room only",
                meal_plan="RO",
                is_refundable=False,
                cancellation_policy="Non-refundable.",
            ),
            RatePlan.objects.create(
                property=prop,
                code="HB",
                name="Half board",
                meal_plan="HB",
                is_refundable=True,
                cancellation_policy="Free cancellation until 3 days before arrival.",
            ),
        ]
        self.rate_plans[prop.id] = plans
        return plans

    def _create_rooms_for_type(self, prop, plans, idx, type_spec, floor_counter):
        code, name, legacy, cap, beds, base, count = type_spec
        amenities = ["wifi", "ac", "minibar", "safe"] + (["sea_view"] if idx > 0 else [])
        rt = RoomType.objects.create(
            property=prop,
            code=code,
            name=name,
            capacity=cap,
            max_occupancy=cap,
            base_occupancy=min(2, cap),
            base_price=money(base),
            description=f"{name} at {prop.name}",
            amenities=amenities,
        )
        self.room_types[rt.id] = rt
        for plan in plans:
            plan.room_types.add(rt)
        floor = 1 + len(floor_counter) % 4
        for _ in range(count):
            floor_counter[floor] = floor_counter.get(floor, 0) + 1
            room = Room.objects.create(
                property=prop,
                room_number=f"{floor}{floor_counter[floor]:02d}",
                floor=floor,
                room_type=legacy,
                room_type_fk=rt,
                capacity=cap,
                number_of_beds=beds,
                base_price=money(base),
                current_price=nightly_rate(base, self.today),
                status="available",
                amenities=rt.amenities,
            )
            room.rt = rt
            self.rooms.append(room)
            if floor_counter[floor] >= 8:
                floor += 1

    def _occupancy_price_map(self, price, max_occupancy):
        by_occ = {}
        for occupancy in range(1, max_occupancy + 1):
            factor = (
                Decimal("0.85")
                if occupancy == 1
                else 1 + Decimal("0.18") * max(0, occupancy - 2)
            )
            by_occ[str(occupancy)] = str(money(price * factor))
        return by_occ

    def _seed_rate_plan_prices(self, prop, plans):
        plan_factor = {
            "BAR": Decimal("1"),
            "NRF": Decimal("0.88"),
            "HB": Decimal("1.22"),
        }
        prices = []
        room_types = [t for t in self.room_types.values() if t.property_id == prop.id]
        for rt in room_types:
            for offset in range((self.end - self.today).days + 60):
                d = self.today + timedelta(days=offset)
                bar = nightly_rate(rt.base_price, d)
                for plan in plans:
                    p = bar * plan_factor[plan.code]
                    by_occ = self._occupancy_price_map(p, rt.max_occupancy)
                    prices.append(
                        RatePlanPrice(
                            rate_plan=plan,
                            room_type=rt,
                            date=d,
                            price_1=Decimal(by_occ["1"]),
                            price_2=Decimal(by_occ.get("2", by_occ["1"])),
                            price_by_occupancy=by_occ,
                        )
                    )
        RatePlanPrice.objects.bulk_create(prices, batch_size=2000)

    def _properties(self):
        self.props, self.rooms, self.room_types, self.rate_plans = [], [], {}, {}
        for idx, spec in enumerate(PROPERTIES):
            prop = self._create_property(idx, spec)
            self.props.append(prop)
            plans = self._create_rate_plans(prop)
            floor_counter = {}
            for type_spec in spec["types"]:
                self._create_rooms_for_type(prop, plans, idx, type_spec, floor_counter)
            self._seed_rate_plan_prices(prop, plans)

    def _agencies_and_contracts(self):
        self.agencies = []
        for name, contact, city, country, commission in AGENCIES:
            slug = name.lower().replace(" ", "")
            self.agencies.append(
                TravelAgency.objects.create(
                    name=name,
                    contact_name=contact,
                    email=f"partners@{slug}.{GUEST_DOMAIN}",
                    phone="+30 210 555 0000",
                    website=f"https://{slug}.{GUEST_DOMAIN}",
                    address="1 Partner Way",
                    city=city,
                    country=country,
                    commission_percentage=commission,
                    status="active",
                    description=f"Leisure tour operator based in {city}.",
                )
            )
        statuses = ["active", "active", "signed_property", "pending", "active", "draft"]
        i = 0
        for prop in self.props:
            for agency in self.rng.sample(self.agencies, 2):
                status = statuses[i % len(statuses)]
                i += 1
                signed = timezone.now() - timedelta(days=self.rng.randint(20, 200))
                Contract.objects.create(
                    property=prop,
                    travel_agency=agency,
                    contract_type=self.rng.choice(
                        ["allotment", "commission", "guarantee"]
                    ),
                    allocation_percentage=Decimal("15.00"),
                    allocated_rooms=max(2, prop.total_rooms // 6),
                    commission_percentage=agency.commission_percentage,
                    payment_terms="Net 30 days after guest departure.",
                    cancellation_policy="Release 14 days prior to arrival without penalty.",
                    start_date=date(self.today.year, 1, 1),
                    end_date=date(self.today.year + 1, 12, 31),
                    contract_text=f"Allotment agreement between {prop.name} and {agency.name} for seasons {self.today.year}-{self.today.year + 1}.",
                    status=status,
                    property_manager_signed_at=(
                        signed if status in ("active", "signed_property") else None
                    ),
                    travel_agency_signed_at=(
                        signed + timedelta(days=3) if status == "active" else None
                    ),
                )

    def _users(self, password):
        self.users = {}
        for username, group, first, last, position, dept, prop_idx in ROLE_USERS:
            user = User.objects.create_user(
                username=username,
                email=f"{username}@{GUEST_DOMAIN}",
                password=password,
                first_name=first,
                last_name=last,
            )
            user.groups.set([Group.objects.get_or_create(name=group)[0]])
            self.users[username] = user
            if position:
                Employee.objects.create(
                    user=user,
                    phone_number="+30 690 000 0000",
                    salary=money(self.rng.randint(1100, 3200)),
                    position=position,
                    department=dept,
                    hire_date=self.today - timedelta(days=self.rng.randint(120, 2000)),
                    status="active",
                    property=self.props[prop_idx],
                )
        self.props[0].manager = self.users["demo_manager"]
        self.props[1].manager = self.users["demo_santorini_mgr"]
        self.props[2].manager = self.users["demo_manager"]
        for p in self.props:
            p.save(update_fields=["manager"])
        TravelAgentProfile.objects.create(
            user=self.users["demo_agent"],
            travel_agency=self.agencies[0],
            position="Contracting Manager",
        )

    def _guests(self):
        self.guests = []
        used = set()
        countries = list(GUEST_POOL)
        weights = [22, 16, 14, 10, 9, 10, 6, 5, 4, 4]
        while len(self.guests) < 160:
            country = self.rng.choices(countries, weights)[0]
            firsts, lasts, iso = GUEST_POOL[country]
            first, last = self.rng.choice(firsts), self.rng.choice(lasts)
            key = (
                f"{first}.{last}".lower()
                .replace(" ", "")
                .replace("é", "e")
                .replace("ü", "u")
            )
            n = 1
            while f"{key}{n}" in used:
                n += 1
            used.add(f"{key}{n}")
            self.guests.append(
                Guest.objects.create(
                    email=f"{key}{n}@{GUEST_DOMAIN}",
                    first_name=first,
                    last_name=last,
                    phone_number=f"+{self.rng.randint(30, 49)} {self.rng.randint(600, 699)} {self.rng.randint(100000, 999999)}",
                    city="",
                    country=country,
                    nationality=iso,
                    document_type="passport" if iso != "GR" else "id_card",
                    document_number=f"{iso}{self.rng.randint(1000000, 9999999)}",
                    birth_date=date(
                        self.rng.randint(1955, 2002),
                        self.rng.randint(1, 12),
                        self.rng.randint(1, 28),
                    ),
                    preferences={
                        "pillow": self.rng.choice(["soft", "firm"]),
                        "floor": self.rng.choice(["high", "low", "any"]),
                    },
                )
            )
        demo = self.users["demo_guest"]
        self.demo_guest = Guest.objects.create(
            user=demo,
            email=demo.email,
            first_name=demo.first_name,
            last_name=demo.last_name,
            country="Germany",
            nationality="DE",
            phone_number="+49 151 0000000",
        )
        # A handful of loyal repeat guests make guest analytics more interesting
        self.repeaters = self.rng.sample(self.guests, 18)

    # ── bookings ───────────────────────────────────────────────────────────
    def _target_occupancy(self, d):
        """Historic occupancy follows seasonality; future follows a pickup curve."""
        base = min(0.95, 0.55 + 0.30 * (season_factor(d) - 0.7) / 0.72)
        if d >= self.today:
            ahead = (d - self.today).days
            base *= max(0.25, 1 - ahead / 90)
        return base

    def _pick_guest(self):
        r = self.rng.random()
        if r < 0.22:
            return self.rng.choice(self.repeaters)
        return self.rng.choice(self.guests)

    def _seed_room_stay_rows(self, sources, weights):
        rows = []
        for room in self.rooms:
            prop = next(p for p in self.props if p.id == room.property_id)
            d = self.start - timedelta(days=self.rng.randint(0, 4))
            while d < self.end:
                if self.rng.random() > self._target_occupancy(d):
                    d += timedelta(days=self.rng.randint(1, 3))
                    continue
                nights = self.rng.choices(
                    [1, 2, 3, 4, 5, 7, 10], [8, 18, 22, 18, 14, 14, 6]
                )[0]
                check_in, check_out = d, d + timedelta(days=nights)
                rows.append(
                    self._make_booking(
                        room, prop, check_in, check_out, sources, weights
                    )
                )
                d = check_out + timedelta(days=self.rng.choice([0, 0, 0, 1, 2]))
        return rows

    def _seed_demo_guest_stays(self, sources, weights):
        for ci, co, status in [
            (-60, -55, "checked_out"),
            (-20, -17, "checked_out"),
            (21, 26, "confirmed"),
        ]:
            room = self.rng.choice(
                [r for r in self.rooms if r.property_id == self.props[1].id]
            )
            ci_d = self.today + timedelta(days=ci)
            co_d = self.today + timedelta(days=co)
            booking = self._make_booking(
                room,
                self.props[1],
                ci_d,
                co_d,
                sources,
                weights,
                guest=self.demo_guest,
                status=status,
                source="direct_website",
                check_conflicts=True,
            )
            if booking:
                booking.save()
                self.bookings.append(booking)

    def _link_agency_group_bookings(self):
        group = [
            b
            for b in self.bookings
            if b.travel_agency_id and b.check_in_date > self.today
        ][:3]
        for booking in group[1:]:
            booking.related_bookings = group[0]
            booking.save(update_fields=["related_bookings"])

    def _bookings(self):
        sources, weights = zip(*SOURCES)
        rows = self._seed_room_stay_rows(sources, weights)
        Booking.objects.bulk_create(rows, batch_size=1000)
        self.bookings = list(
            Booking.objects.filter(room__property__in=self.props).select_related(
                "room", "guest"
            )
        )
        self._seed_demo_guest_stays(sources, weights)
        self._link_agency_group_bookings()

    def _past_departure_status(self, roll):
        if roll > 0.92:
            return "cancelled"
        if roll > 0.90:
            return "no_show"
        return "checked_out"

    def _future_arrival_status(self, roll):
        if roll > 0.93:
            return "cancelled"
        if roll > 0.85:
            return "pending"
        return "confirmed"

    def _resolve_booking_status(self, check_in, check_out, status):
        if status is not None:
            return status
        roll = self.rng.random()
        departed = check_out < self.today or (check_out == self.today and roll < 0.45)
        if departed:
            return self._past_departure_status(roll)
        arrived = check_in < self.today or (check_in == self.today and roll < 0.4)
        if arrived:
            return "checked_in"
        if check_in == self.today:
            return "confirmed"
        return self._future_arrival_status(roll)

    def _booking_pricing(self, room, prop, check_in, nights):
        plan = self.rng.choices(self.rate_plans[prop.id], [60, 25, 15])[0]
        plan_factor = {
            "BAR": Decimal("1"),
            "NRF": Decimal("0.88"),
            "HB": Decimal("1.22"),
        }[plan.code]
        subtotal = sum(
            (
                nightly_rate(room.base_price, check_in + timedelta(days=i))
                for i in range(nights)
            ),
            Decimal("0"),
        )
        subtotal = money(
            subtotal * plan_factor * Decimal(str(self.rng.uniform(0.95, 1.06)))
        )
        return plan, subtotal, compute_taxes(subtotal, nights)

    def _in_house_guest_fields(self, guest, in_house):
        if not in_house:
            return {
                "guest_document_type": "",
                "guest_document_number": "",
                "guest_nationality": "",
                "guest_birth_date": None,
                "shima_stay_purpose": "",
            }
        return {
            "guest_document_type": guest.document_type,
            "guest_document_number": guest.document_number,
            "guest_nationality": guest.nationality,
            "guest_birth_date": guest.birth_date,
            "shima_stay_purpose": "leisure",
        }

    def _make_booking(
        self,
        room,
        prop,
        check_in,
        check_out,
        sources,
        weights,
        guest=None,
        status=None,
        source=None,
        check_conflicts=False,
    ):
        if check_conflicts and Booking.objects.filter(
            room=room,
            check_in_date__lt=check_out,
            check_out_date__gt=check_in,
            status__in=["confirmed", "checked_in", "checked_out", "pending"],
        ).exists():
            return None
        guest = guest or self._pick_guest()
        source = source or self.rng.choices(sources, weights)[0]
        nights = (check_out - check_in).days
        lead = self.rng.choices([1, 5, 14, 30, 60, 120], [10, 15, 25, 25, 15, 10])[
            0
        ] + self.rng.randint(0, 6)
        reserved = min(check_in - timedelta(days=lead), self.today)
        status = self._resolve_booking_status(check_in, check_out, status)
        plan, subtotal, taxes = self._booking_pricing(room, prop, check_in, nights)
        adults = min(room.capacity, self.rng.choice([1, 2, 2, 2, 3]))
        children = self.rng.choice([0, 0, 0, 1, 2]) if room.capacity >= 4 else 0
        in_house = status in ("checked_in", "checked_out")
        # RNG order must match the pre-refactor body: ages before agency choice.
        children_ages = [self.rng.randint(2, 12) for _ in range(children)]
        agency = self.rng.choice(self.agencies) if source == "travel_agency" else None
        return Booking(
            room=room,
            room_type=room.rt,
            rate_plan=plan,
            guest=guest,
            check_in_date=check_in,
            check_out_date=check_out,
            date_of_reservation=reserved,
            number_of_guests=adults + children,
            adults=adults,
            children=children,
            children_ages=children_ages,
            status=status,
            base_price=subtotal,
            actual_price=taxes["total_with_taxes"],
            vat_amount=taxes["vat_amount"],
            climate_resilience_fee=taxes["climate_resilience_fee"],
            booking_source=source,
            travel_agency=agency,
            special_requests=self.rng.choice(SPECIAL_REQUESTS),
            mhte_registry_number=prop.mhte_number,
            **self._in_house_guest_fields(guest, in_house),
        )

    def _sync_inventory(self):
        for room in self.rooms:
            recalculate_room_availability(
                room, self.start - timedelta(days=10), self.end + timedelta(days=11)
            )
        active = {}
        for b in self.bookings:
            if b.status in ("confirmed", "checked_in", "pending") and b.room_type_id:
                d = max(b.check_in_date, self.today)
                while d < b.check_out_date:
                    active[(b.room_type_id, d)] = active.get((b.room_type_id, d), 0) + 1
                    d += timedelta(days=1)
        rows = []
        for rt in self.room_types.values():
            count = rt.rooms.count()
            for offset in range((self.end - self.today).days + 1):
                d = self.today + timedelta(days=offset)
                rows.append(
                    RoomTypeAvailability(
                        room_type=rt,
                        date=d,
                        allotment=count,
                        booked=active.get((rt.id, d), 0),
                        min_stay=2 if season_factor(d) > 1.3 else 1,
                    )
                )
        RoomTypeAvailability.objects.bulk_create(
            rows, batch_size=2000, ignore_conflicts=True
        )

    def _room_statuses(self):
        occupied = {b.room_id for b in self.bookings if b.status == "checked_in"}
        cleaning = {
            b.room_id
            for b in self.bookings
            if b.status == "checked_out" and b.check_out_date == self.today
        }
        Room.objects.filter(id__in=occupied).update(status="occupied")
        Room.objects.filter(id__in=cleaning - occupied).update(status="cleaning")
        free = [r for r in self.rooms if r.id not in occupied | cleaning]
        for room in self.rng.sample(free, min(2, len(free))):
            Room.objects.filter(id=room.id).update(
                status="maintenance",
                status_start_date=self.today,
                status_end_date=self.today + timedelta(days=2),
            )

    # ── money ──────────────────────────────────────────────────────────────
    def _payment_amount_for_booking(self, booking, total, created):
        if booking.status == "checked_out":
            processed = timezone.make_aware(
                datetime.combine(booking.check_out_date, time(10, 30))
            )
            return total, "completed", processed
        if booking.status == "checked_in":
            status = "completed" if self.rng.random() < 0.6 else "pending"
            return total, status, created
        if booking.status == "cancelled":
            if self.rng.random() < 0.5:
                return None
            return money(total * Decimal("0.3")), "refunded", created
        # confirmed: 30% deposit taken for most
        if self.rng.random() < 0.25:
            return total, "pending", None
        return money(total * Decimal("0.3")), "completed", created

    def _create_refund_if_needed(self, payment, booking, amount, status):
        if status != "refunded":
            return
        RefundRequest.objects.create(
            payment=payment,
            guest=booking.guest,
            refund_amount=amount,
            reason="cancellation",
            description="Guest cancelled within free-cancellation window.",
            status=self.rng.choice(["processed", "processed", "approved", "pending"]),
            processed_by=self.users["demo_manager"],
        )

    def _create_invoice_if_needed(self, payment, booking, total, status):
        tax_amount = (booking.vat_amount or 0) + (booking.climate_resilience_fee or 0)
        if booking.status == "checked_out":
            Invoice.objects.create(
                guest=booking.guest,
                payment=payment,
                booking=booking,
                amount=booking.base_price,
                tax_amount=tax_amount,
                total_amount=total,
                status="paid",
                description=(
                    f"Accommodation {booking.check_in_date:%d/%m} – "
                    f"{booking.check_out_date:%d/%m/%Y}"
                ),
                issued_date=timezone.make_aware(
                    datetime.combine(booking.check_out_date, time(10))
                ),
                due_date=booking.check_out_date,
                paid_date=booking.check_out_date,
            )
            return
        if booking.status == "checked_in" and status == "pending":
            Invoice.objects.create(
                guest=booking.guest,
                payment=payment,
                booking=booking,
                amount=booking.base_price,
                tax_amount=tax_amount,
                total_amount=total,
                status="issued",
                description="Pro-forma for current stay",
                due_date=booking.check_out_date,
            )

    def _payments_and_invoices(self):
        card, cash, bank, wallet = (
            self.methods[n]
            for n in ("Credit Card", "Cash", "Bank Transfer", "Viva Wallet")
        )
        for booking in self.bookings:
            if booking.status in ("pending", "no_show"):
                continue
            method = (
                bank
                if booking.booking_source == "travel_agency"
                else self.rng.choices([card, wallet, cash], [70, 18, 12])[0]
            )
            total = booking.actual_price
            created = timezone.make_aware(
                datetime.combine(
                    booking.date_of_reservation, time(self.rng.randint(8, 22))
                )
            )
            details = self._payment_amount_for_booking(booking, total, created)
            if details is None:
                continue
            amount, status, processed = details
            payment = Payment.objects.create(
                guest=booking.guest,
                booking=booking,
                payment_method=method,
                amount=amount,
                currency="EUR",
                status=status,
                transaction_id=f"DEMO-TX-{secrets.token_hex(8)}",
                reference_code=f"DEMO-{secrets.token_hex(5).upper()}",
                processed_at=processed if status != "pending" else None,
                is_verified=status == "completed",
                description=(
                    f"{(booking.check_out_date - booking.check_in_date).days}-night "
                    f"stay, room {booking.room.room_number}"
                ),
            )
            Payment.objects.filter(pk=payment.pk).update(created_at=created)
            self._create_refund_if_needed(payment, booking, amount, status)
            self._create_invoice_if_needed(payment, booking, total, status)

    def _channels(self):
        mapping = {
            "booking_com": ("booking_com", "ota"),
            "expedia": ("expedia", "ota"),
            "airbnb": ("airbnb", "ota"),
            "trivago": ("trivago", "metasearch"),
        }
        by_key = {}
        for prop in self.props:
            for name, ctype in mapping.values():
                by_key[(prop.id, name)] = Channel.objects.create(
                    property=prop,
                    channel_name=name,
                    channel_type=ctype,
                    account_id=f"DEMO-{prop.id}-{name.upper()}",
                    api_key="demo-not-a-real-key",
                    is_active=True,
                    sync_enabled=False,
                    accept_bookings=True,
                    last_sync_at=timezone.now()
                    - timedelta(minutes=self.rng.randint(3, 50)),
                )
        links = []
        for b in self.bookings:
            ch = by_key.get(
                (b.room.property_id, mapping.get(b.booking_source, (None,))[0])
            )
            if ch:
                links.append(
                    ChannelBooking(
                        channel=ch,
                        nephele_booking=b,
                        channel_booking_id=f"{ch.channel_name[:3].upper()}{b.id:08d}",
                        sync_status=(
                            "cancelled" if b.status == "cancelled" else "synced"
                        ),
                    )
                )
        ChannelBooking.objects.bulk_create(links, batch_size=1000)

    # ── pricing / ML ───────────────────────────────────────────────────────
    def _occupancy_by_prop_day(self):
        occ_by_prop_day = {}
        for booking in self.bookings:
            if booking.status in ("cancelled", "no_show"):
                continue
            day = booking.check_in_date
            while day < booking.check_out_date:
                key = (booking.room.property_id, day)
                occ_by_prop_day[key] = occ_by_prop_day.get(key, 0) + 1
                day += timedelta(days=1)
        return occ_by_prop_day

    def _pricing_history_row(self, room, prop, day, occ_by_prop_day):
        occ = Decimal(
            min(100, 100 * occ_by_prop_day.get((prop.id, day), 0) / prop.total_rooms)
        ).quantize(TWO)
        base = nightly_rate(room.base_price, day)
        uplift = Decimal(
            str(1 + (float(occ) - 60) / 400 + self.rng.uniform(-0.03, 0.03))
        )
        dynamic = money(base * uplift)
        future = day >= self.today
        conf = Decimal(str(round(self.rng.uniform(0.72, 0.96), 2)))
        return PricingHistory(
            room=room,
            date=day,
            weekday=day.weekday(),
            base_price=base,
            dynamic_price=dynamic,
            competitor_price=money(base * Decimal(str(self.rng.uniform(0.9, 1.15)))),
            occupancy_rate=occ,
            demand_score=min(
                Decimal("100"),
                occ * Decimal("0.8") + Decimal(self.rng.randint(5, 25)),
            ),
            bookings_count=occ_by_prop_day.get((prop.id, day), 0),
            cancellation_rate=Decimal(str(round(self.rng.uniform(3, 11), 2))),
            season=season_label(day),
            predicted_by_model=future,
            model_version="xgb-2026.09" if future else "",
            confidence_score=conf if future else Decimal("0"),
            ai_recommended_price=dynamic if future else None,
            ensemble_prediction=dynamic if future else None,
            occupancy_impact_percentage=Decimal(
                str(round((float(occ) - 60) / 4, 2))
            ),
            seasonal_impact_percentage=Decimal(
                str(round((season_factor(day) - 1) * 100, 2))
            ),
        )

    def _competitor_rows_for_room(self, room, prop):
        if not (room.room_number.endswith("01") or room.room_number.endswith("02")):
            return []
        rows = []
        for offset in range(-30, 31, 2):
            day = self.today + timedelta(days=offset)
            for name in COMPETITORS[prop.city]:
                rows.append(
                    CompetitorPrice(
                        room=room,
                        competitor_name=name,
                        date=day,
                        price=money(
                            nightly_rate(room.base_price, day)
                            * Decimal(str(self.rng.uniform(0.85, 1.25)))
                        ),
                    )
                )
        return rows

    def _pricing(self):
        occ_by_prop_day = self._occupancy_by_prop_day()
        history, competitors = [], []
        for room in self.rooms:
            prop = next(p for p in self.props if p.id == room.property_id)
            for offset in range(-(self.today - self.start).days, 31):
                day = self.today + timedelta(days=offset)
                history.append(
                    self._pricing_history_row(room, prop, day, occ_by_prop_day)
                )
            competitors.extend(self._competitor_rows_for_room(room, prop))
        PricingHistory.objects.bulk_create(history, batch_size=2000)
        CompetitorPrice.objects.bulk_create(competitors, batch_size=2000)

    # ── operations ─────────────────────────────────────────────────────────
    def _seed_cleaning_tasks(self, staff, now):
        dirty = list(
            Room.objects.filter(
                property=self.props[0], status__in=["cleaning", "occupied"]
            )
        )[:10]
        statuses = ["completed", "completed", "in_progress", "pending", "pending"]
        for index, room in enumerate(dirty):
            status = statuses[index % 5]
            Task.objects.create(
                employee=staff,
                property=self.props[0],
                title=f"Clean room {room.room_number}",
                description=(
                    "Full turnover clean"
                    if room.status == "cleaning"
                    else "Stay-over service"
                ),
                start_time=now + timedelta(minutes=30 * index),
                end_time=now + timedelta(minutes=30 * index + 30),
                status=status,
                priority="high" if room.status == "cleaning" else "medium",
                completed_at=now if status == "completed" else None,
            )

    def _seed_maintenance_tasks(self, tech, now, athens_rooms):
        for title, prio in [
            ("Fix A/C in room", "urgent"),
            ("Replace bathroom light", "low"),
            ("Check minibar fridge", "medium"),
        ]:
            room = self.rng.choice(athens_rooms)
            Task.objects.create(
                employee=tech,
                property=self.props[0],
                title=f"{title} {room.room_number}",
                description=title,
                start_time=now + timedelta(hours=1),
                end_time=now + timedelta(hours=2),
                status="pending",
                priority=prio,
            )

    def _seed_room_services(self):
        descriptions = {
            "food": "Breakfast in room for two",
            "cleaning": "Extra towels",
            "laundry": "Express shirt pressing",
            "concierge": "Book sunset cruise",
            "technical": "TV remote not working",
        }
        in_house = [b for b in self.bookings if b.status == "checked_in"]
        for booking in self.rng.sample(in_house, min(14, len(in_house))):
            kind = self.rng.choice(
                ["food", "food", "cleaning", "laundry", "concierge", "technical"]
            )
            RoomService.objects.create(
                booking=booking,
                room=booking.room,
                service_type=kind,
                status=self.rng.choice(["pending", "in_progress", "completed"]),
                description=descriptions[kind],
                price=money(self.rng.choice([0, 18, 24, 35, 60])),
            )

    def _seed_announcements_events_storage(self):
        mgr = Employee.objects.get(user=self.users["demo_manager"])
        for text in [
            "Fire drill Thursday 10:00 – all departments.",
            "New breakfast menu launches Monday, please brief guests.",
            "Wedding group (22 rooms) arriving next weekend – VIP amenities required.",
        ]:
            Announcement.objects.create(
                content=f"[demo] {text}",
                sender=mgr,
                date=self.today - timedelta(days=self.rng.randint(0, 5)),
            )
        for etype, loc, days, text in [
            (
                "Live Music",
                "Rooftop Bar",
                2,
                "Greek bouzouki night under the Acropolis",
            ),
            ("Conference", "Aegean Hall", 9, "Mediterranean Tourism Tech Summit"),
            ("Movie", "Garden Terrace", 4, "Open-air cinema: Zorba the Greek"),
        ]:
            Event.objects.create(
                eventType=etype,
                location=loc,
                startDate=self.today + timedelta(days=days),
                endDate=self.today + timedelta(days=days),
                explanation=f"[demo] {text}",
            )
        FoodMenu.objects.create(
            startDate=self.today,
            endDate=self.today + timedelta(days=6),
            menuItems="[demo] Greek yoghurt with thyme honey; Spanakopita; Grilled octopus; Moussaka; Loukoumades",
        )
        for name, kind, qty in [
            ("Bath towels", "Textile ", 420),
            ("Bed linen sets", "Textile ", 260),
            ("Espresso capsules", "Kitchen", 1800),
            ("Multi-surface cleaner", "Cleaning", 64),
            ("Spare TV remotes", "Electronic", 12),
        ]:
            Storage.objects.create(
                itemName=f"[demo] {name}", itemType=kind, quantitiy=qty
            )

    def _operations(self):
        staff = Employee.objects.get(user=self.users["demo_staff"])
        tech = Employee.objects.get(user=self.users["demo_maintenance"])
        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        athens_rooms = [r for r in self.rooms if r.property_id == self.props[0].id]
        self._seed_cleaning_tasks(staff, now)
        self._seed_maintenance_tasks(tech, now, athens_rooms)
        self._seed_room_services()
        self._seed_announcements_events_storage()

    def _guest_stats(self):
        for g in self.guests + [self.demo_guest]:
            stays = [
                b
                for b in self.bookings
                if b.guest_id == g.id and b.status == "checked_out"
            ]
            g.number_of_bookings = len([b for b in self.bookings if b.guest_id == g.id])
            g.total_nights_stayed = sum(
                (b.check_out_date - b.check_in_date).days for b in stays
            )
        Guest.objects.bulk_update(
            self.guests + [self.demo_guest],
            ["number_of_bookings", "total_nights_stayed"],
        )

    # ── analytics (uses the real ETL code paths) ───────────────────────────
    def _analytics(self, days_back):
        from analytics import tasks as at

        self.stdout.write("Computing analytics (executive, revenue, guest, forecasts)…")
        for prop in self.props:
            for offset in range(days_back, -1, -1):
                d = self.today - timedelta(days=offset)
                at.calculate_executive_metrics(property_id=prop.id, metric_date=d)
                at.calculate_revenue_metrics(property_id=prop.id, metric_date=d)
                if offset % 7 == 0:
                    at.calculate_guest_analytics(property_id=prop.id, analytics_date=d)
            at.calculate_operational_status(property_id=prop.id)
            for fn in (at.forecast_occupancy_task, at.forecast_revenue_task):
                self._try(fn, property_id=prop.id, forecast_days=30)
            for fn in (at.predict_cancellations_task, at.predict_noshow_task):
                self._try(fn, property_id=prop.id)

    def _try(self, fn, **kwargs):
        try:
            fn(**kwargs)
        except Exception as exc:  # forecasting models are optional in some deployments
            self.stdout.write(self.style.WARNING(f"  {fn.__name__} skipped: {exc}"))

    def _report(self):
        qs = Booking.objects.filter(room__property__in=self.props)
        t = self.today
        self.stdout.write(self.style.SUCCESS("✓ Showcase data ready"))
        self.stdout.write(
            f"  Properties: {len(self.props)}  Rooms: {len(self.rooms)}  Guests: {len(self.guests) + 1}"
        )
        self.stdout.write(
            f"  Bookings: {qs.count()}  (in-house {qs.filter(status='checked_in').count()}, "
            f"arrivals today {qs.filter(check_in_date=t).exclude(status='cancelled').count()}, "
            f"departures today {qs.filter(check_out_date=t).exclude(status='cancelled').count()})"
        )
        self.stdout.write(
            f"  Payments: {Payment.objects.filter(booking__in=qs).count()}  Invoices: {Invoice.objects.filter(booking__in=qs).count()}"
        )
        self.stdout.write(f"  Logins: {', '.join(u[0] for u in ROLE_USERS)}")
