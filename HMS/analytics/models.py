"""
Analytics Data Models

Store pre-calculated dashboard metrics and analytics data for performance optimization.
"""

from django.db import models
from django.contrib.postgres.fields import JSONField
from properties.models import Property


class DashboardExecutiveMetrics(models.Model):
    """
    Executive dashboard metrics - strategic overview for hotel managers.
    
    Updated nightly by ETL process.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='executive_metrics')
    metric_date = models.DateField()
    
    # Executive KPIs
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    avg_daily_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    occupancy_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    revpar = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    booking_count = models.IntegerField(default=0)
    
    # Trends (JSON arrays for charts)
    revenue_trend_30d = models.JSONField(default=dict, blank=True)
    occupancy_trend_30d = models.JSONField(default=dict, blank=True)
    adr_trend_30d = models.JSONField(default=dict, blank=True)
    
    # Year-over-year comparison
    yoy_revenue_change = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    yoy_occupancy_change = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_executive_metrics'
        verbose_name = 'Executive Metrics'
        verbose_name_plural = 'Executive Metrics'
        unique_together = ('property', 'metric_date')
        indexes = [
            models.Index(fields=['property', 'metric_date']),
            models.Index(fields=['metric_date']),
        ]
    
    def __str__(self):
        return f"{self.property.name} - {self.metric_date}"


class DashboardOperationalStatus(models.Model):
    """
    Operational dashboard status - real-time operations overview.
    
    Updated in real-time for current operations tracking.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='operational_status')
    status_date = models.DateField()
    status_time = models.DateTimeField()
    
    # Room Status
    occupied_count = models.IntegerField(default=0)
    vacant_count = models.IntegerField(default=0)
    cleaning_count = models.IntegerField(default=0)
    maintenance_count = models.IntegerField(default=0)
    blocked_count = models.IntegerField(default=0)
    
    # Check-in/Check-out
    checkouts_scheduled = models.IntegerField(default=0)
    checkins_scheduled = models.IntegerField(default=0)
    
    # Task Status
    housekeeping_tasks_pending = models.IntegerField(default=0)
    housekeeping_tasks_in_progress = models.IntegerField(default=0)
    maintenance_tickets_pending = models.IntegerField(default=0)
    
    # Guest-related
    active_guests_count = models.IntegerField(default=0)
    guests_with_special_requests = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dashboard_operational_status'
        verbose_name = 'Operational Status'
        verbose_name_plural = 'Operational Statuses'
        indexes = [
            models.Index(fields=['property', 'status_date', 'status_time']),
            models.Index(fields=['property', 'status_date']),
        ]
    
    def __str__(self):
        return f"{self.property.name} - {self.status_time}"


class DashboardRevenueMetrics(models.Model):
    """
    Revenue analytics dashboard metrics - financial performance data.
    
    Updated nightly by ETL process.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='revenue_metrics')
    metric_date = models.DateField()
    
    # Revenue
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    revenue_direct = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    revenue_ota = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    revenue_agency = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Pricing
    avg_daily_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    revpar = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dynamic_pricing_uplift = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Occupancy
    occupancy_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    occupancy_count = models.IntegerField(null=True, blank=True)
    
    # Bookings
    booking_count = models.IntegerField(default=0)
    cancellation_count = models.IntegerField(default=0)
    cancellation_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    noshow_count = models.IntegerField(default=0)
    
    # Forecast
    revenue_forecast_30d = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    occupancy_forecast_30d = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Detailed breakdown by source
    metrics_by_source = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_revenue_metrics'
        verbose_name = 'Revenue Metrics'
        verbose_name_plural = 'Revenue Metrics'
        unique_together = ('property', 'metric_date')
        indexes = [
            models.Index(fields=['property', 'metric_date']),
            models.Index(fields=['metric_date']),
        ]
    
    def __str__(self):
        return f"{self.property.name} - {self.metric_date} - {self.total_revenue}"


class DashboardGuestAnalytics(models.Model):
    """
    Guest analytics dashboard - guest insights and personalization data.
    
    Updated nightly by ETL process.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='guest_analytics')
    analytics_date = models.DateField()
    
    # Guest counts
    total_unique_guests = models.IntegerField(default=0)
    new_guests = models.IntegerField(default=0)
    returning_guests = models.IntegerField(default=0)
    repeat_booking_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Behavior
    avg_booking_lead_days = models.IntegerField(null=True, blank=True)
    avg_length_of_stay = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Satisfaction
    avg_review_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    avg_nps = models.IntegerField(null=True, blank=True)
    review_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    complaint_count = models.IntegerField(default=0)
    complaint_resolution_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Churn
    retention_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    churn_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    at_risk_guests = models.IntegerField(default=0)
    
    # Personalization
    recommendations_generated = models.IntegerField(default=0)
    recommendations_accepted = models.IntegerField(default=0)
    upsell_conversions = models.IntegerField(default=0)
    cross_sell_conversions = models.IntegerField(default=0)
    personalization_revenue_uplift = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Detailed breakdowns
    guest_segments = models.JSONField(default=dict, blank=True)
    geographic_breakdown = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dashboard_guest_analytics'
        verbose_name = 'Guest Analytics'
        verbose_name_plural = 'Guest Analytics'
        indexes = [
            models.Index(fields=['property', 'analytics_date']),
            models.Index(fields=['analytics_date']),
        ]
    
    def __str__(self):
        return f"{self.property.name} - {self.analytics_date}"


