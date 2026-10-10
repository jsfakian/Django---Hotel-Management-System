from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import Http404, HttpResponse
from django.apps import apps
from django.db.models import Sum
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.forms import modelform_factory
from django.contrib import messages
from django.db import IntegrityError

# Import specific forms and services
from payments.forms import InvoiceForm
from payments.mydata_service import get_mydata_service


def _user_role(user):
    group = user.groups.first()
    return group.name if group else 'user'


def _is_travel_agent(user):
    """Check if user is a travel agent"""
    return user.groups.filter(name='travel_agent').exists()


def _get_travel_agent_profile(user):
    """Get travel agent profile if user is a travel agent"""
    if not _is_travel_agent(user):
        return None
    try:
        return user.travel_agent_profile
    except:
        return None


def _can_access_property(user, property_obj):
    """Check if user can access a property (for booking operations)"""
    # Staff users can access their own property or any property
    if user.groups.filter(name='hotel_manager').exists() or user.is_staff:
        return True
    
    # Travel agents can only access properties they have active contracts for
    agent_profile = _get_travel_agent_profile(user)
    if agent_profile:
        from datetime import date
        from contracts.models import Contract
        today = date.today()
        return Contract.objects.filter(
            travel_agency=agent_profile.travel_agency,
            property=property_obj,
            status='active',
            start_date__lte=today,
            end_date__gte=today
        ).exists()
    
    return False


def _create_booking_notification(booking, created_by_travel_agent=False):
    """Create staff notifications when a booking is created by travel agent"""
    if not created_by_travel_agent:
        return
    
    from notifications.models import Notification
    from accounts.models import Employee
    
    # Get all staff at the property
    property_staff = Employee.objects.filter(
        property=booking.room.property,
        status='active'
    ).select_related('user')
    
    # Create notification for each staff member
    for staff in property_staff:
        if staff.user:
            booking_source = booking.get_booking_source_display()
            if booking.travel_agency:
                message = f"New booking created by {booking.travel_agency.name} for Room {booking.room.room_number}"
            else:
                message = f"New booking from {booking_source} for Room {booking.room.room_number}"
            
            from notifications.models import NotificationType

            ntype = NotificationType.objects.filter(code='booking_created').first()
            if not ntype:
                continue
            Notification.objects.create(
                user=staff.user,
                notification_type=ntype,
                title='New Booking',
                message=message,
                priority='high',
            )


MODULE_CATALOG = {
    'users': {
        'title': 'Users',
        'description': 'Manage and inspect platform users and identity records.',
        'workspace_url': '/admin/auth/user/',
    },
    'rooms': {
        'title': 'Rooms',
        'description': 'Room inventory, rates, and availability operations.',
        'workspace_url': '/admin/room/room/',
    },
    'bookings': {
        'title': 'Bookings',
        'description': 'Track reservations and booking lifecycle events.',
        'workspace_url': '/admin/room/booking/',
    },
    'guests': {
        'title': 'Guests',
        'description': 'Guest profiles, contact data, and preferences.',
        'workspace_url': '/admin/accounts/guest/',
    },
    'properties': {
        'title': 'Properties',
        'description': 'Hotel properties, locations, and infrastructure management.',
        'workspace_url': '/admin/properties/property/',
    },
    'travel-agencies': {
        'title': 'Travel Agencies',
        'description': 'Third-party travel agency partnerships and commission management.',
        'workspace_url': '/properties/travel-agencies/',
    },
    'payments': {
        'title': 'Payments',
        'description': 'Payment transactions, settlement, and status tracking.',
        'workspace_url': '/payments/history/',
    },
    'invoices': {
        'title': 'Invoices',
        'description': 'Invoice generation, review, and lifecycle status.',
        'workspace_url': '/payments/invoices/',
    },
    'contracts': {
        'title': 'Contracts',
        'description': 'Contract creation, signature flow, and retrieval.',
        'workspace_url': '/contracts/',  # now renders contracts.html instead of JSON
    },
    'pricing': {
        'title': 'Pricing',
        'description': 'Dynamic pricing signals and intelligent rate hints.',
        'workspace_url': '/admin/room/room/',
    },
    'tasks': {
        'title': 'Tasks',
        'description': 'Operational task visibility for staff workflows.',
        'workspace_url': '/admin/accounts/task/',
    },
    'notifications': {
        'title': 'Notifications',
        'description': 'Alert center, status monitoring, and preference controls.',
        'workspace_url': '/notifications/',
    },
    'business-intelligence': {
        'title': 'Business Intelligence',
        'description': 'Executive and operational analytics with reporting.',
        'workspace_url': '/admin/analytics/customreport/',
    },
    'forecast': {
        'title': 'Forecast',
        'description': 'Occupancy, revenue, cancellation, and no-show forecasts.',
        'workspace_url': '/admin/analytics/occupancyforecast/',
    },
}


PORTAL_ORDER = [
    'users', 'rooms', 'bookings', 'guests', 'properties', 'travel-agencies', 'payments', 'invoices',
    'contracts', 'pricing', 'tasks', 'notifications', 'business-intelligence', 'forecast'
]

CRUD_ACTIONS = ('create', 'read', 'update', 'delete')

