"""
Analytics Views

REST API endpoints for dashboard data and analytics.
"""

from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count, Q
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, inline_serializer

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
from .serializers import (
    DashboardExecutiveMetricsSerializer,
    DashboardOperationalStatusSerializer,
    DashboardRevenueMetricsSerializer,
    DashboardGuestAnalyticsSerializer,
    CustomReportSerializer,
    ScheduledReportSerializer,
    ScheduledReportCreateUpdateSerializer,
    ReportExecutionSerializer,
    ReportExecutionTriggerSerializer,
    ReportResendSerializer,
    ReportDeliveryTrackingSerializer,
    OccupancyForecastSerializer,
    RevenueForecastSerializer,
    CancellationPredictionSerializer,
    NoShowPredictionSerializer,
    ForecastingModelMetricsSerializer,
)


class AnalyticsPermission(IsAuthenticated):
    """Permission class for analytics endpoints - requires authentication"""
    pass

def _user_group_names(user):
    if not user or not user.is_authenticated:
        return set()
    return set(user.groups.values_list('name', flat=True))


def _user_is_analytics_admin(user):
    group_names = _user_group_names(user)
    return user.is_staff or bool(group_names.intersection({'manager', 'executive', 'admin'}))


def _accessible_property_queryset(user):
    if _user_is_analytics_admin(user):
        return Property.objects.all()

    queryset = Property.objects.none()

    if hasattr(user, 'managed_properties'):
        queryset = queryset | user.managed_properties.all()

    if hasattr(user, 'employee_profile') and user.employee_profile.property_id:
        queryset = queryset | Property.objects.filter(id=user.employee_profile.property_id)

    return queryset.distinct()

class ExecutiveDashboardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Executive Dashboard endpoint
    
    GET /analytics/executive-dashboard/?property_id=1&period=month
    
    Returns strategic KPIs for hotel executives.
    """
    queryset = DashboardExecutiveMetrics.objects.all()
    serializer_class = DashboardExecutiveMetricsSerializer
    permission_classes = [IsAuthenticated, AnalyticsPermission]
    
    def get_queryset(self):
        """Filter metrics by property and user permissions"""
        property_id = self.request.query_params.get('property_id')
        
        if property_id:
            return self.queryset.filter(property_id=property_id)
        
        # Return only properties user has access to
        user = self.request.user
        if _user_is_analytics_admin(user):
            return self.queryset
        
        return self.queryset.none()
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get latest executive metrics for a property"""
        property_id = request.query_params.get('property_id')
        
        if not property_id:
            return Response(
                {'error': 'property_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        metrics = DashboardExecutiveMetrics.objects.filter(
            property_id=property_id
        ).order_by('-metric_date').first()
        
        if not metrics:
            return Response(
                {'message': 'No metrics available yet'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(metrics)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trend(self, request):
        """Get historical trend for selected metric"""
        property_id = request.query_params.get('property_id')
        metric = request.query_params.get('metric', 'total_revenue')
        days = int(request.query_params.get('days', 90))
        
        if not property_id:
            return Response(
                {'error': 'property_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from_date = datetime.now().date() - timedelta(days=days)
        
        metrics = DashboardExecutiveMetrics.objects.filter(
            property_id=property_id,
            metric_date__gte=from_date
        ).order_by('metric_date').values('metric_date', metric)
        
        return Response({
            'metric': metric,
            'period_days': days,
            'data': list(metrics)
        })


class OperationalDashboardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Operational Dashboard endpoint
    
    GET /analytics/operational-dashboard/?property_id=1&date=2026-02-19
    
    Returns real-time operational status for hotel staff.
    """
    queryset = DashboardOperationalStatus.objects.all()
    serializer_class = DashboardOperationalStatusSerializer
    permission_classes = [IsAuthenticated, AnalyticsPermission]
    
    def get_queryset(self):
        """Filter status by property"""
        property_id = self.request.query_params.get('property_id')
        
        if property_id:
            return self.queryset.filter(property_id=property_id)
        
        return self.queryset.none()
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get latest operational status"""
        property_id = request.query_params.get('property_id')
        
        if not property_id:
            return Response(
                {'error': 'property_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        status_obj = DashboardOperationalStatus.objects.filter(
            property_id=property_id
        ).order_by('-status_time').first()
        
        if not status_obj:
            return Response(
                {'message': 'No operational status available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(status_obj)
        return Response(serializer.data)


class RevenueAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Revenue Analytics endpoint
    
    GET /analytics/revenue-analytics/?property_id=1&from_date=2026-01-01&to_date=2026-02-19
    
    Returns financial performance metrics and revenue analysis.
    """
    queryset = DashboardRevenueMetrics.objects.all()
    serializer_class = DashboardRevenueMetricsSerializer
    permission_classes = [IsAuthenticated, AnalyticsPermission]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """Filter and search revenue metrics"""
        property_id = self.request.query_params.get('property_id')
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        
        queryset = self.queryset
        
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        
        if from_date:
            queryset = queryset.filter(metric_date__gte=from_date)
        
        if to_date:
            queryset = queryset.filter(metric_date__lte=to_date)
        
        return queryset.order_by('-metric_date')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get revenue summary statistics"""
        property_id = request.query_params.get('property_id')
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        
        if not property_id:
            return Response(
                {'error': 'property_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        metrics = DashboardRevenueMetrics.objects.filter(property_id=property_id)
        
        if from_date:
            metrics = metrics.filter(metric_date__gte=from_date)
        if to_date:
            metrics = metrics.filter(metric_date__lte=to_date)
        
        stats = metrics.aggregate(
            total_revenue=Sum('total_revenue'),
            avg_adr=Avg('avg_daily_rate'),
            avg_revpar=Avg('revpar'),
            avg_occupancy=Avg('occupancy_rate'),
            total_bookings=Sum('booking_count'),
            total_cancellations=Sum('cancellation_count'),
        )
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def by_source(self, request):
        """Get revenue breakdown by booking source"""
        property_id = request.query_params.get('property_id')
        period = request.query_params.get('period', 'month')
        
        if not property_id:
            return Response(
                {'error': 'property_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # This would typically aggregate actual booking data
        # For now, return from pre-calculated metrics
        metrics = DashboardRevenueMetrics.objects.filter(
            property_id=property_id
        ).values('revenue_direct', 'revenue_ota', 'revenue_agency')
        
        return Response({
            'property_id': property_id,
            'period': period,
            'breakdown': metrics
        })


class GuestAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Guest Analytics endpoint
    
    GET /analytics/guest-analytics/?property_id=1&from_date=2026-01-01
    
    Returns guest insights, segmentation, and personalization metrics.
    """
    queryset = DashboardGuestAnalytics.objects.all()
    serializer_class = DashboardGuestAnalyticsSerializer
    permission_classes = [IsAuthenticated, AnalyticsPermission]
    
    def get_queryset(self):
        """Filter guest analytics by property"""
        property_id = self.request.query_params.get('property_id')
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        
        queryset = self.queryset
        
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        
        if from_date:
            queryset = queryset.filter(analytics_date__gte=from_date)
        
        if to_date:
            queryset = queryset.filter(analytics_date__lte=to_date)
        
        return queryset.order_by('-analytics_date')
    
    @action(detail=False, methods=['get'])
    def segments(self, request):
        """Get guest segmentation data"""
        property_id = request.query_params.get('property_id')
        
        if not property_id:
            return Response(
                {'error': 'property_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        analytics = DashboardGuestAnalytics.objects.filter(
            property_id=property_id
        ).order_by('-analytics_date').first()
        
        if not analytics:
            return Response({'property_id': property_id, 'segments': {}}, status=status.HTTP_200_OK)
        
        return Response({
            'property_id': property_id,
            'segments': analytics.guest_segments
        })
    
    @action(detail=False, methods=['get'])
    def churn(self, request):
        """Get churn analysis"""
        property_id = request.query_params.get('property_id')
        
        if not property_id:
            return Response(
                {'error': 'property_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        analytics = DashboardGuestAnalytics.objects.filter(
            property_id=property_id
        ).order_by('-analytics_date').values(
            'analytics_date',
            'retention_rate',
            'churn_rate',
            'at_risk_guests'
        )
        
        return Response({
            'property_id': property_id,
            'churn_data': list(analytics)
        })


class CustomReportViewSet(viewsets.ModelViewSet):
    """
    Custom Reports endpoint
    
    GET /analytics/custom-reports/ - List all custom reports
    POST /analytics/custom-reports/ - Create new custom report
    GET /analytics/custom-reports/{id}/ - Get report details
    """
    queryset = CustomReport.objects.all()
    serializer_class = CustomReportSerializer
    permission_classes = [IsAuthenticated, AnalyticsPermission]
    
    def get_queryset(self):
        """Filter reports by property and user"""
        property_id = self.request.query_params.get('property_id')
        
        if property_id:
            return self.queryset.filter(property_id=property_id)
        
        return self.queryset.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Generate/export the report"""
        report = self.get_object()
        
        # Trigger async report generation task
        from .tasks import generate_custom_report
        generate_custom_report.delay(report.id)
        
        return Response({
            'message': 'Report generation started',
            'status': 'pending',
            'report_id': report.id
        })
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download generated report"""
        report = self.get_object()
        
        if report.status != 'generated' or not report.file_path:
            return Response(
                {'error': 'Report not yet generated'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Return file download response
        return Response({
            'download_url': f'/media/{report.file_path}',
            'format': report.export_format,
            'generated_at': report.generated_at
        })


class AnalyticsDashboardViewSet(viewsets.ViewSet):
    """
    Combined Analytics Dashboard endpoint
    
    GET /analytics/dashboard/?property_id=1&dashboard_type=executive
    
    Returns combined data for multiple dashboards.
    """
    permission_classes = [IsAuthenticated, AnalyticsPermission]
    
    @extend_schema(
        responses=inline_serializer(
            name='AnalyticsDashboardSummaryResponse',
            fields={
                'property_id': serializers.CharField(),
                'dashboard_type': serializers.CharField(),
                'data': serializers.DictField(child=serializers.JSONField()),
            },
        )
    )
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary data for all dashboards"""
        property_id = request.query_params.get('property_id')
        dashboard_type = request.query_params.get('dashboard_type', 'executive')
        
        if not property_id:
            return Response(
                {'error': 'property_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = {}
        
        # Executive Dashboard
        if dashboard_type in ['executive', 'all']:
            exec_metrics = DashboardExecutiveMetrics.objects.filter(
                property_id=property_id
            ).order_by('-metric_date').first()
            
            if exec_metrics:
                data['executive'] = DashboardExecutiveMetricsSerializer(exec_metrics).data
        
        # Operational Dashboard
        if dashboard_type in ['operational', 'all']:
            op_status = DashboardOperationalStatus.objects.filter(
                property_id=property_id
            ).order_by('-status_time').first()
            
            if op_status:
                data['operational'] = DashboardOperationalStatusSerializer(op_status).data
        
        # Revenue Analytics
        if dashboard_type in ['revenue', 'all']:
            rev_metrics = DashboardRevenueMetrics.objects.filter(
                property_id=property_id
            ).order_by('-metric_date').first()
            
            if rev_metrics:
                data['revenue'] = DashboardRevenueMetricsSerializer(rev_metrics).data
        
        # Guest Analytics
        if dashboard_type in ['guest', 'all']:
            guest_analytics = DashboardGuestAnalytics.objects.filter(
                property_id=property_id
            ).order_by('-analytics_date').first()
            
            if guest_analytics:
                data['guest'] = DashboardGuestAnalyticsSerializer(guest_analytics).data
        
        return Response({
            'property_id': property_id,
            'dashboard_type': dashboard_type,
            'data': data
        })


# Automated Reporting ViewSets

class ScheduledReportViewSet(viewsets.ModelViewSet):
    """
    Scheduled Report Management endpoint
    
    GET /api/v1/analytics/scheduled-reports/ - List scheduled reports
    POST /api/v1/analytics/scheduled-reports/ - Create scheduled report
    GET /api/v1/analytics/scheduled-reports/{id}/ - Retrieve scheduled report
    PUT /api/v1/analytics/scheduled-reports/{id}/ - Update scheduled report
    DELETE /api/v1/analytics/scheduled-reports/{id}/ - Delete scheduled report
    POST /api/v1/analytics/scheduled-reports/{id}/trigger/ - Manually trigger report
    POST /api/v1/analytics/scheduled-reports/{id}/test/ - Send test report via email
    """
    queryset = ScheduledReport.objects.all()
    permission_classes = [IsAuthenticated, AnalyticsPermission]
    pagination_class = PageNumberPagination
    
    def get_serializer_class(self):
        """Use different serializer for different actions"""
        if self.action in ['create', 'update', 'partial_update']:
            return ScheduledReportCreateUpdateSerializer
        return ScheduledReportSerializer
    
    def get_queryset(self):
        """Filter reports by property and user permissions"""
        property_id = self.request.query_params.get('property_id')
        is_active = self.request.query_params.get('is_active')
        
        queryset = ScheduledReport.objects.all()
        
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by user permissions
        user = self.request.user
        if not _user_is_analytics_admin(user):
            queryset = queryset.filter(property__in=_accessible_property_queryset(user))
        
        return queryset.order_by('-is_active', 'schedule_time')
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def trigger(self, request, pk=None):
        """Manually trigger report generation"""
        scheduled_report = self.get_object()
        
        from .tasks import generate_scheduled_report
        
        task = generate_scheduled_report.delay(
            scheduled_report_id=scheduled_report.id,
            override_recipients=request.data.get('override_recipients')
        )
        
        return Response({
            'task_id': task.id,
            'message': 'Report generation triggered',
            'status': 'pending'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Send test report to current user's email"""
        scheduled_report = self.get_object()
        
        if not request.user.email:
            return Response(
                {'error': 'User email not configured'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from .tasks import generate_scheduled_report
        
        task = generate_scheduled_report.delay(
            scheduled_report_id=scheduled_report.id,
            override_recipients=[request.user.email]
        )
        
        return Response({
            'task_id': task.id,
            'message': f'Test report will be sent to {request.user.email}',
            'status': 'pending'
        }, status=status.HTTP_202_ACCEPTED)


class ReportExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Report Execution History endpoint
    
    GET /api/v1/analytics/report-executions/ - List report executions
    GET /api/v1/analytics/report-executions/{id}/ - Retrieve execution details
    GET /api/v1/analytics/report-executions/{id}/delivery-status/ - Get email delivery status
    POST /api/v1/analytics/report-executions/{id}/resend/ - Resend report email
    """
    queryset = ReportExecution.objects.all()
    serializer_class = ReportExecutionSerializer
    permission_classes = [IsAuthenticated, AnalyticsPermission]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """Filter executions by property and user permissions"""
        scheduled_report_id = self.request.query_params.get('scheduled_report_id')
        status_filter = self.request.query_params.get('status')
        
        queryset = ReportExecution.objects.select_related('scheduled_report')
        
        if scheduled_report_id:
            queryset = queryset.filter(scheduled_report_id=scheduled_report_id)
        
        if status_filter:
            queryset = queryset.filter(execution_status=status_filter)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['get'])
    def delivery_status(self, request, pk=None):
        """Get email delivery status for report execution"""
        report_execution = self.get_object()
        
        tracking_records = ReportDeliveryTracking.objects.filter(
            report_execution=report_execution
        )
        
        tracking_serializer = ReportDeliveryTrackingSerializer(
            tracking_records,
            many=True
        )
        
        # Summary statistics
        total_recipients = tracking_records.count()
        sent_count = tracking_records.filter(
            delivery_status__in=['sent', 'opened', 'clicked']
        ).count()
        opened_count = tracking_records.filter(
            delivery_status__in=['opened', 'clicked']
        ).count()
        failed_count = tracking_records.filter(
            delivery_status__in=['bounced', 'failed']
        ).count()
        
        return Response({
            'report_execution_id': report_execution.id,
            'total_recipients': total_recipients,
            'sent': sent_count,
            'opened': opened_count,
            'failed': failed_count,
            'recipient_tracking': tracking_serializer.data,
            'overall_status': report_execution.email_status,
            'sent_at': report_execution.email_sent_at,
        })
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Resend generated report via email"""
        report_execution = self.get_object()
        
        if report_execution.execution_status != 'generated':
            return Response(
                {'error': 'Can only resend reports that have been successfully generated'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get override recipients or use original recipients
        recipients = request.data.get('override_recipients', report_execution.email_recipients)
        
        from .tasks import send_report_email
        
        task = send_report_email.delay(
            execution_id=report_execution.id,
            recipients=recipients
        )
        
        return Response({
            'task_id': task.id,
            'message': f'Report resend initialized for {len(recipients)} recipients',
            'recipients': recipients,
            'status': 'pending'
        }, status=status.HTTP_202_ACCEPTED)


# ============================================================================
# FORECASTING VIEWSETS
# ============================================================================

class OccupancyForecastViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Occupancy Forecasting ViewSet
    
    Endpoints:
    - GET /occupancy-forecasts/ - List all forecasts
    - GET /occupancy-forecasts/{id}/ - Retrieve specific forecast
    - GET /occupancy-forecasts/by-property/{property_id}/ - Property forecasts
    - GET /occupancy-forecasts/next-30-days/{property_id}/ - Next 30 days
    """
    serializer_class = OccupancyForecastSerializer
    permission_classes = [AnalyticsPermission]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """Filter forecasts by property"""
        from .models import OccupancyForecast
        
        property_id = self.request.query_params.get('property_id')
        queryset = OccupancyForecast.objects.all()
        
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        
        if _user_is_analytics_admin(self.request.user):
            return queryset.order_by('-target_date')

        return queryset.filter(property__in=_accessible_property_queryset(self.request.user)).order_by('-target_date')
    
    @action(detail=False, methods=['get'])
    def by_property(self, request):
        """Get occupancy forecasts for a specific property"""
        property_id = request.query_params.get('property_id')
        if not property_id:
            return Response(
                {'error': 'property_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from .models import OccupancyForecast
        
        forecasts = OccupancyForecast.objects.filter(
            property_id=property_id
        )

        if not _user_is_analytics_admin(request.user):
            forecasts = forecasts.filter(property__in=_accessible_property_queryset(request.user))

        forecasts = forecasts.order_by('-target_date')[:50]
        
        serializer = self.get_serializer(forecasts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def next_30_days(self, request):
        """Get 30-day occupancy forecast for properties"""
        from datetime import date
        from .models import OccupancyForecast
        
        property_id = request.query_params.get('property_id')
        today = date.today()
        
        queryset = OccupancyForecast.objects.filter(
            target_date__gte=today,
            target_date__lte=today + timedelta(days=30)
        )
        
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        if not _user_is_analytics_admin(request.user):
            queryset = queryset.filter(property__in=_accessible_property_queryset(request.user))
        
        queryset = queryset.order_by('target_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'property_id': property_id,
            'forecast_days': 30,
            'forecasts': serializer.data
        })


class RevenueForecastViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Revenue Forecasting ViewSet
    
    Endpoints:
    - GET /revenue-forecasts/ - List all forecasts
    - GET /revenue-forecasts/{id}/ - Retrieve specific forecast
    - GET /revenue-forecasts/next-30-days/{property_id}/ - Next 30 days
    """
    serializer_class = RevenueForecastSerializer
    permission_classes = [AnalyticsPermission]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """Filter forecasts by property"""
        from .models import RevenueForecast
        
        property_id = self.request.query_params.get('property_id')
        queryset = RevenueForecast.objects.all()
        
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        
        if _user_is_analytics_admin(self.request.user):
            return queryset.order_by('-target_date')

        return queryset.filter(property__in=_accessible_property_queryset(self.request.user)).order_by('-target_date')
    
    @action(detail=False, methods=['get'])
    def next_30_days(self, request):
        """Get 30-day revenue forecast for properties"""
        from datetime import date
        from .models import RevenueForecast
        
        property_id = request.query_params.get('property_id')
        today = date.today()
        
        queryset = RevenueForecast.objects.filter(
            target_date__gte=today,
            target_date__lte=today + timedelta(days=30)
        )
        
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        if not _user_is_analytics_admin(request.user):
            queryset = queryset.filter(property__in=_accessible_property_queryset(request.user))
        
        queryset = queryset.order_by('target_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'property_id': property_id,
            'forecast_days': 30,
            'forecasts': serializer.data
        })


class CancellationPredictionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Cancellation Risk Prediction ViewSet
    
    Endpoints:
    - GET /cancellation-predictions/ - List all predictions
    - GET /cancellation-predictions/high-risk/ - High-risk bookings
    - GET /cancellation-predictions/by-property/{property_id}/ - Property predictions
    """
    serializer_class = CancellationPredictionSerializer
    permission_classes = [AnalyticsPermission]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """Filter predictions by property"""
        from .models import CancellationPrediction
        
        property_id = self.request.query_params.get('property_id')
        queryset = CancellationPrediction.objects.all()
        
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        
        if _user_is_analytics_admin(self.request.user):
            return queryset.order_by('-cancellation_risk_score')

        return queryset.filter(property__in=_accessible_property_queryset(self.request.user)).order_by('-cancellation_risk_score')
    
    @action(detail=False, methods=['get'])
    def high_risk(self, request):
        """Get high-risk cancellation predictions (risk > 65%)"""
        from .models import CancellationPrediction
        
        property_id = request.query_params.get('property_id')
        
        queryset = CancellationPrediction.objects.filter(
            risk_level='high'
        )
        
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        if not _user_is_analytics_admin(request.user):
            queryset = queryset.filter(property__in=_accessible_property_queryset(request.user))
        
        queryset = queryset.order_by('-cancellation_risk_score')
        
        serializer = self.get_serializer(queryset[:20], many=True)
        return Response({
            'property_id': property_id,
            'high_risk_count': queryset.count(),
            'predictions': serializer.data
        })


class NoShowPredictionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    No-Show Risk Prediction ViewSet
    
    Endpoints:
    - GET /noshow-predictions/ - List all predictions
    - GET /noshow-predictions/high-risk/ - High-risk bookings
    - GET /noshow-predictions/overbooking-recommendations/ - Overbooking suggestions
    """
    serializer_class = NoShowPredictionSerializer
    permission_classes = [AnalyticsPermission]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """Filter predictions by property"""
        from .models import NoShowPrediction
        
        property_id = self.request.query_params.get('property_id')
        queryset = NoShowPrediction.objects.all()
        
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        
        if _user_is_analytics_admin(self.request.user):
            return queryset.order_by('-noshow_risk_score')

        return queryset.filter(property__in=_accessible_property_queryset(self.request.user)).order_by('-noshow_risk_score')
    
    @action(detail=False, methods=['get'])
    def high_risk(self, request):
        """Get high-risk no-show predictions (risk > 40%)"""
        from .models import NoShowPrediction
        
        property_id = request.query_params.get('property_id')
        
        queryset = NoShowPrediction.objects.filter(
            risk_level='high'
        )
        
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        if not _user_is_analytics_admin(request.user):
            queryset = queryset.filter(property__in=_accessible_property_queryset(request.user))
        
        queryset = queryset.order_by('-noshow_risk_score')
        
        serializer = self.get_serializer(queryset[:20], many=True)
        return Response({
            'property_id': property_id,
            'high_risk_count': queryset.count(),
            'predictions': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def overbooking_recommendations(self, request):
        """Get overbooking recommendations based on no-show risk"""
        from .models import NoShowPrediction
        
        property_id = request.query_params.get('property_id')
        
        queryset = NoShowPrediction.objects.all()

        if property_id:
            queryset = queryset.filter(property_id=property_id)

        if not _user_is_analytics_admin(request.user):
            queryset = queryset.filter(property__in=_accessible_property_queryset(request.user))
        
        # Group by risk level
        low_risk = queryset.filter(risk_level='low').count()
        medium_risk = queryset.filter(risk_level='medium').count()
        high_risk = queryset.filter(risk_level='high').count()
        
        total = low_risk + medium_risk + high_risk
        
        return Response({
            'property_id': property_id,
            'total_bookings': total,
            'risk_distribution': {
                'low': low_risk,
                'medium': medium_risk,
                'high': high_risk
            },
            'recommendations': {
                'low_risk_allocation': '100%',
                'medium_risk_allocation': '105-110%',
                'high_risk_allocation': '110-115%',
                'expected_occupancy_gain': '2-3%'
            }
        })


class ForecastingModelMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Forecasting Model Metrics ViewSet - Monitor model performance
    
    Endpoints:
    - GET /forecast-metrics/ - List all metrics
    - GET /forecast-metrics/by-property/{property_id}/ - Property metrics
    - GET /forecast-metrics/health-check/ - Model health status
    """
    serializer_class = ForecastingModelMetricsSerializer
    permission_classes = [AnalyticsPermission]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """Filter metrics by property"""
        from .models import ForecastingModelMetrics
        
        property_id = self.request.query_params.get('property_id')
        queryset = ForecastingModelMetrics.objects.all()
        
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        
        if _user_is_analytics_admin(self.request.user):
            return queryset.order_by('-evaluation_date')

        return queryset.filter(property__in=_accessible_property_queryset(self.request.user)).order_by('-evaluation_date')
    
    @action(detail=False, methods=['get'])
    def health_check(self, request):
        """Get overall forecasting model health status"""
        from .models import ForecastingModelMetrics
        
        property_id = request.query_params.get('property_id')
        
        queryset = ForecastingModelMetrics.objects.all()

        if property_id:
            queryset = queryset.filter(property_id=property_id)

        if not _user_is_analytics_admin(request.user):
            queryset = queryset.filter(property__in=_accessible_property_queryset(request.user))
        
        # Get latest metrics for each model
        latest_metrics = {}
        for model_name in [
            'occupancy_prophet', 'occupancy_sarima', 'revenue_prophet',
            'cancellation_xgb', 'noshow_xgb'
        ]:
            metric = queryset.filter(model_name=model_name).order_by('-evaluation_date').first()
            if metric:
                latest_metrics[model_name] = {
                    'is_acceptable': metric.is_acceptable,
                    'needs_retraining': metric.needs_retraining,
                    'last_evaluated': metric.evaluation_date,
                    'mape': float(metric.mape) if metric.mape else None,
                    'f1_score': float(metric.f1_score) if metric.f1_score else None,
                }
        
        # Determine overall status
        all_acceptable = all(m['is_acceptable'] for m in latest_metrics.values())
        any_need_retraining = any(m['needs_retraining'] for m in latest_metrics.values())
        
        if all_acceptable and not any_need_retraining:
            health_status = 'green'
        elif any_need_retraining:
            health_status = 'red'
        else:
            health_status = 'yellow'
        
        return Response({
            'property_id': property_id,
            'health_status': health_status,
            'model_metrics': latest_metrics,
            'action_required': 'Retrain models' if any_need_retraining else 'No action required'
        })


# Import serializers for forecasting viewsets
from .serializers import (
    OccupancyForecastSerializer,
    RevenueForecastSerializer,
    CancellationPredictionSerializer,
    NoShowPredictionSerializer,
    ForecastingModelMetricsSerializer,
)
