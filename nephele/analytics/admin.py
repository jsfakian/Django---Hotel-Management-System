"""
Analytics Admin Configuration
"""

from django.contrib import admin
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


@admin.register(DashboardExecutiveMetrics)
class ExecutiveMetricsAdmin(admin.ModelAdmin):
    list_display = ('property', 'metric_date', 'total_revenue', 'occupancy_rate', 'revpar')
    list_filter = ('property', 'metric_date', 'occupancy_rate')
    search_fields = ('property__name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Property & Date', {
            'fields': ('property', 'metric_date')
        }),
        ('KPIs', {
            'fields': (
                'total_revenue',
                'avg_daily_rate',
                'occupancy_rate',
                'revpar',
                'booking_count'
            )
        }),
        ('Trends', {
            'fields': (
                'revenue_trend_30d',
                'occupancy_trend_30d',
                'adr_trend_30d'
            )
        }),
        ('Year-over-year', {
            'fields': (
                'yoy_revenue_change',
                'yoy_occupancy_change'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DashboardOperationalStatus)
class OperationalStatusAdmin(admin.ModelAdmin):
    list_display = (
        'property',
        'status_date',
        'occupied_count',
        'vacant_count',
        'cleaning_count'
    )
    list_filter = ('property', 'status_date')
    search_fields = ('property__name',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Property & Time', {
            'fields': ('property', 'status_date', 'status_time')
        }),
        ('Room Status', {
            'fields': (
                'occupied_count',
                'vacant_count',
                'cleaning_count',
                'maintenance_count',
                'blocked_count'
            )
        }),
        ('Check-in/Check-out', {
            'fields': ('checkouts_scheduled', 'checkins_scheduled')
        }),
        ('Tasks', {
            'fields': (
                'housekeeping_tasks_pending',
                'housekeeping_tasks_in_progress',
                'maintenance_tickets_pending'
            )
        }),
        ('Guests', {
            'fields': ('active_guests_count', 'guests_with_special_requests')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(DashboardRevenueMetrics)
class RevenueMetricsAdmin(admin.ModelAdmin):
    list_display = (
        'property',
        'metric_date',
        'total_revenue',
        'avg_daily_rate',
        'occupancy_rate'
    )
    list_filter = ('property', 'metric_date', 'occupancy_rate')
    search_fields = ('property__name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DashboardGuestAnalytics)
class GuestAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'property',
        'analytics_date',
        'total_unique_guests',
        'retention_rate',
        'avg_review_score'
    )
    list_filter = ('property', 'analytics_date')
    search_fields = ('property__name',)
    readonly_fields = ('created_at',)


@admin.register(CustomReport)
class CustomReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'property', 'report_type', 'status', 'created_at')
    list_filter = ('report_type', 'status', 'created_at', 'property')
    search_fields = ('name', 'property__name')
    readonly_fields = ('created_by', 'generated_at', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Report Details', {
            'fields': ('name', 'description', 'property', 'report_type')
        }),
        ('Configuration', {
            'fields': (
                'from_date',
                'to_date',
                'include_charts',
                'include_summary',
                'include_detailed_data'
            )
        }),
        ('Output', {
            'fields': ('export_format', 'file_path')
        }),
        ('Status', {
            'fields': ('status', 'error_message', 'generated_at')
        }),
        ('Meta', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Automated Reporting Admin

@admin.register(ScheduledReport)
class ScheduledReportAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'property',
        'report_type',
        'schedule_type',
        'schedule_time',
        'is_active',
        'last_generated_at',
        'consecutive_failures'
    )
    list_filter = ('report_type', 'schedule_type', 'is_active', 'property', 'created_at')
    search_fields = ('name', 'description', 'property__name')
    readonly_fields = (
        'created_by',
        'last_generated_at',
        'next_scheduled_at',
        'consecutive_failures',
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Report Configuration', {
            'fields': ('property', 'name', 'description', 'report_type')
        }),
        ('Schedule', {
            'fields': (
                'schedule_type',
                'schedule_day',
                'schedule_dow',
                'schedule_time',
                'timezone'
            )
        }),
        ('Recipients', {
            'fields': ('recipient_emails', 'include_managers', 'include_owner')
        }),
        ('Content & Output', {
            'fields': (
                'include_charts',
                'include_summary',
                'include_detailed_data',
                'custom_filters',
                'metric_selection',
                'export_formats'
            )
        }),
        ('Status & Scheduling', {
            'fields': (
                'is_active',
                'last_generated_at',
                'next_scheduled_at',
                'consecutive_failures'
            )
        }),
        ('Meta', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ReportDeliveryTrackingInline(admin.TabularInline):
    model = ReportDeliveryTracking
    readonly_fields = ('recipient_email', 'delivery_status', 'opened_at', 'click_count', 'created_at')
    extra = 0
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ReportExecution)
class ReportExecutionAdmin(admin.ModelAdmin):
    list_display = (
        'scheduled_report',
        'execution_status',
        'email_status',
        'data_date_from',
        'email_sent_at',
        'execution_time_seconds'
    )
    list_filter = ('execution_status', 'email_status', 'created_at', 'scheduled_report')
    search_fields = ('scheduled_report__name',)
    readonly_fields = (
        'scheduled_report',
        'execution_status',
        'email_status',
        'execution_time_seconds',
        'created_at',
        'updated_at'
    )
    inlines = [ReportDeliveryTrackingInline]
    
    fieldsets = (
        ('Report Reference', {
            'fields': ('scheduled_report',)
        }),
        ('Data Range', {
            'fields': ('data_date_from', 'data_date_to')
        }),
        ('Execution Status', {
            'fields': ('execution_status', 'execution_time_seconds', 'error_message')
        }),
        ('Generated Files', {
            'fields': ('pdf_file_path', 'excel_file_path', 'csv_file_path')
        }),
        ('Email Delivery', {
            'fields': ('email_status', 'email_sent_at', 'email_recipients')
        }),
        ('Metrics Snapshot', {
            'fields': ('metrics_snapshot',),
            'classes': ('collapse',)
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ReportDeliveryTracking)
class ReportDeliveryTrackingAdmin(admin.ModelAdmin):
    list_display = (
        'recipient_email',
        'delivery_status',
        'opened_at',
        'click_count',
        'created_at'
    )
    list_filter = ('delivery_status', 'opened_at', 'created_at', 'report_execution__scheduled_report')
    search_fields = ('recipient_email', 'report_execution__scheduled_report__name')
    readonly_fields = (
        'report_execution',
        'recipient_email',
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Report Reference', {
            'fields': ('report_execution',)
        }),
        ('Recipient', {
            'fields': ('recipient_email',)
        }),
        ('Delivery Status', {
            'fields': ('delivery_status', 'email_provider_id')
        }),
        ('Engagement', {
            'fields': ('opened_at', 'click_count', 'last_clicked_at')
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False