"""
Comprehensive seed data script for HMS demo screenshots.
Run with: docker exec hms-django python /app/seed_demo_data.py
"""
import os
import sys
import django
import random
from decimal import Decimal

# Setup Django
sys.path.insert(0, '/app/HMS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HMS.settings')
django.setup()

from datetime import date, timedelta, datetime, time as dtime
from django.utils.timezone import make_aware
from django.utils import timezone
from django.contrib.auth.models import User, Group

from properties.models import Property
from accounts.models import Guest, Employee
from room.models import Room, Booking
from analytics.models import (
    DashboardExecutiveMetrics, DashboardOperationalStatus,
    DashboardRevenueMetrics, DashboardGuestAnalytics,
    CustomReport, ScheduledReport,
    OccupancyForecast, RevenueForecast,
    CancellationPrediction, NoShowPrediction,
    ForecastingModelMetrics
)

TODAY = date.today()
print(f"Seeding data for {TODAY}...")

# ── 1. Superuser ──────────────────────────────────────────────────────────────
admin, _ = User.objects.get_or_create(
    username='admin',
    defaults={'email': 'admin@nephele.io', 'is_staff': True, 'is_superuser': True}
)
admin.set_password('admin123')
admin.save()
print("Admin user ready.")

# ── 2. Property ───────────────────────────────────────────────────────────────
prop, _ = Property.objects.get_or_create(
    name='Nephele Boutique Hotel',
    defaults={
        'location': 'Athens Riviera',
        'address': '12 Poseidonos Avenue',
        'city': 'Athens',
        'postal_code': '17562',
        'country': 'Greece',
        'phone_number': '+30 210 9876543',
        'email': 'info@nephelehotel.gr',
        'website': 'https://www.nephelehotel.gr',
        'total_rooms': 40,
        'star_rating': 4,
        'manager': admin,
        'is_active': True,
    }
)
print(f"Property: {prop.name}")

# ── 3. Rooms ──────────────────────────────────────────────────────────────────
ROOM_DEFS = [
    # (number, floor, type, capacity, beds, base_price, status)
    ('101', 1, 'economic',  2, 1,  80,  'available'),
    ('102', 1, 'economic',  2, 1,  80,  'available'),
    ('103', 1, 'single',    1, 1,  95,  'occupied'),
    ('104', 1, 'single',    2, 1,  95,  'available'),
    ('105', 1, 'double',    2, 2, 130,  'available'),
    ('106', 1, 'double',    2, 2, 130,  'occupied'),
    ('201', 2, 'double',    3, 2, 140,  'cleaning'),
    ('202', 2, 'double',    3, 2, 140,  'available'),
    ('203', 2, 'deluxe',    2, 1, 185,  'occupied'),
    ('204', 2, 'deluxe',    2, 1, 185,  'available'),
    ('205', 2, 'deluxe',    3, 2, 195,  'available'),
    ('206', 2, 'deluxe',    3, 2, 195,  'maintenance'),
    ('301', 3, 'suite',     4, 2, 310,  'occupied'),
    ('302', 3, 'suite',     4, 2, 310,  'available'),
    ('303', 3, 'suite',     2, 1, 290,  'reserved'),
    ('304', 3, 'luxury',    2, 1, 450,  'occupied'),
    ('305', 3, 'luxury',    4, 2, 490,  'available'),
]

rooms = {}
for rnum, floor, rtype, cap, beds, bprice, status in ROOM_DEFS:
    r, _ = Room.objects.get_or_create(
        room_number=rnum,
        defaults={
            'floor': floor,
            'room_type': rtype,
            'capacity': cap,
            'number_of_beds': beds,
            'base_price': Decimal(str(bprice)),
            'current_price': Decimal(str(round(bprice * random.uniform(0.95, 1.25), 2))),
            'status': status,
            'property': prop,
        }
    )
    rooms[rnum] = r
print(f"Rooms: {len(rooms)} created/found.")

