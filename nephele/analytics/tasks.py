"""
Analytics Tasks

Celery tasks for async analytics processing, ETL, and report generation.
"""

try:
    from celery import shared_task
except ImportError:
    def shared_task(func=None, *args, **kwargs):
        def decorator(inner_func):
            inner_func.delay = inner_func
            return inner_func

        if callable(func):
            return decorator(func)
        return decorator
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from properties.models import Property
from room.models import Booking, Room
from .metrics import REVENUE_STATUSES, NightLedger, room_count
from .models import (
    DashboardExecutiveMetrics,
    DashboardOperationalStatus,
    DashboardRevenueMetrics,
    DashboardGuestAnalytics,
    CustomReport,
    ScheduledReport,
    ReportExecution,
    ReportDeliveryTracking,
)

logger = logging.getLogger(__name__)


def _properties_for(property_id=None):
    properties = Property.objects.all()
    if property_id:
        properties = properties.filter(id=property_id)
    return properties


def _safe_round_div(numerator, denominator, multiplier=1):
    """Return round(numerator / denominator * multiplier, 2), or 0 if denominator <= 0."""
    if denominator > 0:
        return round((numerator / denominator * multiplier), 2)
    return 0


def _active_bookings_for(property_obj, metric_date):
    return Booking.objects.filter(
        room__property=property_obj,
        check_in_date__lte=metric_date,
        check_out_date__gt=metric_date,
        status__in=REVENUE_STATUSES,
    )


def _upsert_metrics(model, property_obj, metric_date, values, create_only=None):
    """Create the metrics row, or overwrite ``values`` on an existing one."""
    defaults = {**values, **(create_only or {})}
    metrics, created = model.objects.get_or_create(
        property=property_obj,
        metric_date=metric_date,
        defaults=defaults,
    )
    if not created:
        for field_name, value in values.items():
            setattr(metrics, field_name, value)
        metrics.save()
    return metrics


def _total_rooms_for(property_obj):
    return room_count([property_obj])


def _store_executive_metrics(property_obj, metric_date):
    kpis = NightLedger([property_obj], metric_date, metric_date).kpis()
    _upsert_metrics(
        DashboardExecutiveMetrics,
        property_obj,
        metric_date,
        {
            'total_revenue': kpis['total_revenue'],
            'avg_daily_rate': kpis['adr'],
            'occupancy_rate': kpis['occupancy_rate'],
            'revpar': kpis['revpar'],
            'booking_count': kpis['bookings'],
        },
    )


@shared_task
def calculate_executive_metrics(property_id=None, metric_date=None):
    """
    Calculate executive dashboard metrics for all or specific property
    
    Args:
        property_id: Specific property ID or None for all properties
        metric_date: Specific date or None for today
    """
    if metric_date is None:
        metric_date = timezone.now().date()

    for property_obj in _properties_for(property_id):
        try:
            _store_executive_metrics(property_obj, metric_date)
            logger.info(
                f"Calculated executive metrics for {property_obj.name} on {metric_date}"
            )
        except Exception as e:
            logger.error(
                f"Error calculating metrics for property {property_id}: {str(e)}"
            )


@shared_task
def calculate_operational_status(property_id=None):
    """
    Calculate operational dashboard status (real-time)
    
    Args:
        property_id: Specific property ID or None for all properties
    """
    now = timezone.now()
    
    properties = Property.objects.all()
    if property_id:
        properties = properties.filter(id=property_id)
    
    for property_obj in properties:
        try:
            today = now.date()
            
            room_states = dict(
                Room.objects.filter(property=property_obj)
                .values_list('status')
                .annotate(n=Count('id'))
            )
            occupied_count = room_states.get('occupied', 0)
            in_house = Booking.objects.filter(room__property=property_obj, status='checked_in')
            
            # Get scheduled check-ins/check-outs
            checkouts = Booking.objects.filter(
                room__property=property_obj,
                check_out_date=today,
                status='checked_in'
            ).count()
            
            checkins = Booking.objects.filter(
                room__property=property_obj,
                check_in_date=today,
                status='confirmed'
            ).count()
            
            # Create status record
            DashboardOperationalStatus.objects.create(
                property=property_obj,
                status_date=today,
                status_time=now,
                occupied_count=occupied_count,
                vacant_count=room_states.get('available', 0),
                cleaning_count=room_states.get('cleaning', 0),
                maintenance_count=room_states.get('maintenance', 0),
                blocked_count=room_states.get('reserved', 0),
                checkouts_scheduled=checkouts,
                checkins_scheduled=checkins,
                active_guests_count=in_house.count(),
                guests_with_special_requests=in_house.exclude(special_requests='').count(),
            )
            
            logger.info(
                f"Updated operational status for {property_obj.name}"
            )
            
        except Exception as e:
            logger.error(
                f"Error calculating operational status for property {property_id}: {str(e)}"
            )


def _room_uplift_pct(pricing_analyzer, room, metric_date):
    """ML price uplift (%) over base rate for a room, or None if unavailable."""
    try:
        recommendation = pricing_analyzer.get_pricing_recommendation(room.id, metric_date)
        if not recommendation:
            return None
        ml_price = recommendation['ensemble_prediction']
        base_rate = float(room.base_price)
        return ((ml_price - base_rate) / base_rate * 100) if base_rate > 0 else 0
    except Exception:
        return None


