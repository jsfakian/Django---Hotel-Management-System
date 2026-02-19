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
from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from properties.models import Property
from room.models import Booking
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
    
    properties = Property.objects.all()
    if property_id:
        properties = properties.filter(id=property_id)
    
    for property_obj in properties:
        try:
            # Get bookings for the day
            active_bookings = Booking.objects.filter(
                room__property=property_obj,
                check_in_date__lte=metric_date,
                check_out_date__gt=metric_date,
                status__in=['confirmed', 'checked_in']
            )
            
            total_rooms = property_obj.total_rooms or property_obj.rooms.count()
            occupied_rooms = active_bookings.values('room_id').distinct().count()
            
            # Calculate KPIs
            total_revenue = active_bookings.aggregate(
                total=Sum(Coalesce('actual_price', 'base_price'))
            )['total'] or 0
            
            occupancy_rate = round((occupied_rooms / total_rooms * 100), 2) if total_rooms > 0 else 0
            
            adr = round((total_revenue / occupied_rooms), 2) if occupied_rooms > 0 else 0
            revpar = round((total_revenue / total_rooms), 2) if total_rooms > 0 else 0
            
            # Create or update metrics
            metrics, created = DashboardExecutiveMetrics.objects.get_or_create(
                property=property_obj,
                metric_date=metric_date,
                defaults={
                    'total_revenue': total_revenue,
                    'avg_daily_rate': adr,
                    'occupancy_rate': occupancy_rate,
                    'revpar': revpar,
                    'booking_count': active_bookings.count(),
                }
            )
            
            if not created:
                metrics.total_revenue = total_revenue
                metrics.avg_daily_rate = adr
                metrics.occupancy_rate = occupancy_rate
                metrics.revpar = revpar
                metrics.booking_count = active_bookings.count()
                metrics.save()
            
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
            
            # Get room status counts
            occupied_bookings = Booking.objects.filter(
                room__property=property_obj,
                check_in_date__lte=today,
                check_out_date__gt=today,
                status__in=['confirmed', 'checked_in']
            )
            
            total_rooms = property_obj.total_rooms or property_obj.rooms.count()
            occupied_count = occupied_bookings.values('room_id').distinct().count()
            vacant_count = total_rooms - occupied_count
            
            # Get scheduled check-ins/check-outs
            checkouts = Booking.objects.filter(
                room__property=property_obj,
                check_out_date=today,
                status__in=['confirmed', 'checked_in']
            ).count()
            
            checkins = Booking.objects.filter(
                room__property=property_obj,
                check_in_date=today,
                status='confirmed'
            ).count()
            
            # Create status record
            status_obj = DashboardOperationalStatus.objects.create(
                property=property_obj,
                status_date=today,
                status_time=now,
                occupied_count=occupied_count,
                vacant_count=vacant_count,
                cleaning_count=0,  # Would be updated from cleaning system
                maintenance_count=0,  # Would be updated from maintenance system
                blocked_count=0,
                checkouts_scheduled=checkouts,
                checkins_scheduled=checkins,
            )
            
            logger.info(
                f"Updated operational status for {property_obj.name}"
            )
            
        except Exception as e:
            logger.error(
                f"Error calculating operational status for property {property_id}: {str(e)}"
            )