# ── 4. Guests ─────────────────────────────────────────────────────────────────
GUESTS_DATA = [
    ('maria.santos@email.com',    'Maria',    'Santos',    '+351 912345678', 'Lisbon',     'Portugal'),
    ('james.wilson@email.com',    'James',    'Wilson',    '+44 7911123456', 'London',     'United Kingdom'),
    ('anna.mueller@email.com',    'Anna',     'Mueller',   '+49 1511234567', 'Berlin',     'Germany'),
    ('giovanni.rossi@email.com',  'Giovanni', 'Rossi',     '+39 3471234567', 'Milan',      'Italy'),
    ('sophie.martin@email.com',   'Sophie',   'Martin',    '+33 612345678',  'Paris',      'France'),
    ('alex.papadopoulos@email.com','Alex',    'Papadopoulos','+30 6912345678','Athens',    'Greece'),
    ('emily.johnson@email.com',   'Emily',    'Johnson',   '+1 5551234567',  'New York',   'United States'),
    ('hiroshi.tanaka@email.com',  'Hiroshi',  'Tanaka',    '+81 9012345678', 'Tokyo',      'Japan'),
    ('chen.wei@email.com',        'Chen',     'Wei',       '+86 13912345678','Shanghai',   'China'),
    ('elena.ivanova@email.com',   'Elena',    'Ivanova',   '+7 9123456789',  'Moscow',     'Russia'),
    ('carlos.garcia@email.com',   'Carlos',   'Garcia',    '+34 612345678',  'Madrid',     'Spain'),
    ('lena.berg@email.com',       'Lena',     'Berg',      '+46 701234567',  'Stockholm',  'Sweden'),
]

guests = []
for email, fn, ln, phone, city, country in GUESTS_DATA:
    g, _ = Guest.objects.get_or_create(
        email=email,
        defaults={
            'first_name': fn,
            'last_name': ln,
            'phone_number': phone,
            'city': city,
            'country': country,
        }
    )
    guests.append(g)
print(f"Guests: {len(guests)} created/found.")

# ── 5. Bookings ───────────────────────────────────────────────────────────────
# Historical bookings (past 90 days) + current + upcoming
booking_specs = [
    # (room_num, guest_idx, days_ago_checkin, nights, status, source)
    ('103', 0,  0, 4, 'checked_in',    'direct_website'),
    ('106', 1,  0, 2, 'checked_in',    'booking_com'),
    ('203', 2,  0, 3, 'checked_in',    'direct_website'),
    ('301', 3,  0, 5, 'checked_in',    'trivago'),
    ('304', 4,  0, 7, 'checked_in',    'booking_com'),
    ('105', 5,  3, 2, 'checked_out',   'direct_website'),
    ('202', 6,  5, 3, 'checked_out',   'phone'),
    ('205', 7, 10, 4, 'checked_out',   'booking_com'),
    ('302', 8, 15, 2, 'checked_out',   'direct_website'),
    ('101', 9, 20, 3, 'checked_out',   'trivago'),
    ('104', 10, 25, 5, 'checked_out',  'direct_website'),
    ('204', 11, 30, 4, 'checked_out',  'booking_com'),
    ('303',  0,  5, 1, 'cancelled',    'direct_website'),
    ('102',  1,  8, 3, 'no_show',      'booking_com'),
    ('305', 2,  -3, 3, 'confirmed',    'direct_website'),  # future
    ('201', 3,  -5, 4, 'confirmed',    'phone'),
    ('305', 4,  -7, 6, 'confirmed',    'booking_com'),
    ('102', 5,  35, 2, 'checked_out',  'direct_website'),
    ('104', 6,  40, 3, 'checked_out',  'trivago'),
    ('205', 7,  45, 5, 'checked_out',  'booking_com'),
    ('202', 8,  50, 2, 'checked_out',  'direct_website'),
    ('103', 9,  55, 4, 'checked_out',  'phone'),
    ('106', 10, 60, 3, 'checked_out',  'booking_com'),
    ('203', 11, 65, 6, 'checked_out',  'direct_website'),
    ('301', 0,  70, 3, 'checked_out',  'trivago'),
    ('304', 1,  75, 2, 'checked_out',  'booking_com'),
    ('105', 2,  80, 4, 'checked_out',  'direct_website'),
]

created_bookings = []
for room_num, guest_idx, days_ago, nights, status, source in booking_specs:
    room = rooms.get(room_num)
    guest = guests[guest_idx % len(guests)]
    if not room:
        continue
    checkin = TODAY - timedelta(days=days_ago)
    checkout = checkin + timedelta(days=nights)
    res_date = checkin - timedelta(days=random.randint(3, 30))
    price = room.base_price * Decimal(str(random.uniform(0.9, 1.3)))
    price = round(price, 2)

    b, created = Booking.objects.get_or_create(
        room=room,
        guest=guest,
        check_in_date=checkin,
        defaults={
            'check_out_date': checkout,
            'date_of_reservation': res_date,
            'number_of_guests': random.randint(1, room.capacity),
            'status': status,
            'base_price': room.base_price,
            'actual_price': price,
            'booking_source': source,
        }
    )
    created_bookings.append(b)