def _dynamic_pricing_uplift(property_obj, metric_date):
    """Average ML pricing uplift (%) over a sample of rooms (Task 3 models)."""
    from bookings.pricing_service import PricingAnalyzer

    try:
        pricing_analyzer = PricingAnalyzer()
        if not pricing_analyzer.predictor.available:
            return 0.0
        # Sample 5 rooms to estimate uplift (for performance)
        uplifts = [
            _room_uplift_pct(pricing_analyzer, room, metric_date)
            for room in property_obj.rooms.all()[:5]
        ]
        uplifts = [value for value in uplifts if value is not None]
        if uplifts:
            return round(sum(uplifts) / len(uplifts), 2)
        return 0.0
    except Exception as e:
        logger.warning(f"Could not calculate dynamic pricing uplift: {str(e)}")
        return 0.0


REVENUE_CHANNELS = {
    'booking_com': 'ota', 'trivago': 'ota', 'airbnb': 'ota', 'expedia': 'ota',
    'travel_agency': 'agency',
}


def _store_revenue_metrics(property_obj, metric_date):
    """Compute and persist revenue metrics. Returns the pricing uplift used."""
    ledger = NightLedger([property_obj], metric_date, metric_date)
    kpis = ledger.kpis()
    channel = {'direct': [0, 0.0], 'ota': [0, 0.0], 'agency': [0, 0.0]}
    for row in ledger.by_source():
        bucket = REVENUE_CHANNELS.get(row['source'], 'direct')
        channel[bucket][0] += row['bookings']
        channel[bucket][1] += row['revenue']
    revenue_direct, revenue_ota, revenue_agency = (
        round(channel[k][1], 2) for k in ('direct', 'ota', 'agency')
    )
    booking_count = kpis['bookings']

    cancellation_count = Booking.objects.filter(
        room__property=property_obj,
        check_in_date__lte=metric_date,
        check_out_date__gt=metric_date,
        status='cancelled'
    ).count()

    dynamic_pricing_uplift = _dynamic_pricing_uplift(property_obj, metric_date)

    _upsert_metrics(
        DashboardRevenueMetrics,
        property_obj,
        metric_date,
        {
            'total_revenue': kpis['total_revenue'],
            'revenue_direct': revenue_direct,
            'revenue_ota': revenue_ota,
            'revenue_agency': revenue_agency,
            'avg_daily_rate': kpis['adr'],
            'revpar': kpis['revpar'],
            'occupancy_rate': kpis['occupancy_rate'],
            'occupancy_count': kpis['rooms_sold'],
            'booking_count': booking_count,
            'cancellation_count': cancellation_count,
            'cancellation_rate': _safe_round_div(cancellation_count, booking_count, 100),
            'dynamic_pricing_uplift': dynamic_pricing_uplift,
        },
        create_only={
            'metrics_by_source': {
                key: {'count': count, 'revenue': round(revenue, 2)}
                for key, (count, revenue) in channel.items()
            }
        },
    )
    return dynamic_pricing_uplift


@shared_task
def calculate_revenue_metrics(property_id=None, metric_date=None):
    """
    Calculate revenue analytics metrics
    
    Includes:
    - Revenue by source (direct, OTA, travel agency)
    - Dynamic pricing uplift calculation (using Task 3 ML models)
    - Occupancy and cancellation metrics
    
    Args:
        property_id: Specific property ID or None for all properties
        metric_date: Specific date or None for today
    """
    if metric_date is None:
        metric_date = timezone.now().date()

    for property_obj in _properties_for(property_id):
        try:
            dynamic_pricing_uplift = _store_revenue_metrics(property_obj, metric_date)
            logger.info(
                f"Calculated revenue metrics for {property_obj.name} on {metric_date} "
                f"(Pricing Uplift: {dynamic_pricing_uplift}%)"
            )
        except Exception as e:
            logger.error(
                f"Error calculating revenue metrics for property {property_id}: {str(e)}"
            )


def _new_returning_guest_counts(guest_ids, analytics_date):
    new_guests = 0
    returning_guests = 0
    for guest_id in guest_ids:
        has_prior_booking = Booking.objects.filter(
            guest_id=guest_id,
            status__in=REVENUE_STATUSES,
            check_out_date__lte=analytics_date,
        ).exists()
        if has_prior_booking:
            returning_guests += 1
        else:
            new_guests += 1
    return new_guests, returning_guests


def _store_guest_analytics(property_obj, analytics_date):
    """Compute and persist guest analytics for one property/day."""
    bookings = _active_bookings_for(property_obj, analytics_date)
    stay_lengths = [
        (b.check_out_date - b.check_in_date).days
        for b in bookings.only('check_in_date', 'check_out_date')
    ]
    avg_stay = round(sum(stay_lengths) / len(stay_lengths), 2) if stay_lengths else 0
    guest_ids = list(bookings.values_list('guest_id', flat=True).distinct())
    new_guests, returning_guests = _new_returning_guest_counts(guest_ids, analytics_date)
    retention_rate = (
        round((returning_guests / len(guest_ids) * 100), 2) if guest_ids else 0
    )
    values = {
        'total_unique_guests': len(guest_ids),
        'new_guests': new_guests,
        'returning_guests': returning_guests,
        'avg_length_of_stay': avg_stay,
        'retention_rate': retention_rate,
    }
    analytics, created = DashboardGuestAnalytics.objects.get_or_create(
        property=property_obj,
        analytics_date=analytics_date,
        defaults=values,
    )
    if not created:
        for field_name, value in values.items():
            setattr(analytics, field_name, value)
        analytics.save(update_fields=list(values.keys()))