@shared_task
def calculate_revenue_metrics(property_id=None, metric_date=None):
    """
    Calculate revenue analytics metrics
    
    Args:
        property_id: Specific property ID or None for all properties
        metric_date: Specific date or None for today
    """
    if metric_date is None:
        metric_date = timezone.now().date()
    
    properties = Property.objects.all()
    if property_id:
        properties = properties.filter(id=property_id)
    
    for property_obj in properties:
        try:
            # Get bookings and payments
            active_bookings = Booking.objects.filter(
                room__property=property_obj,
                check_in_date__lte=metric_date,
                check_out_date__gt=metric_date,
                status__in=['confirmed', 'checked_in']
            )
            
            # Calculate revenue by source
            direct_bookings = active_bookings.filter(travel_agency__isnull=True)
            ota_bookings = active_bookings.none()
            agency_bookings = active_bookings.filter(travel_agency__isnull=False)
            
            total_revenue = active_bookings.aggregate(total=Sum(Coalesce('actual_price', 'base_price')))['total'] or 0
            revenue_direct = direct_bookings.aggregate(total=Sum(Coalesce('actual_price', 'base_price')))['total'] or 0
            revenue_ota = ota_bookings.aggregate(total=Sum(Coalesce('actual_price', 'base_price')))['total'] or 0
            revenue_agency = agency_bookings.aggregate(total=Sum(Coalesce('actual_price', 'base_price')))['total'] or 0
            
            total_rooms = property_obj.total_rooms or property_obj.rooms.count()
            occupied_rooms = active_bookings.values('room_id').distinct().count()

            cancellation_count = Booking.objects.filter(
                room__property=property_obj,
                check_in_date__lte=metric_date,
                check_out_date__gt=metric_date,
                status='cancelled'
            ).count()

            cancellation_rate = round((cancellation_count / active_bookings.count() * 100), 2) if active_bookings.count() > 0 else 0
            
            occupancy_rate = round((occupied_rooms / total_rooms * 100), 2) if total_rooms > 0 else 0
            adr = round((total_revenue / occupied_rooms), 2) if occupied_rooms > 0 else 0
            revpar = round((total_revenue / total_rooms), 2) if total_rooms > 0 else 0
            
            # Create or update metrics
            metrics, created = DashboardRevenueMetrics.objects.get_or_create(
                property=property_obj,
                metric_date=metric_date,
                defaults={
                    'total_revenue': total_revenue,
                    'revenue_direct': revenue_direct,
                    'revenue_ota': revenue_ota,
                    'revenue_agency': revenue_agency,
                    'avg_daily_rate': adr,
                    'revpar': revpar,
                    'occupancy_rate': occupancy_rate,
                    'occupancy_count': occupied_rooms,
                    'booking_count': active_bookings.count(),
                    'cancellation_count': cancellation_count,
                    'cancellation_rate': cancellation_rate,
                    'metrics_by_source': {
                        'direct': {
                            'count': direct_bookings.count(),
                            'revenue': float(revenue_direct)
                        },
                        'ota': {
                            'count': ota_bookings.count(),
                            'revenue': float(revenue_ota)
                        },
                        'agency': {
                            'count': agency_bookings.count(),
                            'revenue': float(revenue_agency)
                        }
                    }
                }
            )
            
            if not created:
                metrics.total_revenue = total_revenue
                metrics.revenue_direct = revenue_direct
                metrics.revenue_ota = revenue_ota
                metrics.revenue_agency = revenue_agency
                metrics.avg_daily_rate = adr
                metrics.revpar = revpar
                metrics.occupancy_rate = occupancy_rate
                metrics.occupancy_count = occupied_rooms
                metrics.booking_count = active_bookings.count()
                metrics.cancellation_count = cancellation_count
                metrics.cancellation_rate = cancellation_rate
                metrics.save()
            
            logger.info(
                f"Calculated revenue metrics for {property_obj.name} on {metric_date}"
            )
            
        except Exception as e:
            logger.error(
                f"Error calculating revenue metrics for property {property_id}: {str(e)}"
            )


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
    
    properties = Property.objects.all()
    if property_id:
        properties = properties.filter(id=property_id)
    
    for property_obj in properties:
        try:
            # Get active bookings for the day
            bookings = Booking.objects.filter(
                room__property=property_obj,
                check_in_date__lte=analytics_date,
                check_out_date__gt=analytics_date,
                status__in=['confirmed', 'checked_in']
            )

            guest_ids = list(bookings.values_list('guest_id', flat=True).distinct())
            new_guests = 0
            returning_guests = 0

            for guest_id in guest_ids:
                has_prior_booking = Booking.objects.filter(
                    guest_id=guest_id,
                    check_in_date__lt=analytics_date
                ).exists()
                if has_prior_booking:
                    returning_guests += 1
                else:
                    new_guests += 1
            
            # Create analytics record
            analytics, created = DashboardGuestAnalytics.objects.get_or_create(
                property=property_obj,
                analytics_date=analytics_date,
                defaults={
                    'total_unique_guests': len(guest_ids),
                    'new_guests': new_guests,
                    'returning_guests': returning_guests,
                    'avg_length_of_stay': 3.0,  # Default average
                    'avg_review_score': 4.5,  # Default
                    'retention_rate': round((returning_guests / len(guest_ids) * 100), 2) if len(guest_ids) > 0 else 0,
                }
            )

            if not created:
                analytics.total_unique_guests = len(guest_ids)
                analytics.new_guests = new_guests
                analytics.returning_guests = returning_guests
                analytics.retention_rate = round((returning_guests / len(guest_ids) * 100), 2) if len(guest_ids) > 0 else 0
                analytics.save(update_fields=['total_unique_guests', 'new_guests', 'returning_guests', 'retention_rate'])
            
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
    4. Generate forecasts (if enabled)
    """
    yesterday = (timezone.now() - timedelta(days=1)).date()
    
    logger.info("Starting nightly ETL pipeline")
    
    try:
        # Calculate metrics for previous day
        calculate_executive_metrics.delay(metric_date=yesterday)
        calculate_revenue_metrics.delay(metric_date=yesterday)
        calculate_guest_analytics.delay(analytics_date=yesterday)
        
        # Also calculate today's metrics
        calculate_operational_status.delay()
        
        logger.info("Nightly ETL pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Nightly ETL pipeline failed: {str(e)}")
        raise


@shared_task
def generate_custom_report(report_id):
    """
    Generate custom analytics report (async task)
    
    Args:
        report_id: ID of CustomReport to generate
    """
    try:
        report = CustomReport.objects.get(id=report_id)
        
        import os
        import csv

        report.status = 'pending'
        report.error_message = ''
        report.save(update_fields=['status', 'error_message'])

        reports_dir = '/tmp/nephele_reports/custom'
        os.makedirs(reports_dir, exist_ok=True)

        rows = _gather_custom_report_rows(report)
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')

        extension = report.export_format if report.export_format != 'excel' else 'xlsx'
        file_path = os.path.join(reports_dir, f"custom_{report.id}_{timestamp}.{extension}")

        if report.export_format == 'csv':
            _write_csv_report(file_path, rows)
        elif report.export_format == 'excel':
            try:
                import pandas as pd
                df = pd.DataFrame(rows)
                df.to_excel(file_path, index=False)
            except Exception:
                _write_csv_report(file_path, rows)
        else:
            _write_text_report(file_path, rows)

        report.status = 'generated'
        report.file_path = file_path
        report.generated_at = timezone.now()
        report.save(update_fields=['status', 'file_path', 'generated_at'])
        
        logger.info(f"Generated report {report.name} (ID: {report_id})")
        
    except CustomReport.DoesNotExist:
        logger.error(f"Report {report_id} not found")
    except Exception as e:
        try:
            report = CustomReport.objects.get(id=report_id)
            report.status = 'failed'
            report.error_message = str(e)
            report.save(update_fields=['status', 'error_message'])
        except Exception:
            pass
        logger.error(f"Error generating report {report_id}: {str(e)}")


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
        from django.core.files import File
        import os
        
        execution = ReportExecution.objects.get(id=execution_id)
        
        if not recipients:
            recipients = execution.email_recipients
        
        # Build email
        subject = f"Report: {execution.scheduled_report.name} - {execution.data_date_from}"
        
        # Create HTML body
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
        
        # Create email message
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email='noreply@nephele.local',
            to=recipients,
        )
        email.content_subtype = 'html'
        
        # Attach generated files
        if execution.pdf_file_path and os.path.exists(execution.pdf_file_path):
            email.attach_file(execution.pdf_file_path, mimetype='application/pdf')
        
        if execution.excel_file_path and os.path.exists(execution.excel_file_path):
            email.attach_file(execution.excel_file_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        if execution.csv_file_path and os.path.exists(execution.csv_file_path):
            email.attach_file(execution.csv_file_path, mimetype='text/csv')
        
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

def _gather_report_metrics(scheduled_report, report_date):
    """
    Gather metrics data for report generation
    
    Returns dict of metrics
    """
    metrics = {}
    
    property_obj = scheduled_report.property
    
    # Executive metrics
    exec_metrics = DashboardExecutiveMetrics.objects.filter(
        property=property_obj,
        metric_date=report_date
    ).first()
    
    if exec_metrics:
        metrics['total_revenue'] = float(exec_metrics.total_revenue or 0)
        metrics['avg_daily_rate'] = float(exec_metrics.avg_daily_rate or 0)
        metrics['occupancy_rate'] = float(exec_metrics.occupancy_rate or 0)
        metrics['revpar'] = float(exec_metrics.revpar or 0)
        metrics['booking_count'] = exec_metrics.booking_count
    
    # Revenue metrics
    revenue_metrics = DashboardRevenueMetrics.objects.filter(
        property=property_obj,
        metric_date=report_date
    ).first()
    
    if revenue_metrics:
        metrics['revenue_direct'] = float(revenue_metrics.revenue_direct or 0)
        metrics['revenue_ota'] = float(revenue_metrics.revenue_ota or 0)
        metrics['cancellation_rate'] = float(revenue_metrics.cancellation_rate or 0)
    
    # Guest analytics
    guest_analytics = DashboardGuestAnalytics.objects.filter(
        property=property_obj,
        analytics_date=report_date
    ).first()
    
    if guest_analytics:
        metrics['total_unique_guests'] = guest_analytics.total_unique_guests
        metrics['review_score'] = float(guest_analytics.avg_review_score or 0)
        metrics['nps'] = guest_analytics.avg_nps or 0
    
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
    from django.utils import timezone
    import pytz
    
    user_tz = pytz.timezone(scheduled_report.timezone)
    now_user_tz = timezone.now().astimezone(user_tz)
    
    schedule_time = scheduled_report.schedule_time
    
    # Create next scheduled datetime
    if scheduled_report.schedule_type == 'daily':
        next_date = now_user_tz.date() + timedelta(days=1)
        next_datetime = user_tz.localize(
            datetime.combine(next_date, schedule_time)
        )
    
    elif scheduled_report.schedule_type == 'weekly':
        dow = scheduled_report.schedule_dow or 0
        days_ahead = (dow - now_user_tz.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        next_date = now_user_tz.date() + timedelta(days=days_ahead)
        next_datetime = user_tz.localize(
            datetime.combine(next_date, schedule_time)
        )
    
    elif scheduled_report.schedule_type == 'monthly':
        day = scheduled_report.schedule_day or 1
        next_month = now_user_tz.date().replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=1)
        try:
            next_date = next_month.replace(day=day)
        except ValueError:
            # Handle cases like Feb 30
            next_date = next_month.replace(day=1) - timedelta(days=1)
        
        next_datetime = user_tz.localize(
            datetime.combine(next_date, schedule_time)
        )
    
    else:
        # Custom cron expression - set to 1 day from now
        next_datetime = timezone.now() + timedelta(days=1)
    
    # Convert to UTC
    scheduled_report.next_scheduled_at = next_datetime.astimezone(pytz.UTC)


def _gather_custom_report_rows(report):
    """Build row data for custom report generation."""
    metrics_qs = DashboardExecutiveMetrics.objects.filter(
        property=report.property,
        metric_date__gte=report.from_date,
        metric_date__lte=report.to_date,
    ).order_by('metric_date')

    rows = []
    for metric in metrics_qs:
        rows.append({
            'metric_date': metric.metric_date.isoformat(),
            'total_revenue': float(metric.total_revenue or 0),
            'avg_daily_rate': float(metric.avg_daily_rate or 0),
            'occupancy_rate': float(metric.occupancy_rate or 0),
            'revpar': float(metric.revpar or 0),
            'booking_count': metric.booking_count,
        })

    if not rows:
        rows.append({
            'metric_date': timezone.now().date().isoformat(),
            'total_revenue': 0,
            'avg_daily_rate': 0,
            'occupancy_rate': 0,
            'revpar': 0,
            'booking_count': 0,
        })

    return rows


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