class CustomReport(models.Model):
    """
    Custom analytics reports - user-defined reports for export.
    """
    REPORT_TYPES = (
        ('revenue', 'Revenue Report'),
        ('occupancy', 'Occupancy Report'),
        ('guest', 'Guest Analytics Report'),
        ('pricing', 'Pricing Analysis Report'),
        ('custom', 'Custom Report'),
    )
    
    EXPORT_FORMATS = (
        ('pdf', 'PDF'),
        ('excel', 'Excel (XLSX)'),
        ('csv', 'CSV'),
    )
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='custom_reports')
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='reports_created')
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    
    # Date range
    from_date = models.DateField()
    to_date = models.DateField()
    
    # Configuration
    include_charts = models.BooleanField(default=True)
    include_summary = models.BooleanField(default=True)
    include_detailed_data = models.BooleanField(default=True)
    
    # Output
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS, default='pdf')
    file_path = models.CharField(max_length=500, blank=True, null=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('generated', 'Generated'), ('failed', 'Failed')],
        default='pending'
    )
    generated_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'custom_reports'
        verbose_name = 'Custom Report'
        verbose_name_plural = 'Custom Reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.report_type})"

class ScheduledReport(models.Model):
    """
    Scheduled automated reports configuration.
    
    Reports are generated on a schedule and delivered via email.
    """
    SCHEDULE_TYPES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom Cron'),
    )
    
    REPORT_TYPES = (
        ('daily_operational', 'Daily Operational Dashboard'),
        ('daily_finance', 'Daily Finance Report'),
        ('weekly_performance', 'Weekly Performance Report'),
        ('weekly_marketing', 'Weekly Marketing Report'),
        ('monthly_executive', 'Monthly Executive Summary'),
        ('monthly_occupancy', 'Monthly Occupancy Analysis'),
        ('compliance', 'Compliance Report'),
        ('custom', 'Custom Report'),
    )
    
    EXPORT_FORMATS = (
        ('pdf', 'PDF'),
        ('excel', 'Excel (XLSX)'),
        ('csv', 'CSV'),
    )
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='scheduled_reports')
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='scheduled_reports_created')
    
    # Basic Info
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    
    # Scheduling
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES)
    schedule_day = models.IntegerField(null=True, blank=True, help_text="Day of month for monthly reports (1-31)")
    schedule_dow = models.IntegerField(null=True, blank=True, help_text="Day of week for weekly reports (0=Monday, 6=Sunday)")
    schedule_time = models.TimeField(help_text="Time to generate report (UTC)")
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Recipients
    recipient_emails = models.JSONField(default=list, help_text="Array of email addresses")
    include_managers = models.BooleanField(default=True)
    include_owner = models.BooleanField(default=False)
    
    # Configuration
    include_charts = models.BooleanField(default=True)
    include_summary = models.BooleanField(default=True)
    include_detailed_data = models.BooleanField(default=True)
    custom_filters = models.JSONField(default=dict, blank=True)
    metric_selection = models.JSONField(default=dict, blank=True)
    
    # Output
    export_formats = models.JSONField(
        default=list,
        help_text="Export formats: pdf, excel, csv"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_generated_at = models.DateTimeField(null=True, blank=True)
    next_scheduled_at = models.DateTimeField(null=True, blank=True)
    consecutive_failures = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'scheduled_reports'
        verbose_name = 'Scheduled Report'
        verbose_name_plural = 'Scheduled Reports'
        unique_together = ('property', 'name')
        ordering = ['is_active', 'schedule_time']
        indexes = [
            models.Index(fields=['property', 'is_active']),
            models.Index(fields=['next_scheduled_at']),
            models.Index(fields=['is_active', 'next_scheduled_at']),
        ]
    
    def __str__(self):
        return f"{self.property.name} - {self.name}"


class ReportExecution(models.Model):
    """
    Track each execution of a scheduled report.
    
    Records status, generated files, and delivery information.
    """
    EXECUTION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('generated', 'Generated'),
        ('failed', 'Failed'),
    )
    
    EMAIL_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('error', 'Error'),
    )
    
    scheduled_report = models.ForeignKey(ScheduledReport, on_delete=models.CASCADE, related_name='executions')
    
    # Status
    execution_status = models.CharField(
        max_length=20,
        choices=EXECUTION_STATUS_CHOICES,
        default='pending'
    )
    
    # Generated files
    pdf_file_path = models.CharField(max_length=500, blank=True, null=True)
    excel_file_path = models.CharField(max_length=500, blank=True, null=True)
    csv_file_path = models.CharField(max_length=500, blank=True, null=True)
    
    # Email delivery
    email_status = models.CharField(
        max_length=20,
        choices=EMAIL_STATUS_CHOICES,
        default='pending',
        blank=True
    )
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_recipients = models.JSONField(default=list)
    
    # Data and metrics
    data_date_from = models.DateField()
    data_date_to = models.DateField()
    metrics_snapshot = models.JSONField(default=dict, help_text="Snapshot of KPIs for this report")
    
    # Performance
    execution_time_seconds = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'report_executions'
        verbose_name = 'Report Execution'
        verbose_name_plural = 'Report Executions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['scheduled_report', '-created_at']),
            models.Index(fields=['execution_status']),
            models.Index(fields=['email_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.scheduled_report.name} - {self.created_at.date()}"


class ReportDeliveryTracking(models.Model):
    """
    Track email delivery status and engagement metrics for reports.
    
    Integrates with email provider webhooks to track opens and clicks.
    """
    DELIVERY_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('bounced', 'Bounced'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('failed', 'Failed'),
    )
    
    report_execution = models.ForeignKey(ReportExecution, on_delete=models.CASCADE, related_name='delivery_tracking')
    
    recipient_email = models.EmailField()
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default='pending'
    )
    
    # Engagement metrics
    opened_at = models.DateTimeField(null=True, blank=True)
    click_count = models.IntegerField(default=0)
    last_clicked_at = models.DateTimeField(null=True, blank=True)
    
    # Email provider info
    email_provider_id = models.CharField(max_length=255, blank=True, help_text="SendGrid message ID or similar")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'report_delivery_tracking'
        verbose_name = 'Report Delivery Tracking'
        verbose_name_plural = 'Report Delivery Tracking'
        unique_together = ('report_execution', 'recipient_email')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_execution']),
            models.Index(fields=['recipient_email']),
            models.Index(fields=['delivery_status']),
            models.Index(fields=['opened_at']),
        ]
    
    def __str__(self):
        return f"{self.recipient_email} - {self.delivery_status}"