@shared_task
def calculate_guest_analytics(property_id=None, analytics_date=None):
    """
    Calculate guest analytics metrics
    
    Args:
        property_id: Specific property ID or None for all properties
        analytics_date: Specific date or None for today
    """
    if analytics_date is None:
        analytics_date = timezone.now().date()

    for property_obj in _properties_for(property_id):
        try:
            _store_guest_analytics(property_obj, analytics_date)
            logger.info(
                f"Calculated guest analytics for {property_obj.name} on {analytics_date}"
            )
        except Exception as e:
            logger.error(
                f"Error calculating guest analytics for property {property_id}: {str(e)}"
            )


@shared_task
def nightly_etl_pipeline():
    """
    Run full ETL pipeline nightly (2 AM UTC)
    
    Processes:
    1. Calculate executive metrics
    2. Calculate revenue metrics
    3. Calculate guest analytics
    4. Generate ML-based forecasts (occupancy, revenue, cancellation, no-show)
    5. Update operational status
    
    Leverages Task 3 ML models for predictions where available.
    """
    yesterday = (timezone.now() - timedelta(days=1)).date()
    
    logger.info("Starting nightly ETL pipeline with ML forecasting")
    
    try:
        # Calculate metrics for previous day
        calculate_executive_metrics.delay(metric_date=yesterday)
        calculate_revenue_metrics.delay(metric_date=yesterday)
        calculate_guest_analytics.delay(analytics_date=yesterday)
        
        # Generate forecasts using ML models from Task 3
        forecast_occupancy_task.delay(forecast_days=30)
        forecast_revenue_task.delay(forecast_days=30)
        predict_cancellations_task.delay()
        predict_noshow_task.delay()
        
        # Also calculate today's metrics
        calculate_operational_status.delay()
        
        logger.info("Nightly ETL pipeline completed successfully with ML forecasts")
        
    except Exception as e:
        logger.error(f"Nightly ETL pipeline failed: {str(e)}")
        raise


def run_custom_report(report):
    """Build a custom report, store the rendered file under MEDIA_ROOT and mark it generated."""
    import os
    from django.conf import settings
    from .reports import render_report

    try:
        content, _content_type, extension = render_report(report)
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports', 'custom')
        os.makedirs(reports_dir, exist_ok=True)
        stamp = timezone.now().strftime('%Y%m%d%H%M%S')
        file_path = os.path.join(reports_dir, f"custom_{report.id}_{stamp}.{extension}")
        with open(file_path, 'wb') as output:
            output.write(content)
        report.status = 'generated'
        report.file_path = file_path
        report.generated_at = timezone.now()
        report.error_message = ''
    except Exception as e:
        logger.exception(f"Error generating report {report.id}")
        report.status = 'failed'
        report.error_message = str(e)
    report.save(update_fields=['status', 'file_path', 'generated_at', 'error_message'])
    return report


@shared_task
def generate_custom_report(report_id):
    """Generate custom analytics report (async task)."""
    report = CustomReport.objects.filter(id=report_id).first()
    if report is None:
        logger.error(f"Report {report_id} not found")
        return
    run_custom_report(report)


# Automated Scheduled Report Tasks

@shared_task
def generate_scheduled_report(scheduled_report_id, override_recipients=None, execution_date=None):
    """
    Generate a scheduled report and trigger email delivery
    
    Args:
        scheduled_report_id: ID of ScheduledReport to generate
        override_recipients: Optional list of email addresses to override configured recipients
        execution_date: Optional date range for report (defaults to previous day)
    """
    import time
    start_time = time.time()
    
    try:
        scheduled_report = ScheduledReport.objects.get(id=scheduled_report_id)
        
        # Create report execution record
        if execution_date is None:
            execution_date = timezone.now().date()
        
        execution = ReportExecution.objects.create(
            scheduled_report=scheduled_report,
            execution_status='generating',
            data_date_from=execution_date,
            data_date_to=execution_date,
            email_recipients=override_recipients or scheduled_report.recipient_emails,
        )
        
        try:
            # Gather report data
            metrics_data = _gather_report_metrics(scheduled_report, execution_date)
            
            # Generate report file(s)
            files_generated = _generate_report_files(
                scheduled_report,
                execution,
                metrics_data
            )
            
            # Update execution status
            execution.execution_status = 'generated'
            execution.metrics_snapshot = metrics_data
            execution.execution_time_seconds = int(time.time() - start_time)
            execution.save()
            
            # Send email
            recipients = override_recipients or scheduled_report.recipient_emails
            if scheduled_report.include_managers and scheduled_report.property.manager:
                if scheduled_report.property.manager.email not in recipients:
                    recipients.append(scheduled_report.property.manager.email)
            
            send_report_email.delay(execution.id, recipients)
            
            # Update scheduled report
            scheduled_report.last_generated_at = timezone.now()
            scheduled_report.consecutive_failures = 0
            scheduled_report.save(update_fields=['last_generated_at', 'consecutive_failures'])
            
            logger.info(
                f"Generated scheduled report '{scheduled_report.name}' "
                f"(ID: {scheduled_report_id}) in {execution.execution_time_seconds}s"
            )
            
        except Exception as e:
            execution.execution_status = 'failed'
            execution.error_message = str(e)
            execution.execution_time_seconds = int(time.time() - start_time)
            execution.save()
            
            scheduled_report.consecutive_failures += 1
            scheduled_report.save(update_fields=['consecutive_failures'])
            
            logger.error(
                f"Error generating scheduled report '{scheduled_report.name}' "
                f"(ID: {scheduled_report_id}): {str(e)}"
            )
            raise
    
    except ScheduledReport.DoesNotExist:
        logger.error(f"Scheduled report {scheduled_report_id} not found")
    except Exception as e:
        logger.error(f"Error in scheduled report generation task: {str(e)}")
        raise