print(f"Bookings: {len(created_bookings)} created/found.")

# ── 6. Dashboard Executive Metrics (90 days) ─────────────────────────────────
def rand_dec(lo, hi, dp=2):
    return Decimal(str(round(random.uniform(lo, hi), dp)))

for i in range(90):
    d = TODAY - timedelta(days=i)
    seasonal = 1.0 + 0.3 * abs((i - 45) / 45)  # peak in middle
    DashboardExecutiveMetrics.objects.get_or_create(
        property=prop,
        metric_date=d,
        defaults={
            'total_revenue': rand_dec(3800, 7200) * Decimal(str(seasonal)),
            'avg_daily_rate': rand_dec(140, 220),
            'occupancy_rate': rand_dec(55, 92),
            'revpar': rand_dec(90, 175),
            'booking_count': random.randint(8, 22),
            'yoy_revenue_change': rand_dec(-5, 18),
            'yoy_occupancy_change': rand_dec(-3, 12),
        }
    )

print("Executive metrics: 90 days seeded.")

# ── 7. Dashboard Operational Status (30 days) ────────────────────────────────
for i in range(30):
    d = TODAY - timedelta(days=i)
    DashboardOperationalStatus.objects.get_or_create(
        property=prop,
        status_date=d,
        status_time=make_aware(datetime.combine(d, dtime(8, 0, 0))),
        defaults={
            'occupied_count': random.randint(10, 16),
            'vacant_count': random.randint(1, 5),
            'cleaning_count': random.randint(1, 3),
            'maintenance_count': random.randint(0, 2),
            'blocked_count': random.randint(0, 1),
            'checkouts_scheduled': random.randint(2, 6),
            'checkins_scheduled': random.randint(2, 7),
            'housekeeping_tasks_pending': random.randint(2, 10),
            'housekeeping_tasks_in_progress': random.randint(1, 4),
            'maintenance_tickets_pending': random.randint(0, 3),
            'active_guests_count': random.randint(14, 28),
            'guests_with_special_requests': random.randint(2, 8),
        }
    )

print("Operational status: 30 days seeded.")

# ── 8. Dashboard Revenue Metrics (90 days) ───────────────────────────────────
for i in range(90):
    d = TODAY - timedelta(days=i)
    total = rand_dec(3800, 7200)
    direct_pct = Decimal(str(random.uniform(0.40, 0.55)))
    ota_pct = Decimal(str(random.uniform(0.30, 0.40)))
    agency_pct = 1 - direct_pct - ota_pct
    DashboardRevenueMetrics.objects.get_or_create(
        property=prop,
        metric_date=d,
        defaults={
            'total_revenue': total,
            'revenue_direct': total * direct_pct,
            'revenue_ota': total * ota_pct,
            'revenue_agency': total * agency_pct,
            'avg_daily_rate': rand_dec(140, 220),
            'revpar': rand_dec(90, 175),
            'dynamic_pricing_uplift': rand_dec(3, 14),
            'occupancy_rate': rand_dec(55, 92),
            'occupancy_count': random.randint(10, 16),
            'booking_count': random.randint(8, 22),
            'cancellation_count': random.randint(0, 3),
            'cancellation_rate': rand_dec(2, 10),
            'noshow_count': random.randint(0, 2),
            'revenue_forecast_30d': total * Decimal('1.05'),
            'occupancy_forecast_30d': rand_dec(60, 88),
        }
    )

print("Revenue metrics: 90 days seeded.")