MODULE_MODEL_MAP = {
    'users': ('auth', 'User'),
    'rooms': ('room', 'Room'),
    'bookings': ('room', 'Booking'),
    'guests': ('accounts', 'Guest'),
    'properties': ('properties', 'Property'),
    'travel-agencies': ('properties', 'TravelAgency'),
    'payments': ('payments', 'Payment'),
    'invoices': ('payments', 'Invoice'),
    'contracts': ('contracts', 'Contract'),
    'pricing': ('room', 'Room'),
    'tasks': ('accounts', 'Task'),
    'notifications': ('notifications', 'Notification'),
    'business-intelligence': ('analytics', 'CustomReport'),
    'forecast': ('analytics', 'OccupancyForecast'),
}

MODULE_FIELD_CONFIG = {
    'users': {
        'fields': ['username', 'first_name', 'last_name', 'email', 'is_active'],
        'columns': ['id', 'username', 'email', 'is_active', 'date_joined'],
    },
    'rooms': {
        'fields': ['room_number', 'floor', 'room_type', 'capacity', 'number_of_beds', 'base_price', 'current_price', 'status', 'property'],
        'columns': ['id', 'room_number', 'property', 'room_type', 'status'],
    },
    'bookings': {
        'fields': ['room', 'guest', 'check_in_date', 'check_out_date', 'number_of_guests', 'status', 'base_price', 'actual_price', 'travel_agency', 'booking_source', 'notes'],
        'columns': ['id', 'room', 'guest', 'check_in_date', 'check_out_date', 'status'],
    },
    'guests': {
        'fields': ['user', 'email', 'first_name', 'last_name', 'phone_number', 'city', 'country'],
        'columns': ['id', 'first_name', 'last_name', 'email', 'city', 'country'],
    },
    'properties': {
        'fields': ['name', 'location', 'city', 'country', 'total_rooms', 'star_rating', 'manager', 'email', 'phone_number', 'is_active'],
        'columns': ['id', 'name', 'location', 'city', 'star_rating', 'total_rooms'],
    },
    'travel-agencies': {
        'fields': ['name', 'contact_name', 'email', 'phone', 'city', 'country', 'commission_percentage', 'status'],
        'columns': ['id', 'name', 'contact_name', 'email', 'city', 'status'],
    },
    'payments': {
        'fields': ['guest', 'booking', 'payment_method', 'amount', 'currency', 'status', 'description', 'notes'],
        'columns': ['id', 'guest', 'amount', 'currency', 'status', 'created_at'],
    },
    'invoices': {
        'fields': ['guest', 'payment', 'booking', 'amount', 'tax_amount', 'total_amount', 'status', 'description', 'due_date', 'notes', 'mydata_transmitted', 'mydata_transmission_id'],
        'columns': ['id', 'invoice_number', 'guest', 'total_amount', 'status', 'due_date', 'mydata_transmitted'],
    },
    'contracts': {
        'fields': ['property', 'travel_agency', 'contract_type', 'commission_percentage', 'start_date', 'end_date', 'status', 'payment_terms', 'cancellation_policy', 'special_terms'],
        'columns': ['id', 'property', 'travel_agency', 'contract_type', 'status', 'end_date'],
    },
    'pricing': {
        'fields': ['room_number', 'room_type', 'base_price', 'current_price', 'status', 'property'],
        'columns': ['id', 'room_number', 'room_type', 'base_price', 'current_price', 'status'],
    },
    'tasks': {
        'fields': ['employee', 'title', 'description', 'start_time', 'end_time', 'status', 'priority', 'booking', 'property'],
        'columns': ['id', 'title', 'employee', 'priority', 'status', 'start_time'],
    },
    'notifications': {
        'fields': ['user', 'notification_type', 'title', 'message', 'status', 'priority', 'action_url', 'action_label'],
        'columns': ['id', 'user', 'title', 'status', 'priority', 'created_at'],
    },
    'business-intelligence': {
        'fields': ['property', 'name', 'description', 'report_type', 'from_date', 'to_date', 'include_charts', 'include_summary', 'include_detailed_data', 'export_format', 'status'],
        'columns': ['id', 'property', 'name', 'report_type', 'status', 'created_at'],
    },
    'forecast': {
        'fields': ['property', 'forecast_date', 'target_date', 'predicted_occupancy', 'lower_bound', 'upper_bound', 'model_type', 'actual_occupancy'],
        'columns': ['id', 'property', 'forecast_date', 'target_date', 'predicted_occupancy', 'model_type'],
    },
}

EXCLUDED_EDIT_FIELDS = {
    'id', 'created_at', 'updated_at', 'processed_at', 'generated_at', 'read_at',
    'email_sent_at', 'email_opened_at', 'last_generated_at', 'next_scheduled_at',
    'property_manager_signed_at', 'travel_agency_signed_at', 'prediction_time',
    'verification_sent_at', 'verification_verified_at', 'paid_date',
    'mydata_transmission_date', 'mydata_qr_code', 'mydata_cancel_date'  # MyData readonly fields
}

