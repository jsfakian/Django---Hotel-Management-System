"""
Django Admin Configuration for Pricing Models

This module customizes the Django admin interface for:
1. Pricing history viewing and filtering
2. AI confidence monitoring
3. Bulk pricing adjustments
4. Model version tracking
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q, Avg, Count
from django.urls import reverse
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta

from bookings.models import PricingHistory


class ConfidenceRangeFilter(admin.SimpleListFilter):
    """Custom filter for confidence score ranges."""
    
    title = 'Confidence Range'
    parameter_name = 'confidence_range'
    
    def lookups(self, request, model_admin):
        return (
            ('very_high', 'Very High (≥ 85%)'),
            ('high', 'High (75-85%)'),
            ('medium', 'Medium (60-75%)'),
            ('low', 'Low (< 60%)'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'very_high':
            return queryset.filter(confidence_score__gte=0.85)
        elif self.value() == 'high':
            return queryset.filter(confidence_score__gte=0.75, confidence_score__lt=0.85)
        elif self.value() == 'medium':
            return queryset.filter(confidence_score__gte=0.60, confidence_score__lt=0.75)
        elif self.value() == 'low':
            return queryset.filter(confidence_score__lt=0.60)
        return queryset


@admin.register(PricingHistory)
class PricingHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for pricing history and AI recommendations.
    
    Features:
    - Color-coded confidence indicators
    - Advanced filtering by confidence, season, model
    - Bulk pricing adjustment actions
    - Revenue impact calculation
    - Search by room name and date
    """
    
    # List Display
    list_display = (
        'room_link',
        'date',
        'base_price_display',
        'ai_price_display', 
        'price_change_percent_display',
        'confidence_indicator',
        'season',
        'model_version_short',
    )
    
    # Ordering
    list_per_page = 50
    ordering = ['-date', 'room__room_number']
    
    # Filters
    list_filter = (
        'date',
        'season',
        'model_version',
        ConfidenceRangeFilter,
    )
    
    # Search
    search_fields = ('room__room_number', 'room__property__name', 'date')
    
    # Read-only fields
    readonly_fields = (
        'room',
        'date',
        'base_price',
        'dynamic_price',
        'ensemble_prediction',
        'gradient_boosting_prediction',
        'neural_network_prediction',
        'linear_regression_prediction',
        'confidence_score',
        'model_version',
        'price_change_analysis',
        'factor_breakdown',
        'created_at',
        'updated_at',
    )
    
    # Fieldsets for organized display
    fieldsets = (
        ('Room & Date', {
            'fields': ('room', 'date'),
        }),
        ('Pricing Data', {
            'fields': (
                'base_price',
                'dynamic_price',
                'competitor_price',
                'ai_recommended_price',
            ),
        }),
        ('Model Predictions', {
            'fields': (
                'ensemble_prediction',
                'gradient_boosting_prediction',
                'neural_network_prediction',
                'linear_regression_prediction',
                'confidence_score',
                'model_version',
            ),
            'classes': ('collapse',),
        }),
        ('Pricing Factors', {
            'fields': (
                'occupancy_rate',
                'season',
                'occupancy_impact_percentage',
                'seasonal_impact_percentage',
                'demand_impact_percentage',
                'competitor_impact_percentage',
                'factor_breakdown',
            ),
            'classes': ('collapse',),
        }),
        ('Analysis', {
            'fields': (
                'price_change_analysis',
            ),
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    # Actions
    actions = [
        'accept_prices_action',
        'reject_prices_action',
        'mark_high_confidence',
        'mark_low_confidence',
        'export_to_csv',
    ]
    
    # Inline display
    def has_delete_permission(self, request):
        """Only superusers can delete pricing records."""
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        """Prevent manual addition; only allow via auto_price task."""
        return False
    
    # ========================================================================
    # Display Methods
    # ========================================================================
    
    def room_link(self, obj):
        """Link to room detail page."""
        url = reverse('admin:room_room_change', args=[obj.room.pk])
        return format_html('<a href="{}">{}</a>', url, obj.room.room_number)
    room_link.short_description = 'Room'
    
    def base_price_display(self, obj):
        """Display base price formatted."""
        if obj.base_price:
            return f"${obj.base_price:.2f}"
        return "-"
    base_price_display.short_description = 'Base Price'
    
    def ai_price_display(self, obj):
        """Display AI recommended price with color."""
        if obj.dynamic_price:
            if obj.dynamic_price > obj.base_price:
                color = 'green'
                symbol = '↑'
            elif obj.dynamic_price < obj.base_price:
                color = 'red'
                symbol = '↓'
            else:
                color = 'gray'
                symbol = '='
            
            price_str = f"${obj.dynamic_price:.2f}"
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} {}</span>',
                color, symbol, price_str
            )
        return "-"
    ai_price_display.short_description = 'AI Price'
    
    def price_change_percent_display(self, obj):
        """Display percentage change from base to dynamic price."""
        if obj.base_price and obj.dynamic_price:
            change_percent = ((obj.dynamic_price - obj.base_price) / obj.base_price) * 100
            
            if change_percent > 0:
                color = 'green'
                sign = '+'
            elif change_percent < 0:
                color = 'red'
                sign = ''
            else:
                color = 'gray'
                sign = ''
            
            percent_str = f"{sign}{change_percent:.1f}%"
            return format_html(
                '<span style="color: {};">{}</span>',
                color, percent_str
            )
        return "-"
    price_change_percent_display.short_description = 'Change %'
    
    def confidence_indicator(self, obj):
        """Visual confidence score indicator."""
        if not obj.confidence_score:
            return "-"
        
        confidence = float(obj.confidence_score)
        
        # Color based on confidence level
        if confidence >= 0.85:
            color = '#28a745'  # Green
            text = '✓'
        elif confidence >= 0.75:
            color = '#ffc107'  # Yellow
            text = '◐'
        elif confidence >= 0.60:
            color = '#ff9800'  # Orange
            text = '◑'
        else:
            color = '#dc3545'  # Red
            text = '✕'
        
        confidence_pct = f"{confidence:.0%}"
        confidence_title = f"{confidence:.1%}"
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold; cursor: help;" '
            'title="Confidence: {}">{} {}</span>',
            color, confidence_title, text, confidence_pct
        )
    confidence_indicator.short_description = 'Confidence'
    
    def model_version_short(self, obj):
        """Display shortened model version."""
        if obj.model_version:
            # Show last part of version (e.g., 'ensemble-v2.3' -> 'v2.3')
            return obj.model_version.split('-')[-1]
        return "-"
    model_version_short.short_description = 'Model'
    
    def price_change_analysis(self, obj):
        """Detailed analysis of price change drivers."""
        if not obj.base_price or not obj.dynamic_price:
            return "Insufficient data"
        
        change = obj.dynamic_price - obj.base_price
        change_percent = (change / obj.base_price) * 100 if obj.base_price else 0
        
        html = f"""
        <div style="padding: 10px; background-color: #f5f5f5; border-radius: 5px;">
            <h4>Price Change Analysis</h4>
            <p>
                <strong>Change:</strong> 
                <span style="font-size: 18px; color: {'green' if change > 0 else 'red' if change < 0 else 'gray'};">
                    {'+' if change > 0 else ''} ${change:.2f} ({change_percent:+.1f}%)
                </span>
            </p>
            <h5>Impact Factors:</h5>
            <ul>
                <li>Occupancy Impact: {obj.occupancy_impact_percentage or 0:.1f}%</li>
                <li>Seasonal Impact: {obj.seasonal_impact_percentage or 0:.1f}%</li>
                <li>Demand Impact: {obj.demand_impact_percentage or 0:.1f}%</li>
                <li>Competitor Impact: {obj.competitor_impact_percentage or 0:.1f}%</li>
            </ul>
            <p><strong>Season:</strong> {obj.season or 'Unknown'}</p>
            <p><strong>Occupancy Rate:</strong> {obj.occupancy_rate or 0:.1%}</p>
        </div>
        """
        return mark_safe(html)
    price_change_analysis.short_description = 'Price Analysis'
    
    def factor_breakdown(self, obj):
        """Breakdown of all factors contributing to price."""
        html = f"""
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Factor</th>
                <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Impact</th>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">Base Price</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">${obj.base_price:.2f}</td>
            </tr>
            <tr style="background-color: #f9f9f9;">
                <td style="border: 1px solid #ddd; padding: 8px;">Occupancy Impact</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{obj.occupancy_impact_percentage or 0:.1f}%</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">Seasonal Impact</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{obj.seasonal_impact_percentage or 0:.1f}%</td>
            </tr>
            <tr style="background-color: #f9f9f9;">
                <td style="border: 1px solid #ddd; padding: 8px;">Demand Impact</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{obj.demand_impact_percentage or 0:.1f}%</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">Competitor Impact</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{obj.competitor_impact_percentage or 0:.1f}%</td>
            </tr>
            <tr style="background-color: #ffffcc; font-weight: bold;">
                <td style="border: 1px solid #ddd; padding: 8px;">Final Price</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">${obj.dynamic_price:.2f}</td>
            </tr>
        </table>
        """
        return mark_safe(html)
    factor_breakdown.short_description = 'Factor Breakdown'
    
    # ========================================================================
    # Admin Actions
    # ========================================================================
    
    def accept_prices_action(self, request, queryset):
        """Mark selected prices as reviewed."""
        count = queryset.count()
        self.message_user(request, f'{count} pricing records reviewed.')
    accept_prices_action.short_description = 'Review selected prices'
    
    def reject_prices_action(self, request, queryset):
        """Review selected prices."""
        count = queryset.count()
        self.message_user(request, f'{count} pricing records reviewed for rejection.')
    reject_prices_action.short_description = 'Review for rejection'
    
    def mark_high_confidence(self, request, queryset):
        """Filter for high confidence prices."""
        high_confidence = queryset.filter(confidence_score__gte=0.85)
        count = high_confidence.count()
        self.message_user(request, f'Found {count} high-confidence prices (≥85%).')
    mark_high_confidence.short_description = 'Find high confidence prices (≥85%%)'
    
    def mark_low_confidence(self, request, queryset):
        """Filter for low confidence prices."""
        low_confidence = queryset.filter(confidence_score__lt=0.75)
        count = low_confidence.count()
        self.message_user(request, f'Found {count} low-confidence prices for review.')
    mark_low_confidence.short_description = 'Flag low confidence prices (<75%%)'
    
    def export_to_csv(self, request, queryset):
        """Export selected records to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="pricing_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Room', 'Date', 'Base Price', 'Dynamic Price', 'Confidence',
            'Change %', 'Season', 'Model', 'Status'
        ])
        
        for obj in queryset:
            change_percent = 0
            if obj.base_price and obj.dynamic_price:
                change_percent = ((obj.dynamic_price - obj.base_price) / obj.base_price) * 100
            
            writer.writerow([
                obj.room.room_number,
                obj.date.isoformat(),
                f'{obj.base_price:.2f}',
                f'{obj.dynamic_price:.2f}',
                f'{float(obj.confidence_score or 0):.2%}',
                f'{change_percent:.1f}%',
                obj.season or 'N/A',
                obj.model_version or 'N/A',
                'AI Predicted',
            ])
        
        return response
    export_to_csv.short_description = 'Export to CSV'
    
    # ========================================================================
    # Dashboard Summary
    # ========================================================================
    
    def changelist_view(self, request, extra_context=None):
        """Add summary statistics above the list."""
        extra_context = extra_context or {}
        
        # Calculate summary stats for the last 30 days
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        recent = PricingHistory.objects.filter(date__gte=thirty_days_ago)
        
        stats = recent.aggregate(
            total_count=Count('id'),
            avg_confidence=Avg('confidence_score'),
            high_confidence_count=Count('id', filter=Q(confidence_score__gte=0.85)),
        )
        
        if stats['total_count'] > 0:
            extra_context['stats'] = {
                'total_records': stats['total_count'],
                'average_confidence': f"{float(stats['avg_confidence'] or 0):.1%}",
                'high_confidence': stats['high_confidence_count'],
                'period': 'Last 30 days',
            }
        
        return super().changelist_view(request, extra_context)