# ── 9. Dashboard Guest Analytics (90 days) ────────────────────────────────────
for i in range(90):
    d = TODAY - timedelta(days=i)
    new_g = random.randint(4, 12)
    ret_g = random.randint(2, 8)
    DashboardGuestAnalytics.objects.get_or_create(
        property=prop,
        analytics_date=d,
        defaults={
            'total_unique_guests': new_g + ret_g,
            'new_guests': new_g,
            'returning_guests': ret_g,
            'repeat_booking_rate': rand_dec(22, 45),
            'avg_booking_lead_days': random.randint(7, 35),
            'avg_length_of_stay': rand_dec(2.5, 5.5),
            'avg_review_score': rand_dec(4.1, 4.9),
            'avg_nps': random.randint(42, 78),
            'review_rate': rand_dec(55, 80),
            'complaint_count': random.randint(0, 2),
            'complaint_resolution_rate': rand_dec(85, 100),
            'retention_rate': rand_dec(60, 82),
            'churn_rate': rand_dec(8, 22),
            'at_risk_guests': random.randint(0, 4),
            'recommendations_generated': random.randint(20, 60),
            'recommendations_accepted': random.randint(8, 25),
            'upsell_conversions': random.randint(2, 8),
            'cross_sell_conversions': random.randint(1, 5),
            'personalization_revenue_uplift': rand_dec(4, 12),
        }
    )

print("Guest analytics: 90 days seeded.")

# ── 10. Occupancy Forecasts (next 60 days + 30 days history) ─────────────────
MODEL_TYPES = ['prophet', 'sarima', 'ensemble']

for i in range(-30, 61):
    target = TODAY + timedelta(days=i)
    forecast_dt = TODAY - timedelta(days=max(0, -i))
    base = 72 + 15 * (0.5 - abs(i / 60))  # slightly higher near today
    for mtype in MODEL_TYPES:
        predicted = max(30, min(98, base + random.uniform(-8, 8)))
        conf_range = random.uniform(5, 15)
        OccupancyForecast.objects.get_or_create(
            property=prop,
            forecast_date=TODAY,
            target_date=target,
            model_type=mtype,
            defaults={
                'predicted_occupancy': Decimal(str(round(predicted, 2))),
                'lower_bound': Decimal(str(round(max(0, predicted - conf_range), 2))),
                'upper_bound': Decimal(str(round(min(100, predicted + conf_range), 2))),
                'actual_occupancy': Decimal(str(round(base + random.uniform(-5, 5), 2))) if i <= 0 else None,
                'forecast_error': Decimal(str(round(random.uniform(0.5, 4), 2))) if i <= 0 else None,
            }
        )

print("Occupancy forecasts: seeded.")

# ── 11. Revenue Forecasts (next 60 days + 30 days history) ───────────────────
for i in range(-30, 61):
    target = TODAY + timedelta(days=i)
    base_rev = 5200 + random.uniform(-800, 1200)
    RevenueForecast.objects.get_or_create(
        property=prop,
        forecast_date=TODAY,
        target_date=target,
        defaults={
            'predicted_revenue': Decimal(str(round(base_rev, 2))),
            'lower_bound': Decimal(str(round(base_rev * 0.88, 2))),
            'upper_bound': Decimal(str(round(base_rev * 1.12, 2))),
            'model_type': 'prophet',
            'predicted_occupancy': Decimal(str(round(random.uniform(62, 88), 2))),
            'avg_daily_rate': Decimal(str(round(random.uniform(148, 215), 2))),
            'num_rooms': 17,
            'actual_revenue': Decimal(str(round(base_rev * random.uniform(0.93, 1.07), 2))) if i <= 0 else None,
            'forecast_error': Decimal(str(round(random.uniform(50, 400), 2))) if i <= 0 else None,
            'forecast_error_pct': Decimal(str(round(random.uniform(0.5, 6), 2))) if i <= 0 else None,
        }
    )

print("Revenue forecasts: seeded.")

# ── 12. Cancellation Predictions ─────────────────────────────────────────────
risk_data = [
    # (score, risk_level, source, customer_type, refund_policy, price, intervention)
    (82, 'high',   'booking_com', 'leisure',  'flexible',      155.0, True,  'discount_offer'),
    (74, 'high',   'trivago',     'leisure',  'flexible',      185.0, True,  'loyalty_points'),
    (68, 'high',   'booking_com', 'business', 'non_refundable', 210.0, False, None),
    (58, 'medium', 'direct_website','leisure','flexible',       130.0, False, None),
    (52, 'medium', 'phone',       'business', 'flexible',       195.0, True,  'personal_call'),
    (45, 'medium', 'booking_com', 'leisure',  'flexible',       165.0, False, None),
    (28, 'low',    'direct_website','business','non_refundable', 220.0, False, None),
    (15, 'low',    'direct_website','leisure', 'non_refundable', 145.0, False, None),
    (76, 'high',   'trivago',     'leisure',  'flexible',       175.0, True,  'discount_offer'),
    (61, 'medium', 'booking_com', 'leisure',  'flexible',       160.0, False, None),
]