CRUD_OPERATIONS = {
    'users': {
        'create': '/admin/auth/user/add/',
        'read': '/admin/auth/user/',
        'update': '/admin/auth/user/',
        'delete': '/admin/auth/user/',
    },
    'rooms': {
        'create': '/admin/room/room/add/',
        'read': '/admin/room/room/',
        'update': '/admin/room/room/',
        'delete': '/admin/room/room/',
    },
    'bookings': {
        'create': '/admin/room/booking/add/',
        'read': '/admin/room/booking/',
        'update': '/admin/room/booking/',
        'delete': '/admin/room/booking/',
    },
    'guests': {
        'create': '/admin/accounts/guest/add/',
        'read': '/admin/accounts/guest/',
        'update': '/admin/accounts/guest/',
        'delete': '/admin/accounts/guest/',
    },
    'properties': {
        'create': '/admin/properties/property/add/',
        'read': '/admin/properties/property/',
        'update': '/admin/properties/property/',
        'delete': '/admin/properties/property/',
    },
    'travel-agencies': {
        'create': '/admin/properties/travelagency/add/',
        'read': '/admin/properties/travelagency/',
        'update': '/admin/properties/travelagency/',
        'delete': '/admin/properties/travelagency/',
    },
    'payments': {
        'read': '/payments/history/',
    },
    'invoices': {
        'create': '/admin/payments/invoice/add/',
        'read': '/payments/invoices/',
        'update': '/admin/payments/invoice/',
        'delete': '/admin/payments/invoice/',
    },
    'contracts': {
        'create': '/admin/contracts/contract/add/',
        'read': '/contracts/',
        'update': '/admin/contracts/contract/',
        'delete': '/admin/contracts/contract/',
    },
    'pricing': {
        'create': '/admin/room/room/add/',
        'read': '/admin/room/room/',
        'update': '/admin/room/room/',
        'delete': '/admin/room/room/',
    },
    'tasks': {
        'create': '/admin/accounts/task/add/',
        'read': '/admin/accounts/task/',
        'update': '/admin/accounts/task/',
        'delete': '/admin/accounts/task/',
    },
    'notifications': {
        'create': '/admin/notifications/notification/add/',
        'read': '/notifications/',
        'update': '/admin/notifications/notification/',
        'delete': '/admin/notifications/notification/',
    },
    'business-intelligence': {
        'create': '/admin/analytics/customreport/add/',
        'read': '/admin/analytics/customreport/',
        'update': '/admin/analytics/customreport/',
        'delete': '/admin/analytics/customreport/',
    },
    'forecast': {
        'create': '/admin/analytics/occupancyforecast/add/',
        'read': '/admin/analytics/occupancyforecast/',
        'update': '/admin/analytics/occupancyforecast/',
        'delete': '/admin/analytics/occupancyforecast/',
    },
}


def _crud_target(module_key, action):
    return CRUD_OPERATIONS.get(module_key, {}).get(action, '/home/')

def _crud_target(module_key, action):
    targets = {
        'users': {
            'create': '/admin/auth/user/add/',
            'read': '/admin/auth/user/',
            'update': '/admin/auth/user/',
            'delete': '/admin/auth/user/',
        },
        'rooms': {
            'create': '/admin/room/room/add/',
            'read': '/admin/room/room/',
            'update': '/admin/room/room/',
            'delete': '/admin/room/room/',
        },
        'bookings': {
            'create': '/admin/room/booking/add/',
            'read': '/admin/room/booking/',
            'update': '/admin/room/booking/',
            'delete': '/admin/room/booking/',
        },
        'guests': {
            'create': '/admin/accounts/guest/add/',
            'read': '/admin/accounts/guest/',
            'update': '/admin/accounts/guest/',
            'delete': '/admin/accounts/guest/',
        },
        'properties': {
            'create': '/admin/properties/property/add/',
            'read': '/admin/properties/property/',
            'update': '/admin/properties/property/',
            'delete': '/admin/properties/property/',
        },
        'travel-agencies': {
            'create': '/admin/properties/travelagency/add/',
            'read': '/admin/properties/travelagency/',
            'update': '/admin/properties/travelagency/',
            'delete': '/admin/properties/travelagency/',
        },
        'payments': {
            'create': '/payments/process/',
            'read': '/payments/history/',
            'update': '/admin/payments/payment/',
            'delete': '/admin/payments/payment/',
        },
        'invoices': {
            'create': '/admin/payments/invoice/add/',
            'read': '/payments/invoices/',
            'update': '/admin/payments/invoice/',
            'delete': '/admin/payments/invoice/',
        },
        'contracts': {
            'create': '/admin/contracts/contract/add/',
            'read': '/contracts/',
            'update': '/admin/contracts/contract/',
            'delete': '/admin/contracts/contract/',
        },
        'pricing': {
            'create': '/admin/room/room/add/',
            'read': '/admin/room/room/',
            'update': '/admin/room/room/',
            'delete': '/admin/room/room/',
        },
        'tasks': {
            'create': '/admin/accounts/task/add/',
            'read': '/admin/accounts/task/',
            'update': '/admin/accounts/task/',
            'delete': '/admin/accounts/task/',
        },
        'notifications': {
            'create': '/admin/notifications/notification/add/',
            'read': '/notifications/',
            'update': '/admin/notifications/notification/',
            'delete': '/admin/notifications/notification/',
        },
        'business-intelligence': {
            'create': '/admin/analytics/customreport/add/',
            'read': '/admin/analytics/customreport/',
            'update': '/admin/analytics/customreport/',
            'delete': '/admin/analytics/customreport/',
        },
        'forecast': {
            'create': '/admin/analytics/occupancyforecast/add/',
            'read': '/admin/analytics/occupancyforecast/',
            'update': '/admin/analytics/occupancyforecast/',
            'delete': '/admin/analytics/occupancyforecast/',
        },
    }
    return targets.get(module_key, {}).get(action, '/home/')


