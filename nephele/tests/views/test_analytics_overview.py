"""Live analytics overview endpoints, custom report exports and forecasting jobs."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group, User
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Employee, Guest, Task
from analytics import tasks
from analytics.metrics import SOURCE_LABELS, NightLedger
from analytics.models import (
    CancellationPrediction, CustomReport, DashboardExecutiveMetrics,
    NoShowPrediction, OccupancyForecast, RevenueForecast,
)
from payments.models import Payment, PaymentMethod
from properties.models import Property
from room.models import Booking, Room

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def _property(name, city):
    return Property.objects.create(
        name=name,
        location=city,
        address="1 Main St",
        city=city,
        postal_code="10000",
        country="Greece",
    )


def _room(prop, number, status="available"):
    return Room.objects.create(
        property=prop,
        room_number=number,
        floor=1,
        room_type="double",
        capacity=2,
        number_of_beds=1,
        base_price=Decimal("100.00"),
        current_price=Decimal("100.00"),
        status=status,
    )


def _guest(email, country="Germany"):
    return Guest.objects.create(
        email=email,
        first_name=email.split("@")[0].title(),
        last_name="Test",
        country=country,
    )


def _booking(
    room, guest, check_in, nights, status="checked_out", base="300.00", **extra
):
    return Booking.objects.create(
        room=room,
        guest=guest,
        check_in_date=check_in,
        check_out_date=check_in + timedelta(days=nights),
        status=status,
        base_price=Decimal(base),
        actual_price=Decimal(base) * Decimal("1.13"),
        number_of_guests=2,
        adults=2,
        date_of_reservation=check_in - timedelta(days=20),
        **extra,
    )


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def hotel(db):
    today = timezone.localdate()
    athens, chania = _property("Athens Test", "Athens"), _property(
        "Chania Test", "Chania"
    )
    a1, a2 = _room(athens, "101"), _room(athens, "102")
    c1 = _room(chania, "201")
    anna, ben = _guest("anna@ex.com"), _guest("ben@ex.com", country="France")
    stays = {
        # 3 nights for €300 inside the last week -> ADR must be €100, not €300
        "past": _booking(
            a1, anna, today - timedelta(days=5), 3, booking_source="booking_com"
        ),
        "in_house": _booking(
            a1,
            ben,
            today - timedelta(days=1),
            2,
            status="checked_in",
            base="240.00",
            booking_source="direct_website",
        ),
        "arrival": _booking(
            a2,
            anna,
            today,
            2,
            status="confirmed",
            base="200.00",
            booking_source="expedia",
        ),
        "chania": _booking(
            c1, ben, today - timedelta(days=3), 1, base="80.00", booking_source="phone"
        ),
        "cancelled": _booking(
            c1, anna, today - timedelta(days=6), 2, status="cancelled"
        ),
    }
    # Checked-out bookings flip rooms to "cleaning" via a signal; set the live states last
    for room, state in ((a1, "occupied"), (a2, "cleaning"), (c1, "available")):
        Room.objects.filter(pk=room.pk).update(status=state)
    manager = User.objects.create_user(username="mgr", password="x")
    manager.groups.add(Group.objects.get_or_create(name="manager")[0])
    return {
        "today": today,
        "athens": athens,
        "chania": chania,
        "rooms": (a1, a2, c1),
        "guests": (anna, ben),
        "stays": stays,
        "manager": manager,
    }


@pytest.fixture
def client(hotel):
    api = APIClient()
    api.force_authenticate(hotel["manager"])
    return api


def test_night_ledger_attributes_revenue_per_night(hotel):
    today = hotel["today"]
    day = today - timedelta(days=4)  # second night of the 3-night €300 stay
    kpis = NightLedger([hotel["athens"]], day, day).kpis()
    assert kpis["total_revenue"] == 100.0
    assert kpis["adr"] == 100.0
    assert kpis["occupancy_rate"] == 50.0  # 1 of 2 Athens rooms


def test_etl_executive_metrics_use_nightly_rate_and_checked_out_stays(hotel):
    day = hotel["today"] - timedelta(days=4)
    tasks.calculate_executive_metrics(property_id=hotel["athens"].id, metric_date=day)
    metric = DashboardExecutiveMetrics.objects.get(
        property=hotel["athens"], metric_date=day
    )
    assert metric.total_revenue == Decimal("100.00")
    assert metric.avg_daily_rate == Decimal("100.00")
    assert metric.occupancy_rate == Decimal("50.00")


def test_executive_overview_shape_and_property_filter(client, hotel):
    response = client.get(
        "/api/v1/analytics/executive-dashboard/overview/", {"period": "week"}
    )
    assert response.status_code == 200
    data = response.json()
    assert {p["name"] for p in data["properties"]} == {"Athens Test", "Chania Test"}
    assert len(data["revenue_trend"]) == 7
    # 3×100 (past) + 120 (in-house night yesterday) + 120 (tonight) + 80 (Chania) + 100 (arrival tonight)
    assert data["kpis"]["total_revenue"] == 720.0
    assert data["kpis"]["revenue_trend_pct"] is None  # no previous-week sales
    assert [m["metric"] for m in data["year_over_year"]][0] == "Revenue (€)"

    only_chania = client.get(
        "/api/v1/analytics/executive-dashboard/overview/",
        {"period": "week", "property_id": hotel["chania"].id},
    ).json()
    assert only_chania["kpis"]["total_revenue"] == 80.0
    assert [p["name"] for p in only_chania["top_properties"]] == ["Chania Test"]


def test_year_period_is_bucketed_by_month(client, hotel):
    data = client.get(
        "/api/v1/analytics/executive-dashboard/overview/", {"period": "year"}
    ).json()
    assert all(len(row["date"]) == 7 for row in data["revenue_trend"])
    assert 12 <= len(data["revenue_trend"]) <= 13


def test_revenue_overview_sources_and_payments(client, hotel):
    method = PaymentMethod.objects.create(name="Card", payment_type="card")
    stays = hotel["stays"]
    for booking, amount, status in [
        (stays["past"], "339.00", "completed"),
        (stays["in_house"], "100.00", "pending"),
        (stays["cancelled"], "50.00", "refunded"),
    ]:
        Payment.objects.create(
            guest=booking.guest,
            booking=booking,
            payment_method=method,
            amount=Decimal(amount),
            status=status,
            transaction_id=f"tx-{booking.id}",
            reference_code=f"ref-{booking.id}",
        )

    data = client.get(
        "/api/v1/analytics/revenue-analytics/overview/", {"period": "week"}
    ).json()
    assert data["kpis"]["collected"] == 339.0
    assert data["kpis"]["outstanding"] == 100.0
    assert data["kpis"]["refunded"] == 50.0
    assert data["payments_by_method"] == [
        {"method": "Card", "count": 1, "amount": 339.0}
    ]
    sources = {row["source"]: row for row in data["revenue_by_source"]}
    assert sources["booking_com"]["revenue"] == 300.0
    assert sources["booking_com"]["label"] == SOURCE_LABELS["booking_com"]
    assert round(sum(row["pct"] for row in data["revenue_by_source"])) == 100


def test_guest_overview_counts_repeat_guests_and_nationalities(client, hotel):
    data = client.get(
        "/api/v1/analytics/guest-analytics/overview/", {"period": "week"}
    ).json()
    assert data["kpis"]["total_guests"] == 2
    assert data["kpis"]["repeat_guests"] == 2  # both stayed more than once this week
    assert data["kpis"]["in_house"] == 1
    assert {n["country"] for n in data["nationalities"]} == {"Germany", "France"}
    assert data["guest_segments"][0]["segment"] == "Couple"


def test_operational_overview_without_property(client, hotel):
    employee = Employee.objects.create(
        user=User.objects.create_user(username="maid"), property=hotel["athens"]
    )
    now = timezone.now()
    Task.objects.create(
        employee=employee,
        property=hotel["athens"],
        title="Clean 102",
        description="Turnover",
        start_time=now,
        end_time=now + timedelta(hours=1),
    )

    data = client.get("/api/v1/analytics/operational-dashboard/overview/").json()
    assert data["room_status"] == {
        "occupied": 1,
        "available": 1,
        "cleaning": 1,
        "maintenance": 0,
        "blocked": 0,
        "total": 3,
    }
    assert [m["booking_id"] for m in data["checkins_today"]] == [
        hotel["stays"]["arrival"].id
    ]
    assert data["checkins_today"][0]["property_name"] == "Athens Test"
    assert data["staff_tasks"][0]["title"] == "Clean 102"
    assert len(data["rooms"]) == 3


def test_overview_requires_analytics_role(hotel):
    receptionist = User.objects.create_user(username="desk")
    receptionist.groups.add(Group.objects.get_or_create(name="receptionist")[0])
    api = APIClient()
    api.force_authenticate(receptionist)
    assert api.get("/api/v1/analytics/executive-dashboard/overview/").status_code == 403


def _create_report(client, hotel, **overrides):
    today = hotel["today"]
    payload = {
        "name": "Week payments",
        "report_type": "payment",
        "property": None,
        "from_date": (today - timedelta(days=7)).isoformat(),
        "to_date": today.isoformat(),
        "export_format": "csv",
        **overrides,
    }
    response = client.post("/api/v1/analytics/custom-reports/", payload, format="json")
    assert response.status_code == 201, response.content
    return response.json()


def test_payment_report_for_all_properties(client, hotel):
    method = PaymentMethod.objects.create(name="Cash", payment_type="cash")
    booking = hotel["stays"]["past"]
    Payment.objects.create(
        guest=booking.guest,
        booking=booking,
        payment_method=method,
        amount=Decimal("339.00"),
        status="completed",
        transaction_id="tx-r",
        reference_code="REF-R",
    )
    report = _create_report(client, hotel)
    assert report["property_name"] is None

    generated = client.post(
        f"/api/v1/analytics/custom-reports/{report['id']}/generate/"
    ).json()
    assert generated["status"] == "generated"

    data = client.get(f"/api/v1/analytics/custom-reports/{report['id']}/data/").json()
    assert [row["reference"] for row in data["rows"]] == ["REF-R"]
    assert data["summary"]["Collected (€)"] == 339.0

    download = client.get(f"/api/v1/analytics/custom-reports/{report['id']}/download/")
    assert download.status_code == 200
    assert download["Content-Type"].startswith("text/csv")
    assert "attachment;" in download["Content-Disposition"]
    assert b"REF-R" in download.content


@pytest.mark.parametrize(
    "report_type", ["revenue", "occupancy", "booking", "guest", "pricing", "custom"]
)
def test_every_report_type_builds(client, hotel, report_type):
    report = _create_report(
        client, hotel, report_type=report_type, property=hotel["athens"].id
    )
    response = client.get(f"/api/v1/analytics/custom-reports/{report['id']}/data/")
    assert response.status_code == 200
    data = response.json()
    assert data["columns"] and isinstance(data["rows"], list) and data["summary"]


@pytest.mark.parametrize(
    "fmt,content_type",
    [
        ("excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("pdf", "application/pdf"),
    ],
)
def test_binary_exports(client, hotel, fmt, content_type):
    pytest.importorskip("openpyxl" if fmt == "excel" else "reportlab")
    report = _create_report(client, hotel, report_type="revenue", export_format=fmt)
    download = client.get(f"/api/v1/analytics/custom-reports/{report['id']}/download/")
    assert download.status_code == 200
    assert download["Content-Type"] == content_type
    assert len(download.content) > 500


def test_report_rejects_inverted_dates(client, hotel):
    today = hotel["today"]
    response = client.post(
        "/api/v1/analytics/custom-reports/",
        {
            "name": "Bad",
            "report_type": "revenue",
            "from_date": today.isoformat(),
            "to_date": (today - timedelta(days=1)).isoformat(),
        },
        format="json",
    )
    assert response.status_code == 400


def test_forecast_and_prediction_jobs_persist_rows(client, hotel):
    athens = hotel["athens"]
    future = _booking(
        hotel["rooms"][2],
        hotel["guests"][1],
        hotel["today"] + timedelta(days=40),
        1,
        status="confirmed",
        booking_source="travel_agency",
    )

    tasks.forecast_occupancy_task(property_id=athens.id, forecast_days=10)
    tasks.forecast_revenue_task(property_id=athens.id, forecast_days=10)
    tasks.predict_cancellations_task()
    tasks.predict_noshow_task()

    assert OccupancyForecast.objects.filter(property=athens).count() == 10
    tomorrow = OccupancyForecast.objects.get(
        property=athens, target_date=hotel["today"] + timedelta(days=1)
    )
    assert tomorrow.lower_bound <= tomorrow.predicted_occupancy <= tomorrow.upper_bound
    assert RevenueForecast.objects.filter(property=athens).count() == 10

    prediction = CancellationPrediction.objects.get(booking=future)
    assert prediction.risk_factors["advance_booking"] is True
    assert prediction.lead_time_days == 20
    assert NoShowPrediction.objects.filter(booking=hotel["stays"]["arrival"]).exists()

    high_risk = client.get("/api/v1/analytics/cancellation-predictions/").json()[
        "results"
    ]
    row = next(r for r in high_risk if r["booking_id"] == str(future.id))
    assert row["guest_name"] == "Ben Test"
    assert row["room_number"] == "201"
    assert "risk_factors" in row

    forecasts = client.get(
        "/api/v1/analytics/occupancy-forecasts/next-30-days/"
    ).json()["forecasts"]
    assert forecasts and forecasts[0]["property_name"] == "Athens Test"


def test_custom_report_task_marks_generated(hotel):
    report = CustomReport.objects.create(
        name="Rev",
        report_type="revenue",
        from_date=hotel["today"] - timedelta(days=3),
        to_date=hotel["today"],
        export_format="csv",
        created_by=hotel["manager"],
    )
    tasks.generate_custom_report(report.id)
    report.refresh_from_db()
    assert report.status == "generated"
    assert report.file_path.endswith(".csv")


def test_rebuild_analytics_command(hotel):
    from django.core.management import call_command

    call_command("rebuild_analytics", days=7, forecast_days=5)
    assert DashboardExecutiveMetrics.objects.filter(property=hotel["athens"]).count() == 8
    assert OccupancyForecast.objects.filter(property=hotel["chania"]).count() == 5