# ============================================================================
# FORECASTING MODELS - Predictive Analytics
# ============================================================================

class OccupancyForecast(models.Model):
    """
    Occupancy forecasting using Prophet and SARIMA time-series models.
    
    Stores predicted occupancy rates for next 7, 14, 30 days.
    Updated daily as new bookings arrive.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='occupancy_forecasts')
    
    # Forecast dates
    forecast_date = models.DateField(help_text="Date when forecast was generated")
    target_date = models.DateField(help_text="Date being forecasted")
    
    # Predictions and confidence intervals
    predicted_occupancy = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Predicted occupancy % (0-100)"
    )
    lower_bound = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="95% confidence interval lower bound"
    )
    upper_bound = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="95% confidence interval upper bound"
    )
    
    # Model info
    model_type = models.CharField(
        max_length=20,
        choices=[('prophet', 'Prophet'), ('sarima', 'SARIMA'), ('ensemble', 'Ensemble')],
        default='prophet'
    )
    
    # Actual vs forecast (populated after target date)
    actual_occupancy = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Actual occupancy after target date passed"
    )
    forecast_error = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Error = actual - predicted"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'occupancy_forecasts'
        verbose_name = 'Occupancy Forecast'
        verbose_name_plural = 'Occupancy Forecasts'
        unique_together = ('property', 'forecast_date', 'target_date', 'model_type')
        indexes = [
            models.Index(fields=['property', 'target_date']),
            models.Index(fields=['property', 'forecast_date']),
            models.Index(fields=['target_date']),
        ]
    
    def __str__(self):
        return f"{self.property.name} - {self.target_date}: {self.predicted_occupancy}% (±{self.upper_bound - self.predicted_occupancy}%)"


class RevenueForecast(models.Model):
    """
    Revenue forecasting using Prophet time-series model.
    
    Predicts daily/weekly revenue for next 7, 14, 30 days.
    Updated daily as pricing and bookings change.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='revenue_forecasts')
    
    # Forecast dates
    forecast_date = models.DateField(help_text="Date when forecast was generated")
    target_date = models.DateField(help_text="Date being forecasted")
    
    # Predictions and confidence intervals
    predicted_revenue = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Predicted revenue (in base currency)"
    )
    lower_bound = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="95% confidence interval lower bound"
    )
    upper_bound = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="95% confidence interval upper bound"
    )
    
    # Model info
    model_type = models.CharField(
        max_length=20,
        choices=[('prophet', 'Prophet'), ('sarima', 'SARIMA'), ('ensemble', 'Ensemble')],
        default='prophet'
    )
    
    # Revenue drivers
    predicted_occupancy = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Predicted occupancy used for forecast"
    )
    avg_daily_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="ADR used for revenue forecast"
    )
    num_rooms = models.IntegerField(null=True, blank=True, help_text="Number of rooms")
    
    # Actual vs forecast
    actual_revenue = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Actual revenue after target date passed"
    )
    forecast_error = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Error = actual - predicted"
    )
    forecast_error_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Error as percentage of predicted"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'revenue_forecasts'
        verbose_name = 'Revenue Forecast'
        verbose_name_plural = 'Revenue Forecasts'
        unique_together = ('property', 'forecast_date', 'target_date', 'model_type')
        indexes = [
            models.Index(fields=['property', 'target_date']),
            models.Index(fields=['property', 'forecast_date']),
            models.Index(fields=['target_date']),
        ]
    
    def __str__(self):
        return f"{self.property.name} - {self.target_date}: ${self.predicted_revenue:.2f}"