def _model_for_module(module_key):
    model_ref = MODULE_MODEL_MAP.get(module_key)
    if not model_ref:
        return None
    app_label, model_name = model_ref
    try:
        return apps.get_model(app_label, model_name)
    except Exception:
        return None


def _editable_fields(model):
    fields = []
    for field in model._meta.get_fields():
        if not getattr(field, 'editable', False):
            continue
        if getattr(field, 'auto_created', False):
            continue
        if getattr(field, 'many_to_many', False):
            continue
        if field.name in EXCLUDED_EDIT_FIELDS:
            continue
        fields.append(field.name)
    return fields


def _configured_fields(model, module_key):
    configured = MODULE_FIELD_CONFIG.get(module_key, {}).get('fields', [])
    if not configured:
        return _editable_fields(model)
    model_fields = {field.name for field in model._meta.get_fields()}
    filtered = [name for name in configured if name in model_fields]
    return filtered if filtered else _editable_fields(model)


def _table_columns(model):
    candidates = []
    for field in model._meta.get_fields():
        if getattr(field, 'many_to_many', False):
            continue
        if getattr(field, 'auto_created', False):
            continue
        if field.name in {'password'}:
            continue
        candidates.append(field.name)
    preferred = ['id', 'username', 'email', 'status', 'created_at', 'updated_at', 'name', 'title']
    ordered = [c for c in preferred if c in candidates] + [c for c in candidates if c not in preferred]
    return ordered[:6]


def _configured_columns(model, module_key):
    configured = MODULE_FIELD_CONFIG.get(module_key, {}).get('columns', [])
    if not configured:
        return _table_columns(model)
    model_fields = {field.name for field in model._meta.get_fields()}
    filtered = [name for name in configured if name in model_fields]
    return filtered if filtered else _table_columns(model)


def _style_form_fields(form):
    for name, field in form.fields.items():
        widget = field.widget
        existing = widget.attrs.get('class', '')
        if widget.__class__.__name__.lower().startswith('checkbox'):
            widget.attrs['class'] = (existing + ' form-check-input').strip()
        elif widget.__class__.__name__.lower().startswith('select'):
            widget.attrs['class'] = (existing + ' custom-select').strip()
        else:
            widget.attrs['class'] = (existing + ' form-control').strip()


def _build_rows(queryset, columns):
    rows = []
    for obj in queryset:
        values = []
        for col in columns:
            value = getattr(obj, col, '')
            values.append(str(value) if value is not None else '-')
        rows.append({'pk': obj.pk, 'values': values, 'object': obj})
    return rows


def _count(app_label, model_name, **filters):
    try:
        model = apps.get_model(app_label, model_name)
        if not model:
            return 0
        return model.objects.filter(**filters).count()
    except Exception:
        return 0


def _sum(app_label, model_name, field_name, **filters):
    try:
        model = apps.get_model(app_label, model_name)
        if not model:
            return 0
        value = model.objects.filter(**filters).aggregate(total=Sum(field_name)).get('total')
        return float(value) if value else 0
    except Exception:
        return 0


def _kpi_spec(label, app_label, model_name, **filters):
    return (label, lambda: _count(app_label, model_name, **filters))


def _static_kpi(label, value):
    return (label, lambda: value)


def _revenue_kpi():
    return (
        'Revenue (€)',
        lambda: f"{_sum('payments', 'Payment', 'amount', status='completed'):.2f}",
    )