confirmed_bookings = [b for b in created_bookings if b.status in ('confirmed', 'checked_in')]
for idx, (score, level, source, ctype, refund, price, interv, itype) in enumerate(risk_data):
    booking = confirmed_bookings[idx % len(confirmed_bookings)] if confirmed_bookings else None
    if booking is None:
        break
    CancellationPrediction.objects.get_or_create(
        booking=booking,
        prediction_date=TODAY,
        defaults={
            'prediction_time': make_aware(datetime.combine(TODAY, dtime(9, 0, 0))),
            'property': prop,
            'cancellation_risk_score': Decimal(str(score)),
            'risk_level': level,
            'lead_time_days': random.randint(3, 45),
            'booking_source': source,
            'customer_type': ctype,
            'refund_policy': refund,
            'price_per_night': Decimal(str(price)),
            'model_version': 'v2.1',
            'intervention_flag': interv,
            'intervention_type': itype if interv else '',
        }
    )

print("Cancellation predictions: seeded.")

# ── 13. No-Show Predictions ───────────────────────────────────────────────────
noshow_data = [
    (71, 'high',   'Greece',  'booking_com',  False, 2,  145.0, 1, 1.08),
    (63, 'high',   'Germany', 'direct_website', True, 5, 190.0, 0, 1.06),
    (55, 'medium', 'France',  'trivago',       True,  3, 175.0, 2, 1.04),
    (48, 'medium', 'UK',      'booking_com',   True,  7, 215.0, 1, 1.03),
    (32, 'low',    'Italy',   'direct_website', True, 14, 165.0, 3, 1.02),
    (22, 'low',    'Spain',   'direct_website', True, 21, 140.0, 0, 1.01),
    (77, 'high',   'Russia',  'booking_com',   False, 1,  155.0, 0, 1.08),
    (44, 'medium', 'USA',     'phone',          True, 10, 200.0, 2, 1.03),
]

for idx, (score, level, country, source, paid, advance, price, reqs, factor) in enumerate(noshow_data):
    booking = confirmed_bookings[idx % len(confirmed_bookings)] if confirmed_bookings else None
    if booking is None:
        break
    NoShowPrediction.objects.get_or_create(
        booking=booking,
        prediction_date=TODAY + timedelta(days=1),
        defaults={
            'prediction_time': make_aware(datetime.combine(TODAY + timedelta(days=1), dtime(9, 0, 0))),
            'property': prop,
            'noshow_risk_score': Decimal(str(score)),
            'risk_level': level,
            'customer_country': country,
            'booking_source': source,
            'payment_confirmed': paid,
            'advance_checkin_days': advance,
            'price_per_night': Decimal(str(price)),
            'special_requests_count': reqs,
            'model_version': 'v2.1',
            'overbooking_flag': score >= 60,
            'overbooking_factor': Decimal(str(factor)),
        }
    )

print("No-show predictions: seeded.")

# ── 14. Forecasting Model Metrics ─────────────────────────────────────────────
model_metrics = [
    # (model_name, mae, rmse, mape, r2, prec, rec, f1, auc, acceptable, retrain)
    ('occupancy_prophet',  3.2,  4.1,  4.5, 0.91, None,  None,  None,  None,  True,  False),
    ('occupancy_sarima',   4.1,  5.2,  5.8, 0.87, None,  None,  None,  None,  True,  False),
    ('revenue_prophet',    312,  425,  5.8, 0.89, None,  None,  None,  None,  True,  False),
    ('cancellation_xgb',   None, None, None, None, 0.83, 0.78,  0.80,  0.88,  True,  False),
    ('noshow_xgb',         None, None, None, None, 0.79, 0.74,  0.76,  0.85,  True,  False),
]