def _build_report_email_html(execution):
    html_content = f"""
        <html>
        <body>
            <h2>{execution.scheduled_report.name}</h2>
            <p>Dear Recipient,</p>
            <p>Your scheduled report for <strong>{execution.data_date_from}</strong> is ready.</p>
            <dl>
                <dt>Report Type:</dt>
                <dd>{execution.scheduled_report.get_report_type_display()}</dd>
                <dt>Generated:</dt>
                <dd>{execution.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC</dd>
            </dl>
            <p>Key Metrics:</p>
            <ul>
        """

    # Add metrics to email
    if execution.metrics_snapshot:
        for key, value in execution.metrics_snapshot.items():
            if isinstance(value, (int, float)):
                html_content += f"<li><strong>{key}:</strong> {value}</li>\n"

    html_content += """
            </ul>
            <p>Attached are the generated report files.</p>
            <p>Best regards,<br>NEPHELE Analytics System</p>
        </body>
        </html>
        """
    return html_content


_REPORT_ATTACHMENTS = (
    ('pdf_file_path', 'application/pdf'),
    ('excel_file_path', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    ('csv_file_path', 'text/csv'),
)


def _attach_report_files(email, execution):
    import os

    for attr_name, mimetype in _REPORT_ATTACHMENTS:
        file_path = getattr(execution, attr_name)
        if file_path and os.path.exists(file_path):
            email.attach_file(file_path, mimetype=mimetype)


@shared_task
def send_report_email(execution_id, recipients=None):
    """
    Send generated report via email
    
    Args:
        execution_id: ID of ReportExecution to send
        recipients: Optional override recipients list
    """
    try:
        from django.core.mail import EmailMessage
        
        execution = ReportExecution.objects.get(id=execution_id)
        
        if not recipients:
            recipients = execution.email_recipients
        
        # Build email
        subject = f"Report: {execution.scheduled_report.name} - {execution.data_date_from}"
        html_content = _build_report_email_html(execution)
        
        # Create email message
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email='noreply@nephele.local',
            to=recipients,
        )
        email.content_subtype = 'html'
        
        # Attach generated files
        _attach_report_files(email, execution)
        
        # Send email
        email.send(fail_silently=False)
        
        # Update execution status
        execution.email_status = 'sent'
        execution.email_sent_at = timezone.now()
        execution.save(update_fields=['email_status', 'email_sent_at'])
        
        # Create delivery tracking records
        for recipient in recipients:
            ReportDeliveryTracking.objects.get_or_create(
                report_execution=execution,
                recipient_email=recipient,
                defaults={'delivery_status': 'sent'}
            )
        
        logger.info(f"Sent report email (execution_id: {execution_id}) to {len(recipients)} recipients")
        
    except ReportExecution.DoesNotExist:
        logger.error(f"Report execution {execution_id} not found")
    except Exception as e:
        logger.error(f"Error sending report email (execution_id: {execution_id}): {str(e)}")
        
        try:
            execution = ReportExecution.objects.get(id=execution_id)
            execution.email_status = 'failed'
            execution.save(update_fields=['email_status'])
        except:
            pass
        
        raise


@shared_task
def process_pending_scheduled_reports():
    """
    Check for pending scheduled reports and trigger generation
    
    Called every hour by Celery beat
    """
    from django.db.models import Q
    
    now = timezone.now()
    
    try:
        # Find active scheduled reports where next_scheduled_at <= now
        pending_reports = ScheduledReport.objects.filter(
            is_active=True,
            next_scheduled_at__lte=now
        )
        
        logger.info(f"Found {pending_reports.count()} pending scheduled reports")
        
        for report in pending_reports:
            # Trigger generation task
            generate_scheduled_report.delay(scheduled_report_id=report.id)
            
            # Calculate next scheduled time
            _calculate_next_scheduled_time(report)
            report.save(update_fields=['next_scheduled_at'])
        
    except Exception as e:
        logger.error(f"Error processing pending scheduled reports: {str(e)}")
        raise


@shared_task
def cleanup_old_reports(days_to_retain=730):
    """
    Clean up old report files and database records
    
    Args:
        days_to_retain: Number of days of reports to keep (default: 2 years)
    """
    import os
    from shutil import rmtree
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_retain)
        
        # Find old executions
        old_executions = ReportExecution.objects.filter(created_at__lt=cutoff_date)
        
        logger.info(f"Cleaning up {old_executions.count()} report executions older than {days_to_retain} days")
        
        for execution in old_executions:
            # Delete files
            for file_path in [execution.pdf_file_path, execution.excel_file_path, execution.csv_file_path]:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
            
            # Delete tracking records
            delivery_records = ReportDeliveryTracking.objects.filter(report_execution=execution)
            delivery_records.delete()
        
        # Delete old executions
        old_executions.delete()
        
        logger.info("Report cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Error cleaning up old reports: {str(e)}")
        raise