_MODULE_KPI_SPECS = {
    'users': [
        _kpi_spec('Total users', 'auth', 'User'),
        _kpi_spec('Staff users', 'auth', 'User', is_staff=True),
        _kpi_spec('Active users', 'auth', 'User', is_active=True),
    ],
    'rooms': [
        _kpi_spec('Total rooms', 'room', 'Room'),
        _kpi_spec('Available', 'room', 'Room', status='available'),
        _kpi_spec('Occupied', 'room', 'Room', status='occupied'),
    ],
    'bookings': [
        _kpi_spec('Total bookings', 'room', 'Booking'),
        _kpi_spec('Pending', 'room', 'Booking', status='pending'),
        _kpi_spec('Confirmed', 'room', 'Booking', status='confirmed'),
    ],
    'guests': [
        _kpi_spec('Total guests', 'accounts', 'Guest'),
        _kpi_spec('Employee profiles', 'accounts', 'Employee'),
        _kpi_spec('Travel agencies', 'properties', 'TravelAgency'),
    ],
    'properties': [
        _kpi_spec('Total properties', 'properties', 'Property'),
        _kpi_spec('Active', 'properties', 'Property', is_active=True),
        _static_kpi('Avg rooms', 'View details'),
    ],
    'travel-agencies': [
        _kpi_spec('Total agencies', 'properties', 'TravelAgency'),
        _kpi_spec('Active', 'properties', 'TravelAgency', status='active'),
        _static_kpi('Avg commission %', '10%'),
    ],
    'payments': [
        _kpi_spec('Total payments', 'payments', 'Payment'),
        _kpi_spec('Completed', 'payments', 'Payment', status='completed'),
        _revenue_kpi(),
    ],
    'invoices': [
        _kpi_spec('Total invoices', 'payments', 'Invoice'),
        _kpi_spec('Paid', 'payments', 'Invoice', status='paid'),
        _kpi_spec('Issued', 'payments', 'Invoice', status='issued'),
    ],
    'contracts': [
        _kpi_spec('Total contracts', 'contracts', 'Contract'),
        _kpi_spec('Active', 'contracts', 'Contract', status='active'),
        _kpi_spec('Pending', 'contracts', 'Contract', status='pending'),
    ],
    'pricing': [
        _kpi_spec('Room pricing items', 'room', 'Room'),
        _kpi_spec('Revenue metric rows', 'analytics', 'DashboardRevenueMetrics'),
        _static_kpi('Dynamic endpoint', 'Enabled'),
    ],
    'tasks': [
        _kpi_spec('Total tasks', 'accounts', 'Task'),
        _kpi_spec('Pending', 'accounts', 'Task', status='pending'),
        _kpi_spec('In progress', 'accounts', 'Task', status='in_progress'),
    ],
    'notifications': [
        _kpi_spec('Total notifications', 'notifications', 'Notification'),
        _kpi_spec('Unread', 'notifications', 'Notification', status='unread'),
        _kpi_spec('Preferences', 'notifications', 'NotificationPreference'),
    ],
    'business-intelligence': [
        _kpi_spec('Executive metrics', 'analytics', 'DashboardExecutiveMetrics'),
        _kpi_spec('Operational snapshots', 'analytics', 'DashboardOperationalStatus'),
        _kpi_spec('Custom reports', 'analytics', 'CustomReport'),
    ],
    'forecast': [
        _kpi_spec('Occupancy forecasts', 'analytics', 'OccupancyForecast'),
        _kpi_spec('Revenue forecasts', 'analytics', 'RevenueForecast'),
        _kpi_spec('Cancellation predictions', 'analytics', 'CancellationPrediction'),
    ],
}


def _module_kpis(module_key):
    return [
        {'label': label, 'value': value_fn()}
        for label, value_fn in _MODULE_KPI_SPECS.get(module_key, [])
    ]


def _daily_count_series(app_label, model_name, datetime_field, days=7):
    series = [0] * days
    try:
        model = apps.get_model(app_label, model_name)
        if not model:
            return series
        start_day = timezone.now().date() - timedelta(days=days - 1)
        queryset = (
            model.objects
            .filter(**{f'{datetime_field}__date__gte': start_day})
            .annotate(day=TruncDate(datetime_field))
            .values('day')
            .order_by('day')
        )
        day_map = {}
        for row in queryset:
            key = row['day']
            day_map[key] = day_map.get(key, 0) + 1

        for i in range(days):
            day = start_day + timedelta(days=i)
            series[i] = int(day_map.get(day, 0))
    except Exception:
        pass
    return series


def _daily_sum_series(app_label, model_name, datetime_field, amount_field, days=7):
    series = [0.0] * days
    try:
        model = apps.get_model(app_label, model_name)
        if not model:
            return series
        start_day = timezone.now().date() - timedelta(days=days - 1)
        queryset = (
            model.objects
            .filter(**{f'{datetime_field}__date__gte': start_day})
            .annotate(day=TruncDate(datetime_field))
            .values('day')
            .annotate(total=Sum(amount_field))
            .order_by('day')
        )
        day_map = {row['day']: float(row['total'] or 0) for row in queryset}
        for i in range(days):
            day = start_day + timedelta(days=i)
            series[i] = round(day_map.get(day, 0.0), 2)
    except Exception:
        pass
    return series


def _fill_forecast_series(series, key, model, days, date_field, value_field, since):
    if not model:
        return
    queryset = (
        model.objects.filter(**{f'{date_field}__gte': since})
        .order_by(date_field)[:days]
    )
    values = [float(getattr(row, value_field) or 0) for row in queryset]
    series[key][:len(values)] = values


def _forecast_series(days=7):
    today = timezone.now().date()
    series = {'occupancy': [0.0] * days, 'revenue': [0.0] * days, 'cancel': [0.0] * days}
    try:
        occupancy_model = apps.get_model('analytics', 'OccupancyForecast')
        revenue_model = apps.get_model('analytics', 'RevenueForecast')
        cancellation_model = apps.get_model('analytics', 'CancellationPrediction')

        _fill_forecast_series(
            series, 'occupancy', occupancy_model, days,
            'target_date', 'predicted_occupancy', today,
        )
        _fill_forecast_series(
            series, 'revenue', revenue_model, days,
            'target_date', 'predicted_revenue', today,
        )
        _fill_forecast_series(
            series, 'cancel', cancellation_model, days,
            'prediction_date', 'cancellation_risk_score',
            today - timedelta(days=days - 1),
        )
    except Exception:
        pass

    return series