class CancellationPrediction(models.Model):
    """
    Cancellation risk prediction using XGBoost classification model.
    
    Predicts probability of booking cancellation (0-100).
    Updated for each new booking and as booking date approaches.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='cancellation_predictions')
    booking = models.ForeignKey(
        'room.Booking', on_delete=models.CASCADE,
        related_name='cancellation_prediction', null=True, blank=True
    )
    
    # Prediction info
    prediction_date = models.DateField(help_text="Date prediction was made")
    prediction_time = models.DateTimeField(help_text="Time prediction was made")
    
    # Risk scoring
    cancellation_risk_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Risk score 0-100 (higher = more likely to cancel)"
    )
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low Risk (<40%)'),
            ('medium', 'Medium Risk (40-65%)'),
            ('high', 'High Risk (>65%)')
        ]
    )
    
    # Features used
    lead_time_days = models.IntegerField(null=True, blank=True)
    booking_source = models.CharField(max_length=50, null=True, blank=True)
    customer_type = models.CharField(max_length=50, null=True, blank=True)
    refund_policy = models.CharField(max_length=50, null=True, blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Model info
    model_version = models.CharField(max_length=50, default='v1.0')
    
    # Actual outcome
    actually_cancelled = models.BooleanField(null=True, blank=True)
    cancellation_date = models.DateField(null=True, blank=True)
    
    # Actions taken
    intervention_flag = models.BooleanField(
        default=False,
        help_text="Whether automated intervention (email, offer) was triggered"
    )
    intervention_type = models.CharField(
        max_length=100, null=True, blank=True,
        choices=[
            ('confirmation_email', 'Confirmation Email'),
            ('special_offer', 'Special Offer'),
            ('vip_treatment', 'VIP Treatment'),
            ('increased_overbooking', 'Increased Overbooking'),
        ]
    )
    intervention_result = models.CharField(
        max_length=50, null=True, blank=True,
        choices=[('success', 'Prevented Cancellation'), ('failed', 'Still Cancelled')]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cancellation_predictions'
        verbose_name = 'Cancellation Prediction'
        verbose_name_plural = 'Cancellation Predictions'
        indexes = [
            models.Index(fields=['property', 'prediction_date']),
            models.Index(fields=['booking', 'prediction_date']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['cancellation_risk_score']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_id or 'N/A'}: {self.cancellation_risk_score}% ({self.risk_level})"


class NoShowPrediction(models.Model):
    """
    No-show risk prediction using XGBoost classification model.
    
    Predicts probability of guest not arriving (0-100).
    Used for overbooking optimization and room allocation.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='noshow_predictions')
    booking = models.ForeignKey(
        'room.Booking', on_delete=models.CASCADE,
        related_name='noshow_prediction', null=True, blank=True
    )
    
    # Prediction info
    prediction_date = models.DateField(help_text="Date prediction was made")
    prediction_time = models.DateTimeField(help_text="Time prediction was made")
    
    # Risk scoring
    noshow_risk_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Risk score 0-100 (higher = more likely to no-show)"
    )
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low Risk (<20%)'),
            ('medium', 'Medium Risk (20-40%)'),
            ('high', 'High Risk (>40%)')
        ]
    )
    
    # Features used
    customer_country = models.CharField(max_length=100, null=True, blank=True)
    booking_source = models.CharField(max_length=50, null=True, blank=True)
    payment_confirmed = models.BooleanField(null=True, blank=True)
    advance_checkin_days = models.IntegerField(null=True, blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    special_requests_count = models.IntegerField(null=True, blank=True)
    
    # Model info
    model_version = models.CharField(max_length=50, default='v1.0')
    
    # Actual outcome
    actually_noshow = models.BooleanField(null=True, blank=True)
    checked_in_date = models.DateField(null=True, blank=True)
    
    # Overbooking strategy
    overbooking_flag = models.BooleanField(
        default=False,
        help_text="Whether room was overbooked due to high no-show risk"
    )
    overbooking_factor = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
        choices=[(1.0, '100% allocation'), (1.05, '105% allocation'), (1.10, '110% allocation')],
        help_text="Overbooking percentage applied"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'noshow_predictions'
        verbose_name = 'No-Show Prediction'
        verbose_name_plural = 'No-Show Predictions'
        indexes = [
            models.Index(fields=['property', 'prediction_date']),
            models.Index(fields=['booking', 'prediction_date']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['noshow_risk_score']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_id or 'N/A'}: {self.noshow_risk_score}% ({self.risk_level})"


class ForecastingModelMetrics(models.Model):
    """
    Track forecasting model performance metrics over time.
    
    Used for model monitoring, drift detection, and performance validation.
    Updated daily after comparisons between predictions and actuals.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='forecast_metrics')
    
    # Model identification
    model_name = models.CharField(
        max_length=100,
        choices=[
            ('occupancy_prophet', 'Occupancy (Prophet)'),
            ('occupancy_sarima', 'Occupancy (SARIMA)'),
            ('revenue_prophet', 'Revenue (Prophet)'),
            ('cancellation_xgb', 'Cancellation Prediction (XGBoost)'),
            ('noshow_xgb', 'No-Show Prediction (XGBoost)'),
        ]
    )
    
    evaluation_date = models.DateField(help_text="Date of performance evaluation")
    evaluation_period = models.CharField(
        max_length=20,
        choices=[
            ('7day', 'Last 7 days'),
            ('14day', 'Last 14 days'),
            ('30day', 'Last 30 days'),
            ('90day', 'Last 90 days'),
        ],
        default='30day'
    )
    
    # Time series metrics (for forecasting models)
    mae = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True,
        help_text="Mean Absolute Error"
    )
    rmse = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True,
        help_text="Root Mean Squared Error"
    )
    mape = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Mean Absolute Percentage Error (%)"
    )
    r_squared = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True,
        help_text="R-squared coefficient"
    )
    
    # Classification metrics (for prediction models)
    precision = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True,
        help_text="Precision (True Positives / (True Positives + False Positives))"
    )
    recall = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True,
        help_text="Recall (True Positives / (True Positives + False Negatives))"
    )
    f1_score = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True,
        help_text="F1 Score (harmonic mean of precision and recall)"
    )
    roc_auc = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True,
        help_text="ROC-AUC score"
    )
    
    # Data volume
    predictions_count = models.IntegerField(default=0, help_text="Number of predictions evaluated")
    
    # Status
    is_acceptable = models.BooleanField(
        default=True,
        help_text="Whether model performance is within acceptable thresholds"
    )
    needs_retraining = models.BooleanField(
        default=False,
        help_text="Whether model should be retrained due to performance degradation"
    )
    
    # Notes
    notes = models.TextField(blank=True, help_text="Any remarks about model performance")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'forecasting_model_metrics'
        verbose_name = 'Forecasting Model Metrics'
        verbose_name_plural = 'Forecasting Model Metrics'
        unique_together = ('property', 'model_name', 'evaluation_date')
        indexes = [
            models.Index(fields=['property', 'model_name', '-evaluation_date']),
            models.Index(fields=['model_name', '-evaluation_date']),
            models.Index(fields=['is_acceptable', 'needs_retraining']),
        ]
    
    def __str__(self):
        return f"{self.property.name} - {self.model_name} ({self.evaluation_date})"