for (mname, mae, rmse, mape, r2, prec, rec, f1, auc, acceptable, retrain) in model_metrics:
    ForecastingModelMetrics.objects.get_or_create(
        property=prop,
        model_name=mname,
        evaluation_date=TODAY,
        defaults={
            'evaluation_period': '30day',
            'mae': Decimal(str(mae)) if mae is not None else None,
            'rmse': Decimal(str(rmse)) if rmse is not None else None,
            'mape': Decimal(str(mape)) if mape is not None else None,
            'r_squared': Decimal(str(r2)) if r2 is not None else None,
            'precision': Decimal(str(prec)) if prec is not None else None,
            'recall': Decimal(str(rec)) if rec is not None else None,
            'f1_score': Decimal(str(f1)) if f1 is not None else None,
            'roc_auc': Decimal(str(auc)) if auc is not None else None,
            'predictions_count': random.randint(180, 500),
            'is_acceptable': acceptable,
            'needs_retraining': retrain,
        }
    )

print("Forecast model metrics: seeded.")

# ── 15. Custom Reports ────────────────────────────────────────────────────────
reports = [
    ('Monthly Revenue Report – April 2026',  'revenue',    TODAY - timedelta(days=50), TODAY - timedelta(days=20), 'pdf',   'completed'),
    ('Q1 Occupancy Analysis',                'occupancy',  TODAY - timedelta(days=90), TODAY - timedelta(days=1),  'excel', 'completed'),
    ('Guest Segmentation & Retention',       'guest',      TODAY - timedelta(days=60), TODAY,                      'pdf',   'completed'),
    ('Dynamic Pricing Performance',          'pricing',    TODAY - timedelta(days=30), TODAY,                      'excel', 'completed'),
    ('Weekly Operations Summary',            'occupancy',  TODAY - timedelta(days=7),  TODAY,                      'pdf',   'completed'),
    ('Cancellation Risk Analysis',           'revenue',    TODAY - timedelta(days=14), TODAY + timedelta(days=14), 'pdf',   'pending'),
    ('Summer Forecast Report',               'revenue',    TODAY,                      TODAY + timedelta(days=90), 'pdf',   'pending'),
]

for name, rtype, from_d, to_d, fmt, status in reports:
    CustomReport.objects.get_or_create(
        name=name,
        property=prop,
        defaults={
            'created_by': admin,
            'report_type': rtype,
            'from_date': from_d,
            'to_date': to_d,
            'include_charts': True,
            'include_summary': True,
            'include_detailed_data': True,
            'export_format': fmt,
            'status': status,
        }
    )

print("Custom reports: seeded.")

# ── 16. Scheduled Reports ─────────────────────────────────────────────────────
scheduled = [
    ('Daily Occupancy Briefing',        'daily_operational', 'daily',   None, ['manager@nephelehotel.gr']),
    ('Weekly Revenue Summary',          'weekly_performance','weekly',  1,    ['gm@nephelehotel.gr', 'revenue@nephelehotel.gr']),
    ('Monthly Executive KPI Report',    'monthly_executive', 'monthly', 1,    ['ceo@nephelehotel.gr', 'cfo@nephelehotel.gr']),
    ('Weekly Guest Insights Report',    'weekly_marketing',  'weekly',  None, ['marketing@nephelehotel.gr']),
]

for sname, rtype, sched, sday, recipients in scheduled:
    ScheduledReport.objects.get_or_create(
        name=sname,
        property=prop,
        defaults={
            'created_by': admin,
            'report_type': rtype,
            'schedule_type': sched,
            'schedule_day': sday,
            'recipient_emails': recipients,
            'is_active': True,
            'export_formats': ['pdf'],
            'include_charts': True,
            'include_summary': True,
            'schedule_time': dtime(7, 0, 0),
        }
    )

print("Scheduled reports: seeded.")

print("\n✓ All demo data seeded successfully!")
print(f"  Property: {prop.name}")
print(f"  Rooms: {Room.objects.count()}")
print(f"  Guests: {Guest.objects.count()}")
print(f"  Bookings: {Booking.objects.count()}")
print(f"  OccupancyForecasts: {OccupancyForecast.objects.count()}")
print(f"  RevenueForecasts: {RevenueForecast.objects.count()}")
print(f"  CancellationPredictions: {CancellationPrediction.objects.count()}")
print(f"  NoShowPredictions: {NoShowPrediction.objects.count()}")
print(f"  CustomReports: {CustomReport.objects.count()}")
print(f"  ScheduledReports: {ScheduledReport.objects.count()}")
print(f"\nLogin at http://localhost:8000/login/ with admin / admin123")