def _module_trends(module_key):
    if module_key == 'bookings':
        return [
            {'label': '7-day bookings', 'series': _daily_count_series('room', 'Booking', 'created_at', 7)},
        ]
    if module_key == 'payments':
        return [
            {'label': '7-day payment volume', 'series': _daily_count_series('payments', 'Payment', 'created_at', 7)},
            {'label': '7-day paid revenue', 'series': _daily_sum_series('payments', 'Payment', 'created_at', 'amount', 7)},
        ]
    if module_key == 'forecast':
        forecast = _forecast_series(7)
        return [
            {'label': 'Occupancy forecast %', 'series': forecast['occupancy']},
            {'label': 'Revenue forecast', 'series': forecast['revenue']},
            {'label': 'Cancellation risk %', 'series': forecast['cancel']},
        ]
    return []


def landing_page(request):
    return render(request, 'landing.html')


@login_required(login_url='login')
def home_page(request):
    role = _user_role(request.user)

    role_menus = []
    for key in PORTAL_ORDER:
        module_kpis = _module_kpis(key)
        role_menus.append(
            {
                'label': MODULE_CATALOG[key]['title'],
                'href': f'/portal/{key}/',
                'desc': MODULE_CATALOG[key]['description'],
                'count': module_kpis[0]['value'] if module_kpis else '',
            }
        )

    return render(request, 'role-dashboard.html', {
        'role': role,
        'menu_items': role_menus,
    })


@login_required(login_url='login')
def module_portal(request, module_key):
    module = MODULE_CATALOG.get(module_key)
    if not module:
        raise Http404('Module not found')

    model = _model_for_module(module_key)
    list_columns = []
    module_items = []
    if model:
        list_columns = _configured_columns(model, module_key)[:5]
        queryset = model.objects.all()
        
        # Travel agents can only see bookings from properties they have contracts for
        if module_key == 'bookings' and _is_travel_agent(request.user):
            agent_profile = _get_travel_agent_profile(request.user)
            if agent_profile:
                property_ids = agent_profile.get_accessible_properties()
                queryset = queryset.filter(room__property_id__in=property_ids)
        
        order_by_field = '-id' if 'id' in [f.name for f in model._meta.fields] else model._meta.pk.name
        queryset = queryset.order_by(order_by_field)[:20]
        module_items = _build_rows(queryset, list_columns)

    return render(request, 'module-portal.html', {
        'page_title': module['title'],
        'role': _user_role(request.user),
        'module_key': module_key,
        'module': module,
        'kpis': _module_kpis(module_key),
        'trends': _module_trends(module_key),
        'list_columns': list_columns,
        'module_items': module_items,
        'portal_order': [
            {'key': key, 'title': MODULE_CATALOG[key]['title']}
            for key in PORTAL_ORDER
        ],
        'available_actions': list(CRUD_OPERATIONS.get(module_key, {}).keys()),
    })


def _crud_access_denied(request):
    from accounts.permissions import get_user_role
    from django.http import HttpResponseForbidden

    role = get_user_role(request.user)
    if role not in ('admin', 'manager', 'receptionist') and not request.user.is_superuser:
        return HttpResponseForbidden('Staff access required for portal CRUD.')
    return None


def _crud_form_class(model, module_key):
    editable_fields = _configured_fields(model, module_key)

    # Use specific form for invoices, otherwise use dynamic form
    if module_key == 'invoices':
        return InvoiceForm
    return modelform_factory(model, fields=editable_fields if editable_fields else [])


def _add_integrity_error(form, exc):
    """Translate a duplicate-key IntegrityError into form errors."""
    error_msg = str(exc).lower()
    if 'username' in error_msg:
        form.add_error('username', 'A user with this username already exists.')
    elif 'unique' not in error_msg:
        form.add_error(None, f'Database error: {str(exc)}')
    elif 'email' in error_msg:
        form.add_error('email', 'A user with this email already exists.')
    else:
        form.add_error(None, 'This record already exists. Please use different values.')
    _style_form_fields(form)


def _transmit_invoice_to_mydata(request, instance, verb, skip_if_transmitted=False):
    """Validate and transmit an invoice to MyData, reporting via messages."""
    try:
        if skip_if_transmitted and instance.mydata_transmitted:
            messages.warning(request, 'Invoice already transmitted to MyData.')
            return
        mydata_service = get_mydata_service()
        # Validate invoice before transmission
        is_valid, validation_errors = mydata_service.validate_invoice_for_transmission(instance)
        if not is_valid:
            messages.warning(
                request,
                f'Invoice {verb}. MyData transmission skipped: {", ".join(validation_errors)}',
            )
            return
        success, result = mydata_service.transmit_invoice(instance)
        if success:
            messages.success(
                request, f'Invoice {verb} and transmitted to MyData (ID: {result}).'
            )
        else:
            messages.warning(
                request, f'Invoice {verb} but MyData transmission failed: {result}'
            )
    except Exception as e:
        messages.warning(request, f'Invoice {verb}. MyData transmission error: {str(e)}')


def _report_save_success(request, form, instance, module_key, module, verb,
                         skip_if_transmitted=False):
    if module_key == 'invoices' and form.cleaned_data.get('transmit_to_mydata'):
        _transmit_invoice_to_mydata(
            request, instance, verb, skip_if_transmitted=skip_if_transmitted
        )
    else:
        messages.success(request, f'{module["title"]} record {verb} successfully.')


def _crud_success_response(module_key, panel_mode):
    if panel_mode:
        return HttpResponse(status=204)  # No content, triggers reload in panel
    return redirect(f'/portal/{module_key}/read/')