# Helper functions

def _executive_report_metrics(property_obj, report_date):
    exec_metrics = DashboardExecutiveMetrics.objects.filter(
        property=property_obj,
        metric_date=report_date
    ).first()
    if not exec_metrics:
        return {}
    return {
        'total_revenue': float(exec_metrics.total_revenue or 0),
        'avg_daily_rate': float(exec_metrics.avg_daily_rate or 0),
        'occupancy_rate': float(exec_metrics.occupancy_rate or 0),
        'revpar': float(exec_metrics.revpar or 0),
        'booking_count': exec_metrics.booking_count,
    }


def _revenue_report_metrics(property_obj, report_date):
    revenue_metrics = DashboardRevenueMetrics.objects.filter(
        property=property_obj,
        metric_date=report_date
    ).first()
    if not revenue_metrics:
        return {}
    return {
        'revenue_direct': float(revenue_metrics.revenue_direct or 0),
        'revenue_ota': float(revenue_metrics.revenue_ota or 0),
        'cancellation_rate': float(revenue_metrics.cancellation_rate or 0),
    }


def _guest_report_metrics(property_obj, report_date):
    guest_analytics = DashboardGuestAnalytics.objects.filter(
        property=property_obj,
        analytics_date=report_date
    ).first()
    if not guest_analytics:
        return {}
    return {
        'total_unique_guests': guest_analytics.total_unique_guests,
        'review_score': float(guest_analytics.avg_review_score or 0),
        'nps': guest_analytics.avg_nps or 0,
    }


def _gather_report_metrics(scheduled_report, report_date):
    """
    Gather metrics data for report generation
    
    Returns dict of metrics
    """
    property_obj = scheduled_report.property

    metrics = {}
    metrics.update(_executive_report_metrics(property_obj, report_date))
    metrics.update(_revenue_report_metrics(property_obj, report_date))
    metrics.update(_guest_report_metrics(property_obj, report_date))
    return metrics


def _generate_report_files(scheduled_report, execution, metrics_data):
    """
    Generate report files in configured formats
    
    Returns dict with file paths
    """
    import os
    
    # Create reports directory if needed
    reports_dir = '/tmp/nephele_reports'
    os.makedirs(reports_dir, exist_ok=True)
    
    files = {}
    report_name = f"{scheduled_report.property.id}_{scheduled_report.id}_{execution.data_date_from}"
    
    # Generate PDF
    if 'pdf' in scheduled_report.export_formats:
        pdf_path = os.path.join(reports_dir, f"{report_name}.pdf")
        _write_text_report(pdf_path, [
            {'metric': key, 'value': value} for key, value in metrics_data.items()
        ])
        files['pdf'] = pdf_path
        execution.pdf_file_path = pdf_path
    
    # Generate Excel
    if 'excel' in scheduled_report.export_formats:
        excel_path = os.path.join(reports_dir, f"{report_name}.xlsx")
        rows = [{'metric': key, 'value': value} for key, value in metrics_data.items()]
        try:
            import pandas as pd
            pd.DataFrame(rows).to_excel(excel_path, index=False)
        except Exception:
            _write_csv_report(excel_path, rows)
        files['excel'] = excel_path
        execution.excel_file_path = excel_path
    
    # Generate CSV
    if 'csv' in scheduled_report.export_formats:
        csv_path = os.path.join(reports_dir, f"{report_name}.csv")
        _write_csv_report(csv_path, [
            {'metric': key, 'value': value} for key, value in metrics_data.items()
        ])
        files['csv'] = csv_path
        execution.csv_file_path = csv_path
    
    execution.save()
    return files


def _calculate_next_scheduled_time(scheduled_report):
    """
    Calculate next scheduled execution time for a scheduled report
    """
    from zoneinfo import ZoneInfo

    from django.utils import timezone

    user_tz = ZoneInfo(scheduled_report.timezone)
    now_user_tz = timezone.now().astimezone(user_tz)

    schedule_time = scheduled_report.schedule_time

    # Create next scheduled datetime
    if scheduled_report.schedule_type == 'daily':
        next_date = now_user_tz.date() + timedelta(days=1)
        next_datetime = datetime.combine(next_date, schedule_time, tzinfo=user_tz)

    elif scheduled_report.schedule_type == 'weekly':
        dow = scheduled_report.schedule_dow or 0
        days_ahead = (dow - now_user_tz.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        next_date = now_user_tz.date() + timedelta(days=days_ahead)
        next_datetime = datetime.combine(next_date, schedule_time, tzinfo=user_tz)

    elif scheduled_report.schedule_type == 'monthly':
        day = scheduled_report.schedule_day or 1
        next_month = now_user_tz.date().replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=1)
        try:
            next_date = next_month.replace(day=day)
        except ValueError:
            # Handle cases like Feb 30
            next_date = next_month.replace(day=1) - timedelta(days=1)

        next_datetime = datetime.combine(next_date, schedule_time, tzinfo=user_tz)

    else:
        # Custom cron expression - set to 1 day from now
        next_datetime = timezone.now() + timedelta(days=1)

    # Store as UTC-aware datetime
    scheduled_report.next_scheduled_at = next_datetime.astimezone(ZoneInfo('UTC'))


