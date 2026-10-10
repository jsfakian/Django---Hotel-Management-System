"""
Analytics Serializers

Serializes analytics data for API responses.
"""

from rest_framework import serializers
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


class DashboardExecutiveMetricsSerializer(serializers.ModelSerializer):
    """Serializer for Executive Dashboard metrics"""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = DashboardExecutiveMetrics
        fields = [
            'id',
            'property',
            'property_name',
            'metric_date',
            'total_revenue',
            'avg_daily_rate',
            'occupancy_rate',
            'revpar',
            'booking_count',
            'revenue_trend_30d',
            'occupancy_trend_30d',
            'adr_trend_30d',
            'yoy_revenue_change',
            'yoy_occupancy_change',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DashboardOperationalStatusSerializer(serializers.ModelSerializer):
    """Serializer for Operational Dashboard status"""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    total_rooms = serializers.SerializerMethodField()
    occupancy_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = DashboardOperationalStatus
        fields = [
            'id',
            'property',
            'property_name',
            'status_date',
            'status_time',
            'occupied_count',
            'vacant_count',
            'cleaning_count',
            'maintenance_count',
            'blocked_count',
            'total_rooms',
            'occupancy_percentage',
            'checkouts_scheduled',
            'checkins_scheduled',
            'housekeeping_tasks_pending',
            'housekeeping_tasks_in_progress',
            'maintenance_tickets_pending',
            'active_guests_count',
            'guests_with_special_requests',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_total_rooms(self, obj) -> int:
        """Calculate total rooms"""
        return (obj.occupied_count + obj.vacant_count + 
                obj.cleaning_count + obj.maintenance_count + obj.blocked_count)
    
    def get_occupancy_percentage(self, obj) -> float:
        """Calculate occupancy percentage"""
        total = self.get_total_rooms(obj)
        if total == 0:
            return 0
        return round((obj.occupied_count / total) * 100, 2)


class DashboardRevenueMetricsSerializer(serializers.ModelSerializer):
    """Serializer for Revenue Analytics dashboard"""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = DashboardRevenueMetrics
        fields = [
            'id',
            'property',
            'property_name',
            'metric_date',
            'total_revenue',
            'revenue_direct',
            'revenue_ota',
            'revenue_agency',
            'avg_daily_rate',
            'revpar',
            'dynamic_pricing_uplift',
            'occupancy_rate',
            'occupancy_count',
            'booking_count',
            'cancellation_count',
            'cancellation_rate',
            'noshow_count',
            'revenue_forecast_30d',
            'occupancy_forecast_30d',
            'metrics_by_source',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DashboardGuestAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for Guest Analytics dashboard"""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = DashboardGuestAnalytics
        fields = [
            'id',
            'property',
            'property_name',
            'analytics_date',
            'total_unique_guests',
            'new_guests',
            'returning_guests',
            'repeat_booking_rate',
            'avg_booking_lead_days',
            'avg_length_of_stay',
            'avg_review_score',
            'avg_nps',
            'review_rate',
            'complaint_count',
            'complaint_resolution_rate',
            'retention_rate',
            'churn_rate',
            'at_risk_guests',
            'recommendations_generated',
            'recommendations_accepted',
            'upsell_conversions',
            'cross_sell_conversions',
            'personalization_revenue_uplift',
            'guest_segments',
            'geographic_breakdown',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CustomReportSerializer(serializers.ModelSerializer):
    """Serializer for Custom Reports"""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = CustomReport
        fields = [
            'id',
            'property',
            'property_name',
            'created_by',
            'created_by_name',
            'name',
            'description',
            'report_type',
            'from_date',
            'to_date',
            'include_charts',
            'include_summary',
            'include_detailed_data',
            'export_format',
            'file_path',
            'status',
            'error_message',
            'generated_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_by',
            'file_path',
            'status',
            'error_message',
            'generated_at',
            'created_at',
            'updated_at',
        ]


# Summary Serializers for Dashboard Views

class DashboardSummarySerializer(serializers.Serializer):
    """Combined dashboard summary data"""
    
    executive_metrics = DashboardExecutiveMetricsSerializer()
    operational_status = DashboardOperationalStatusSerializer()
    revenue_metrics = DashboardRevenueMetricsSerializer()
    guest_analytics = DashboardGuestAnalyticsSerializer()


class AnalyticsExportSerializer(serializers.Serializer):
    """Input serializer for analytics export"""
    
    report_type = serializers.ChoiceField(
        choices=['revenue', 'occupancy', 'guest', 'custom'],
        required=True
    )
    from_date = serializers.DateField(required=True)
    to_date = serializers.DateField(required=True)
    export_format = serializers.ChoiceField(
        choices=['pdf', 'excel', 'csv'],
        default='pdf'
    )
    include_charts = serializers.BooleanField(default=True)
    include_summary = serializers.BooleanField(default=True)


class MetricComparisonSerializer(serializers.Serializer):
    """Serializer for comparing metrics across properties"""
    
    metric = serializers.CharField(required=True)
    period = serializers.ChoiceField(choices=['day', 'week', 'month', 'quarter', 'year'])
    property_ids = serializers.ListField(child=serializers.IntegerField())
    
    comparison_data = serializers.JSONField(read_only=True)
    summary_stats = serializers.JSONField(read_only=True)


# Automated Reporting Serializers

class ReportDeliveryTrackingSerializer(serializers.ModelSerializer):
    """Serializer for report delivery tracking"""
    
    class Meta:
        model = ReportDeliveryTracking
        fields = [
            'id',
            'recipient_email',
            'delivery_status',
            'opened_at',
            'click_count',
            'last_clicked_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReportExecutionSerializer(serializers.ModelSerializer):
    """Serializer for report execution records"""
    
    scheduled_report_name = serializers.CharField(source='scheduled_report.name', read_only=True)
    delivery_tracking = ReportDeliveryTrackingSerializer(many=True, read_only=True)
    
    class Meta:
        model = ReportExecution
        fields = [
            'id',
            'scheduled_report',
            'scheduled_report_name',
            'execution_status',
            'email_status',
            'pdf_file_path',
            'excel_file_path',
            'csv_file_path',
            'data_date_from',
            'data_date_to',
            'metrics_snapshot',
            'execution_time_seconds',
            'email_sent_at',
            'email_recipients',
            'error_message',
            'delivery_tracking',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'execution_status',
            'email_status',
            'pdf_file_path',
            'excel_file_path',
            'csv_file_path',
            'execution_time_seconds',
            'email_sent_at',
            'error_message',
            'created_at',
            'updated_at',
        ]


class ScheduledReportSerializer(serializers.ModelSerializer):
    """Serializer for scheduled report configuration"""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    executions = ReportExecutionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ScheduledReport
        fields = [
            'id',
            'property',
            'property_name',
            'name',
            'description',
            'report_type',
            'schedule_type',
            'schedule_day',
            'schedule_dow',
            'schedule_time',
            'timezone',
            'recipient_emails',
            'include_managers',
            'include_owner',
            'include_charts',
            'include_summary',
            'include_detailed_data',
            'custom_filters',
            'metric_selection',
            'export_formats',
            'is_active',
            'last_generated_at',
            'next_scheduled_at',
            'consecutive_failures',
            'created_by',
            'created_by_name',
            'executions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'last_generated_at',
            'next_scheduled_at',
            'consecutive_failures',
            'created_by',
            'executions',
            'created_at',
            'updated_at',
        ]


class ScheduledReportCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating scheduled reports"""
    
    class Meta:
        model = ScheduledReport
        fields = [
            'property',
            'name',
            'description',
            'report_type',
            'schedule_type',
            'schedule_day',
            'schedule_dow',
            'schedule_time',
            'timezone',
            'recipient_emails',
            'include_managers',
            'include_owner',
            'include_charts',
            'include_summary',
            'include_detailed_data',
            'custom_filters',
            'metric_selection',
            'export_formats',
            'is_active',
        ]


class ReportExecutionTriggerSerializer(serializers.Serializer):
    """Serializer for triggering manual report execution"""
    
    override_recipients = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        help_text="Override scheduled recipients for this execution"
    )


class ReportResendSerializer(serializers.Serializer):
    """Serializer for resending generated report"""
    
    report_exec_id = serializers.IntegerField(required=True)
    override_recipients = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        help_text="Override original recipients"
    )


# ============================================================================
# FORECASTING SERIALIZERS
# ============================================================================

class OccupancyForecastSerializer(serializers.ModelSerializer):
    """Serializer for occupancy forecasting results"""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    days_ahead = serializers.SerializerMethodField()
    
    class Meta:
        from .models import OccupancyForecast
        model = OccupancyForecast
        fields = [
            'id',
            'property',
            'property_name',
            'forecast_date',
            'target_date',
            'days_ahead',
            'predicted_occupancy',
            'lower_bound',
            'upper_bound',
            'model_type',
            'actual_occupancy',
            'forecast_error',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_days_ahead(self, obj) -> int:
        """Calculate days between forecast date and target date"""
        return (obj.target_date - obj.forecast_date).days


class RevenueForecastSerializer(serializers.ModelSerializer):
    """Serializer for revenue forecasting results"""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    days_ahead = serializers.SerializerMethodField()
    
    class Meta:
        from .models import RevenueForecast
        model = RevenueForecast
        fields = [
            'id',
            'property',
            'property_name',
            'forecast_date',
            'target_date',
            'days_ahead',
            'predicted_revenue',
            'lower_bound',
            'upper_bound',
            'model_type',
            'predicted_occupancy',
            'avg_daily_rate',
            'num_rooms',
            'actual_revenue',
            'forecast_error',
            'forecast_error_pct',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_days_ahead(self, obj) -> int:
        """Calculate days between forecast date and target date"""
        return (obj.target_date - obj.forecast_date).days


class CancellationPredictionSerializer(serializers.ModelSerializer):
    """Serializer for cancellation risk predictions"""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    booking_id = serializers.CharField(source='booking.id', read_only=True, allow_null=True)
    days_to_checkin = serializers.SerializerMethodField()
    
    class Meta:
        from .models import CancellationPrediction
        model = CancellationPrediction
        fields = [
            'id',
            'property',
            'property_name',
            'booking_id',
            'prediction_date',
            'prediction_time',
            'cancellation_risk_score',
            'risk_level',
            'days_to_checkin',
            'lead_time_days',
            'booking_source',
            'customer_type',
            'refund_policy',
            'price_per_night',
            'model_version',
            'actually_cancelled',
            'cancellation_date',
            'intervention_flag',
            'intervention_type',
            'intervention_result',
        ]
        read_only_fields = ['id', 'prediction_date', 'prediction_time']
    
    def get_days_to_checkin(self, obj) -> int | None:
        """Calculate days until check-in if booking exists"""
        if obj.booking and obj.booking.check_in_date:
            from datetime import date
            return (obj.booking.check_in_date - date.today()).days
        return None


class NoShowPredictionSerializer(serializers.ModelSerializer):
    """Serializer for no-show risk predictions"""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    booking_id = serializers.CharField(source='booking.id', read_only=True, allow_null=True)
    days_to_checkin = serializers.SerializerMethodField()
    
    class Meta:
        from .models import NoShowPrediction
        model = NoShowPrediction
        fields = [
            'id',
            'property',
            'property_name',
            'booking_id',
            'prediction_date',
            'prediction_time',
            'noshow_risk_score',
            'risk_level',
            'days_to_checkin',
            'customer_country',
            'booking_source',
            'payment_confirmed',
            'advance_checkin_days',
            'price_per_night',
            'special_requests_count',
            'model_version',
            'actually_noshow',
            'checked_in_date',
            'overbooking_flag',
            'overbooking_factor',
        ]
        read_only_fields = ['id', 'prediction_date', 'prediction_time']
    
    def get_days_to_checkin(self, obj) -> int | None:
        """Calculate days until check-in if booking exists"""
        if obj.booking and obj.booking.check_in_date:
            from datetime import date
            return (obj.booking.check_in_date - date.today()).days
        return None


class ForecastingModelMetricsSerializer(serializers.ModelSerializer):
    """Serializer for forecasting model performance metrics"""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    model_display = serializers.CharField(source='get_model_name_display', read_only=True)
    
    class Meta:
        from .models import ForecastingModelMetrics
        model = ForecastingModelMetrics
        fields = [
            'id',
            'property',
            'property_name',
            'model_name',
            'model_display',
            'evaluation_date',
            'evaluation_period',
            'mae',
            'rmse',
            'mape',
            'r_squared',
            'precision',
            'recall',
            'f1_score',
            'roc_auc',
            'predictions_count',
            'is_acceptable',
            'needs_retraining',
            'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# Summary/Dashboard Serializers for Forecasting

class ForecastingSummarySerializer(serializers.Serializer):
    """Serializer for forecasting summary view across all predictions"""
    
    property_id = serializers.IntegerField()
    occupancy_forecast_7d = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    occupancy_forecast_30d = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    revenue_forecast_7d = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    revenue_forecast_30d = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    
    high_risk_cancellations = serializers.IntegerField()
    high_risk_noshows = serializers.IntegerField()
    
    model_health_status = serializers.CharField(help_text="green/yellow/red based on metrics")
    models_needing_retraining = serializers.ListField(child=serializers.CharField())


class ForecastingAlertSerializer(serializers.Serializer):
    """Serializer for forecasting alerts and anomalies"""
    
    alert_type = serializers.ChoiceField(
        choices=[
            'low_occupancy_forecast',
            'low_revenue_forecast',
            'high_cancellation_risk',
            'model_performance_degradation',
            'unusual_pattern_detected'
        ]
    )
    severity = serializers.ChoiceField(choices=['info', 'warning', 'critical'])
    message = serializers.CharField()
    affected_property = serializers.IntegerField()
    forecast_date = serializers.DateField()
    recommended_action = serializers.CharField()