def _booking_access_denied_response(request, form, module_key, module, panel_mode):
    """Handle a travel agent creating a booking for an inaccessible property.

    Returns a rendered response, or None to fall through to the main page render.
    """
    form.add_error(None, 'You do not have access to create bookings for this property.')
    _style_form_fields(form)
    if panel_mode:
        return None
    return render(request, 'module-crud.html', {
        'action': 'create',
        'action_title': 'Create',
        'module_key': module_key,
        'module': module,
        'form': form,
        'panel_mode': panel_mode,
    })


def _save_created_record(request, form, module_key, module, panel_mode):
    """Persist a created record. Returns a response, or None to re-render the form."""
    instance = form.save(commit=False)

    agent_profile = None
    if module_key == 'bookings' and _is_travel_agent(request.user):
        agent_profile = _get_travel_agent_profile(request.user)
    if agent_profile:
        if not _can_access_property(request.user, instance.room.property):
            return _booking_access_denied_response(
                request, form, module_key, module, panel_mode
            )
        # Auto-set travel agency
        instance.travel_agency = agent_profile.travel_agency

    instance.save()
    _report_save_success(request, form, instance, module_key, module, 'created')

    # Create notifications for staff if travel agent created booking
    if module_key == 'bookings' and _is_travel_agent(request.user):
        _create_booking_notification(instance, created_by_travel_agent=True)

    return _crud_success_response(module_key, panel_mode)


def _crud_create(request, module_key, module, dynamic_form, panel_mode):
    """Handle the create action. Returns (form, response)."""
    if request.method != 'POST':
        form = dynamic_form()
        _style_form_fields(form)
        return form, None

    form = dynamic_form(request.POST)
    _style_form_fields(form)
    if not form.is_valid():
        return form, None
    try:
        response = _save_created_record(request, form, module_key, module, panel_mode)
    except IntegrityError as e:
        _add_integrity_error(form, e)
        return form, None
    return form, response


def _crud_update(request, module_key, module, dynamic_form, instance, panel_mode):
    """Handle the update action. Returns (form, response)."""
    if request.method != 'POST':
        form = dynamic_form(instance=instance)
        _style_form_fields(form)
        return form, None

    form = dynamic_form(request.POST, instance=instance)
    _style_form_fields(form)
    if not form.is_valid():
        return form, None
    try:
        form.save()
        _report_save_success(
            request, form, instance, module_key, module, 'updated',
            skip_if_transmitted=True,
        )
        return form, _crud_success_response(module_key, panel_mode)
    except IntegrityError as e:
        _add_integrity_error(form, e)
        return form, None


def _crud_delete(request, module_key, module, instance, panel_mode):
    instance.delete()
    messages.success(request, f'{module["title"]} record deleted successfully.')
    return _crud_success_response(module_key, panel_mode)


def _crud_load_instance(model, action, pk):
    if action == 'view' and pk is None:
        raise Http404('Record not found')
    if action in ('view', 'update', 'delete') and pk is not None:
        return get_object_or_404(model, pk=pk)
    return None


def _crud_detail_rows(instance, columns):
    rows = []
    for field_name in columns:
        value = getattr(instance, field_name, None)
        rows.append({
            'label': field_name.replace('_', ' ').title(),
            'value': str(value) if value is not None else '-',
        })
    return rows


def _crud_render_page(request, model, module_key, module, action, form, instance,
                      panel_mode):
    columns = _configured_columns(model, module_key)
    detail_rows = []
    if action == 'view' and instance is not None:
        detail_rows = _crud_detail_rows(instance, columns)

    queryset = model.objects.all()
    order_by_field = '-id' if 'id' in [f.name for f in model._meta.fields] else model._meta.pk.name
    queryset = queryset.order_by(order_by_field)[:30]

    return render(request, 'module-crud.html', {
        'role': _user_role(request.user),
        'module_key': module_key,
        'module': module,
        'action': action,
        'action_title': action.title(),
        'action_target_url': _crud_target(module_key, action),
        'crud_actions': CRUD_ACTIONS,
        'form': form,
        'columns': columns,
        'detail_rows': detail_rows,
        'rows': _build_rows(queryset, columns),
        'instance': instance,
        'panel_mode': panel_mode,
    })


def _crud_dispatch(request, model, module_key, module, action, pk, panel_mode):
    """Run the action handler. Returns (form, instance, response)."""
    dynamic_form = _crud_form_class(model, module_key)

    if action == 'create':
        form, response = _crud_create(request, module_key, module, dynamic_form, panel_mode)
        return form, None, response

    instance = _crud_load_instance(model, action, pk)
    if action == 'update' and pk is not None:
        form, response = _crud_update(
            request, module_key, module, dynamic_form, instance, panel_mode
        )
        return form, instance, response

    if action == 'delete' and pk is not None and request.method == 'POST':
        return None, instance, _crud_delete(request, module_key, module, instance, panel_mode)
    return None, instance, None