# ML-Based Forecasting Tasks (Leverage Task 3 Models)

FORECAST_MODEL_TYPE = 'ensemble'
SEASONAL_MULTIPLIER = {1: 0.8, 2: 0.8, 6: 1.15, 7: 1.25, 8: 1.25, 12: 1.1}


def _on_books_nights(property_obj, start, end):
    """{date: (rooms sold, room revenue)} from confirmed / in-house bookings."""
    ledger = NightLedger([property_obj], start, end)
    sold = {}
    for night, booking, rate in ledger.nights:
        if booking.status in ('confirmed', 'checked_in'):
            rooms, revenue = sold.get(night, (0, 0.0))
            sold[night] = (rooms + 1, revenue + float(rate))
    return sold


def _occupancy_forecasts(property_obj, forecast_date, forecast_days):
    """Yield (target_date, predicted %, lower %, upper %) for each day ahead.

    Blends rooms already on the books with a pickup baseline taken from the
    trailing 28 days (same weekday mix), adjusted for seasonality.
    """
    total_rooms = _total_rooms_for(property_obj)
    if not total_rooms:
        return
    trailing = NightLedger([property_obj], forecast_date - timedelta(days=28),
                           forecast_date - timedelta(days=1)).kpis()['occupancy_rate']
    on_books = _on_books_nights(property_obj, forecast_date + timedelta(days=1),
                                forecast_date + timedelta(days=forecast_days))
    for days_ahead in range(1, forecast_days + 1):
        target = forecast_date + timedelta(days=days_ahead)
        booked = on_books.get(target, (0, 0.0))[0] / total_rooms * 100
        seasonal = SEASONAL_MULTIPLIER.get(target.month, 1.0)
        baseline = min(100.0, trailing * seasonal * (1.05 if target.weekday() in (4, 5) else 1.0))
        predicted = min(100.0, max(booked, baseline))
        spread = 4 + days_ahead * 0.35
        yield target, round(predicted, 2), round(max(booked, predicted - spread), 2), round(min(100.0, predicted + spread), 2)


@shared_task
def forecast_occupancy_task(property_id=None, forecast_days=30):
    """
    Generate occupancy forecasts from bookings on the books plus a seasonal pickup baseline.

    Args:
        property_id: Specific property ID or None for all properties
        forecast_days: Number of days to forecast (default 30)
    """
    from .models import OccupancyForecast

    forecast_date = timezone.localdate()
    for property_obj in _properties_for(property_id):
        try:
            for target, predicted, lower, upper in _occupancy_forecasts(property_obj, forecast_date, forecast_days):
                OccupancyForecast.objects.update_or_create(
                    property=property_obj,
                    forecast_date=forecast_date,
                    target_date=target,
                    model_type=FORECAST_MODEL_TYPE,
                    defaults={
                        'predicted_occupancy': predicted,
                        'lower_bound': lower,
                        'upper_bound': upper,
                    },
                )
            logger.info(f"Generated occupancy forecasts for {property_obj.name} ({forecast_days} days)")
        except Exception as e:
            logger.exception(f"Error generating occupancy forecast for {property_obj.name}: {e}")


def _room_adr_contribution(pricing_analyzer, room, target_date, predicted_occupancy):
    """Nightly rate for a room: ML recommendation when available, else base price."""
    try:
        if pricing_analyzer.predictor.available:
            recommendation = pricing_analyzer.get_pricing_recommendation(
                room.id,
                target_date,
                occupancy_rate=predicted_occupancy
            )
            if recommendation:
                return recommendation['ensemble_prediction']
        return float(room.base_price)
    except Exception:
        return float(room.base_price)


def _average_daily_rate(property_obj, pricing_analyzer, target_date, predicted_occupancy):
    total_adr = 0
    room_count = 0
    for room in property_obj.rooms.all():
        total_adr += _room_adr_contribution(
            pricing_analyzer, room, target_date, predicted_occupancy
        )
        room_count += 1
    return (total_adr / room_count) if room_count > 0 else 75.0