@login_required(login_url='login')
def module_crud_page(request, module_key, action, pk=None):
    denied = _crud_access_denied(request)
    if denied is not None:
        return denied

    module = MODULE_CATALOG.get(module_key)
    if not module or action not in (*CRUD_ACTIONS, 'view'):
        raise Http404('Module action not found')

    panel_mode = request.GET.get('panel') == '1'

    model = _model_for_module(module_key)
    if not model:
        messages.warning(request, 'Model binding for this module is not available. Redirected to workspace link.')
        return redirect(module['workspace_url'])

    form, instance, response = _crud_dispatch(
        request, model, module_key, module, action, pk, panel_mode
    )
    if response is not None:
        return response
    return _crud_render_page(
        request, model, module_key, module, action, form, instance, panel_mode
    )


@login_required(login_url='login')
def backend_navigation(request):
    endpoint_groups = [
        {
            'title': 'Core System',
            'items': [
                {'label': 'Health Check', 'method': 'GET', 'path': '/healthz/'},
                {'label': 'Django Admin', 'method': 'GET', 'path': '/admin/'},
                {'label': 'OpenAPI Schema', 'method': 'GET', 'path': '/api/v1/schema/'},
                {'label': 'Swagger UI', 'method': 'GET', 'path': '/api/v1/docs/swagger/'},
            ],
        },
        {
            'title': 'Authentication API',
            'items': [
                {'label': 'Login', 'method': 'POST', 'path': '/api/v1/auth/login/'},
                {'label': 'Refresh Token', 'method': 'POST', 'path': '/api/v1/auth/refresh/'},
                {'label': 'Logout', 'method': 'POST', 'path': '/api/v1/auth/logout/'},
                {'label': 'Register', 'method': 'POST', 'path': '/api/v1/auth/register/'},
                {'label': 'Forgot Password', 'method': 'POST', 'path': '/api/v1/auth/forgot-password/'},
            ],
        },
        {
            'title': 'REST Resources',
            'items': [
                {'label': 'Users', 'method': 'GET', 'path': '/api/v1/users/'},
                {'label': 'Guests', 'method': 'GET', 'path': '/api/v1/guests/'},
                {'label': 'Employees', 'method': 'GET', 'path': '/api/v1/employees/'},
                {'label': 'Properties', 'method': 'GET', 'path': '/api/v1/properties/'},
                {'label': 'Travel Agencies', 'method': 'GET', 'path': '/api/v1/travel-agencies/'},
                {'label': 'Rooms', 'method': 'GET', 'path': '/api/v1/rooms/'},
                {'label': 'Bookings', 'method': 'GET', 'path': '/api/v1/bookings/'},
                {'label': 'Contracts', 'method': 'GET', 'path': '/api/v1/contracts/'},
                {'label': 'Payments', 'method': 'GET', 'path': '/api/v1/payments/'},
                {'label': 'Invoices', 'method': 'GET', 'path': '/api/v1/invoices/'},
                {'label': 'Refund Requests', 'method': 'GET', 'path': '/api/v1/refund-requests/'},
                {'label': 'Notifications', 'method': 'GET', 'path': '/api/v1/notifications/'},
            ],
        },
        {
            'title': 'Analytics API',
            'items': [
                {'label': 'Executive Dashboard', 'method': 'GET', 'path': '/api/v1/analytics/executive-dashboard/'},
                {'label': 'Operational Dashboard', 'method': 'GET', 'path': '/api/v1/analytics/operational-dashboard/'},
                {'label': 'Revenue Analytics', 'method': 'GET', 'path': '/api/v1/analytics/revenue-analytics/'},
                {'label': 'Guest Analytics', 'method': 'GET', 'path': '/api/v1/analytics/guest-analytics/'},
                {'label': 'Custom Reports', 'method': 'GET', 'path': '/api/v1/analytics/custom-reports/'},
                {'label': 'Scheduled Reports', 'method': 'GET', 'path': '/api/v1/analytics/scheduled-reports/'},
                {'label': 'Report Executions', 'method': 'GET', 'path': '/api/v1/analytics/report-executions/'},
                {'label': 'Occupancy Forecasts', 'method': 'GET', 'path': '/api/v1/analytics/occupancy-forecasts/'},
                {'label': 'Revenue Forecasts', 'method': 'GET', 'path': '/api/v1/analytics/revenue-forecasts/'},
                {'label': 'Cancellation Predictions', 'method': 'GET', 'path': '/api/v1/analytics/cancellation-predictions/'},
                {'label': 'No-Show Predictions', 'method': 'GET', 'path': '/api/v1/analytics/noshow-predictions/'},
                {'label': 'Forecast Metrics', 'method': 'GET', 'path': '/api/v1/analytics/forecast-metrics/'},
            ],
        },
        {
            'title': 'Domain Endpoints',
            'items': [
                {'label': 'Properties (Web)', 'method': 'GET', 'path': '/properties/'},
                {'label': 'Payments (Web)', 'method': 'GET', 'path': '/payments/history/'},
                {'label': 'Notifications (Web)', 'method': 'GET', 'path': '/notifications/'},
                {'label': 'Contracts (Web)', 'method': 'GET', 'path': '/contracts/'},
                {'label': 'Dynamic Pricing', 'method': 'GET', 'path': '/api/v1/bookings/dynamic-price/<room_id>/'},
                {'label': 'Room Recommendations', 'method': 'GET', 'path': '/api/v1/bookings/recommendations/<guest_id>/'},
            ],
        },
    ]

    return render(request, 'backend-navigation.html', {
        'page_title': 'API Reference',
        'role': _user_role(request.user),
        'endpoint_groups': endpoint_groups,
    })