def _forecast_property_revenue(property_obj, forecast_date, forecast_days):
    from .models import RevenueForecast, OccupancyForecast
    from bookings.pricing_service import PricingAnalyzer

    total_rooms = _total_rooms_for(property_obj)
    trailing_adr = NightLedger([property_obj], forecast_date - timedelta(days=28),
                               forecast_date - timedelta(days=1)).kpis()['adr']
    on_books = _on_books_nights(property_obj, forecast_date + timedelta(days=1),
                                forecast_date + timedelta(days=forecast_days))
    pricing_analyzer = None

    for days_ahead in range(1, forecast_days + 1):
        target_date = forecast_date + timedelta(days=days_ahead)
        occupancy_forecast = OccupancyForecast.objects.filter(
            property=property_obj,
            forecast_date=forecast_date,
            target_date=target_date,
            model_type=FORECAST_MODEL_TYPE,
        ).first()
        predicted_occupancy = float(occupancy_forecast.predicted_occupancy) if occupancy_forecast else 50.0

        # ADR: rates already sold for that night, else recent ADR, else ML/base rates
        rooms_booked, booked_revenue = on_books.get(target_date, (0, 0.0))
        if rooms_booked:
            avg_adr = booked_revenue / rooms_booked
        elif trailing_adr:
            avg_adr = trailing_adr
        else:
            pricing_analyzer = pricing_analyzer or PricingAnalyzer()
            avg_adr = _average_daily_rate(property_obj, pricing_analyzer, target_date, predicted_occupancy)

        predicted_revenue = total_rooms * predicted_occupancy / 100 * avg_adr
        spread = 0.08 + days_ahead * 0.005

        RevenueForecast.objects.update_or_create(
            property=property_obj,
            forecast_date=forecast_date,
            target_date=target_date,
            model_type=FORECAST_MODEL_TYPE,
            defaults={
                'predicted_revenue': round(predicted_revenue, 2),
                'predicted_occupancy': round(predicted_occupancy, 2),
                'avg_daily_rate': round(avg_adr, 2),
                'num_rooms': total_rooms,
                'upper_bound': round(predicted_revenue * (1 + spread), 2),
                'lower_bound': round(predicted_revenue * (1 - spread), 2),
            }
        )


@shared_task
def forecast_revenue_task(property_id=None, forecast_days=30):
    """
    Generate revenue forecasts using predicted occupancy and pricing data.
    Uses ML-based predictions where available, fallback to statistical methods.
    
    Args:
        property_id: Specific property ID or None for all properties
        forecast_days: Number of days to forecast
    """
    forecast_date = timezone.localdate()

    for property_obj in _properties_for(property_id):
        try:
            _forecast_property_revenue(property_obj, forecast_date, forecast_days)
            logger.info(f"Generated revenue forecasts for {property_obj.name} ({forecast_days} days)")
        except Exception as e:
            logger.error(f"Error generating revenue forecast for property {property_id}: {str(e)}")


def _risk_level(risk_score, high_threshold, medium_threshold):
    if risk_score > high_threshold:
        return 'high'
    return 'medium' if risk_score > medium_threshold else 'low'


def _cancellation_days_delta(days_until_checkin):
    # Very soon bookings less likely to cancel; long advance bookings more likely
    if days_until_checkin < 3:
        return -0.15
    if days_until_checkin > 30:
        return 0.15
    return 0.0


def _cancellation_lead_time_delta(lead_time):
    # Longer lead time increases cancellation risk
    if lead_time > 45:
        return 0.15
    if lead_time < 7:
        return -0.10
    return 0.0


def _lead_time_days(booking):
    reserved = booking.date_of_reservation or booking.created_at.date()
    return max(0, (booking.check_in_date - reserved).days)


def _nightly_price(booking):
    nights = (booking.check_out_date - booking.check_in_date).days
    return round(float(booking.base_price or 0) / nights, 2) if nights > 0 else None


def _cancellation_risk(booking, prediction_date):
    """Return (risk_score, risk_factors) for a booking's cancellation risk."""
    risk_score = 0.3  # Base risk

    # Days until check-in (closer = lower risk of cancellation)
    days_until_checkin = (booking.check_in_date - prediction_date).days
    risk_score += _cancellation_days_delta(days_until_checkin)

    # Guest history - repeat guests less likely to cancel
    guest_booking_count = Booking.objects.filter(
        guest=booking.guest,
        status__in=[*REVENUE_STATUSES, 'cancelled']
    ).count()
    if guest_booking_count > 3:
        risk_score -= 0.10  # Repeat guests better

    lead_time = _lead_time_days(booking)
    risk_score += _cancellation_lead_time_delta(lead_time)

    # Booking source - certain channels have higher cancellation
    if booking.booking_source in ['travel_agency']:
        risk_score += 0.05  # Slight higher risk

    # Length of stay - very short stays have higher cancel risk
    num_nights = (booking.check_out_date - booking.check_in_date).days
    if num_nights == 1:
        risk_score += 0.10

    # Clamp risk score between 0 and 1
    risk_score = max(0.0, min(1.0, risk_score))

    risk_factors = {
        'advance_booking': days_until_checkin > 30,
        'new_guest': guest_booking_count <= 1,
        'long_lead_time': lead_time > 45,
        'single_night': num_nights == 1,
        'travel_agency_booking': booking.booking_source == 'travel_agency'
    }
    return risk_score, risk_factors


def _predict_booking_cancellation(booking, property_obj, prediction_date):
    from .models import CancellationPrediction

    risk_score, risk_factors = _cancellation_risk(booking, prediction_date)
    CancellationPrediction.objects.update_or_create(
        booking=booking,
        property=property_obj,
        prediction_date=prediction_date,
        defaults={
            'prediction_time': timezone.now(),
            'cancellation_risk_score': round(risk_score, 2),
            'risk_level': _risk_level(risk_score, 0.6, 0.35),
            'risk_factors': risk_factors,
            'lead_time_days': _lead_time_days(booking),
            'booking_source': booking.booking_source,
            'customer_type': 'repeat' if not risk_factors['new_guest'] else 'new',
            'refund_policy': (
                'refundable' if booking.rate_plan is None or booking.rate_plan.is_refundable
                else 'non_refundable'
            ),
            'price_per_night': _nightly_price(booking),
        }
    )


@shared_task
def predict_cancellations_task(property_id=None):
    """
    Predict high-risk booking cancellations based on patterns.
    Creates alerts for property staff.
    
    Args:
        property_id: Specific property ID or None for all properties
    """
    prediction_date = timezone.localdate()

    for property_obj in _properties_for(property_id):
        try:
            # Get recent bookings (next 60 days that haven't been cancelled yet)
            upcoming_bookings = Booking.objects.filter(
                room__property=property_obj,
                check_in_date__gte=prediction_date,
                check_in_date__lte=prediction_date + timedelta(days=60),
                status__in=['confirmed', 'pending']
            ).select_related('guest', 'rate_plan')

            for booking in upcoming_bookings:
                try:
                    _predict_booking_cancellation(booking, property_obj, prediction_date)
                except Exception as e:
                    logger.warning(f"Error predicting cancellation for booking {booking.id}: {str(e)}")

            logger.info(f"Generated cancellation predictions for {property_obj.name}")

        except Exception as e:
            logger.error(f"Error in cancellation prediction for property {property_id}: {str(e)}")


def _noshow_days_delta(days_until_checkin):
    if days_until_checkin == 0:
        return -0.10  # Today = committed
    if days_until_checkin == 1:
        return -0.08
    if days_until_checkin > 14:
        return 0.12  # Far future more likely to not show
    return 0.0


def _noshow_source_delta(booking_source):
    if booking_source in ['booking_com', 'trivago']:
        return 0.10  # OTA bookings higher no-show risk
    if booking_source in ['direct_website', 'phone']:
        return -0.08  # Direct bookings lower no-show
    return 0.0


def _noshow_risk(booking, prediction_date):
    """Return (risk_score, risk_factors) for a booking's no-show risk."""
    risk_score = 0.15  # Base no-show risk

    # Days until check-in (very close = lower no-show risk)
    days_until_checkin = (booking.check_in_date - prediction_date).days
    risk_score += _noshow_days_delta(days_until_checkin)

    # Guest communication - no special requests might indicate casual interest
    has_special_requests = bool(booking.special_requests)
    if not has_special_requests:
        risk_score += 0.08

    risk_score += _noshow_source_delta(booking.booking_source)

    # Weekend vs weekday (slightly higher risk on weekends)
    is_weekend_checkin = booking.check_in_date.weekday() >= 4  # Fri-Sun
    if is_weekend_checkin:
        risk_score += 0.05

    # Clamp risk score
    risk_score = max(0.0, min(1.0, risk_score))

    risk_factors = {
        'far_future_booking': days_until_checkin > 14,
        'no_special_requests': not has_special_requests,
        'ota_booking': booking.booking_source in ['booking_com', 'trivago'],
        'weekend_checkin': is_weekend_checkin,
    }
    return risk_score, risk_factors


def _predict_booking_noshow(booking, property_obj, prediction_date):
    from .models import NoShowPrediction

    risk_score, risk_factors = _noshow_risk(booking, prediction_date)
    NoShowPrediction.objects.update_or_create(
        booking=booking,
        property=property_obj,
        prediction_date=prediction_date,
        defaults={
            'prediction_time': timezone.now(),
            'noshow_risk_score': round(risk_score, 2),
            'risk_level': _risk_level(risk_score, 0.45, 0.25),
            'risk_factors': risk_factors,
            'customer_country': booking.guest.country if booking.guest else None,
            'booking_source': booking.booking_source,
            'payment_confirmed': booking.payments.filter(status='completed').exists(),
            'advance_checkin_days': (booking.check_in_date - prediction_date).days,
            'price_per_night': _nightly_price(booking),
            'special_requests_count': 1 if booking.special_requests else 0,
            'overbooking_flag': risk_score > 0.45,
        }
    )


@shared_task
def predict_noshow_task(property_id=None):
    """
    Predict no-show risk for upcoming check-ins.
    Used for overbooking decisions and guest communication.
    
    Args:
        property_id: Specific property ID or None for all properties
    """
    prediction_date = timezone.localdate()
    checkin_window_start = prediction_date
    checkin_window_end = prediction_date + timedelta(days=30)

    for property_obj in _properties_for(property_id):
        try:
            # Get bookings checking in within 30 days
            upcoming_checkins = Booking.objects.filter(
                room__property=property_obj,
                check_in_date__gte=checkin_window_start,
                check_in_date__lte=checkin_window_end,
                status__in=['confirmed', 'pending']
            ).select_related('guest')

            for booking in upcoming_checkins:
                try:
                    _predict_booking_noshow(booking, property_obj, prediction_date)
                except Exception as e:
                    logger.warning(f"Error predicting no-show for booking {booking.id}: {str(e)}")

            logger.info(f"Generated no-show predictions for {property_obj.name}")

        except Exception as e:
            logger.error(f"Error in no-show prediction for property {property_id}: {str(e)}")


def _write_csv_report(path, rows):
    """Write rows to CSV file."""
    import csv

    fieldnames = list(rows[0].keys()) if rows else ['metric', 'value']
    with open(path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_text_report(path, rows):
    """Write simple text-based report content."""
    with open(path, 'w', encoding='utf-8') as text_file:
        text_file.write('NEPHELE Analytics Report\n')
        text_file.write(f'Generated: {timezone.now().isoformat()}\n\n')
        for row in rows:
            text_file.write(', '.join([f"{key}={value}" for key, value in row.items()]))
            text_file.write('\n')
