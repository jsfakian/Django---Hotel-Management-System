"""
GDPR Data Export Service
Handles complete data portability export for users per GDPR Article 20
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Model, QuerySet
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

from room.models import Booking, RoomService
from payments.models import Payment, Invoice, RefundRequest
from contracts.models import Contract
from notifications.models import Notification, NotificationLog
from analytics.models import CustomReport, ScheduledReport

User = get_user_model()

logger = logging.getLogger(__name__)


class GDPRDataSerializer(DjangoJSONEncoder):
    """Custom JSON encoder for GDPR data export"""
    
    def default(self, obj):
        """Handle special types for JSON serialization"""
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Model):
            return str(obj)
        return super().default(obj)


class GDPRExportService:
    """
    Service for exporting complete user data in GDPR-compliant format
    
    Collects data from all models related to a user:
    - User account information
    - Guest profile and preferences
    - Employee profile (if applicable)
    - Bookings and reservations
    - Payments and invoices
    - Contracts and agreements
    - Notifications and communication
    - Analytics data
    - Activity logs and audit trails
    """
    
    EXPORT_VERSION = "1.0"
    EXPORT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    def __init__(self, user: User):
        """Initialize export service for a specific user"""
        self.user = user
        self.export_data = {}
        self.export_date = timezone.now()
        self.errors = []
    
    def export_all_data(self) -> Dict[str, Any]:
        """
        Export all user data in GDPR-compliant format
        
        Returns:
            Dictionary containing all user data organized by category
        """
        try:
            logger.info(f"Starting GDPR export for user {self.user.id}")
            
            self.export_data = {
                "export_info": self._get_export_info(),
                "user_profile": self._export_user_profile(),
                "guest_profile": self._export_guest_profile(),
                "employee_profile": self._export_employee_profile(),
                "travel_agent_profile": self._export_travel_agent_profile(),
                "bookings": self._export_bookings(),
                "payments": self._export_payments(),
                "invoices": self._export_invoices(),
                "refunds": self._export_refunds(),
                "contracts": self._export_contracts(),
                "notifications": self._export_notifications(),
                "communication": self._export_communication_logs(),
                "reports": self._export_custom_reports(),
                "audit_trail": self._export_audit_trail(),
            }
            
            logger.info(f"GDPR export completed for user {self.user.id}")
            return self.export_data
            
        except Exception as e:
            logger.error(f"Error during GDPR export for user {self.user.id}: {str(e)}")
            raise
    
    def _get_export_info(self) -> Dict[str, Any]:
        """Get export metadata"""
        return {
            "export_date": self.export_date.isoformat(),
            "export_version": self.EXPORT_VERSION,
            "data_format": "JSON",
            "compliance": "GDPR Article 20 - Right to Data Portability",
            "user_id": self.user.id,
            "user_email": self.user.email,
        }
    
    def _export_user_profile(self) -> Dict[str, Any]:
        """Export user account information"""
        if not self.user:
            return {}
        
        return {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "is_active": self.user.is_active,
            "is_staff": self.user.is_staff,
            "is_superuser": self.user.is_superuser,
            "date_joined": self.user.date_joined.isoformat(),
            "last_login": self.user.last_login.isoformat() if self.user.last_login else None,
            "groups": [group.name for group in self.user.groups.all()],
        }
    
    def _export_guest_profile(self) -> Optional[Dict[str, Any]]:
        """Export guest profile if user is a guest"""
        try:
            guest = self.user.guest_profile
            return {
                "id": guest.id,
                "email": guest.email,
                "first_name": guest.first_name,
                "last_name": guest.last_name,
                "phone_number": guest.phone_number,
                "address": guest.address,
                "city": guest.city,
                "country": guest.country,
                "postal_code": guest.postal_code,
                "preferences": guest.preferences,
                "number_of_bookings": guest.number_of_bookings,
                "total_nights_stayed": guest.total_nights_stayed,
            }
        except Exception as e:
            logger.debug(f"No guest profile for user {self.user.id}: {str(e)}")
            return None
    
    def _export_employee_profile(self) -> Optional[Dict[str, Any]]:
        """Export employee profile if user is an employee"""
        try:
            employee = self.user.employee
            return {
                "id": employee.id,
                "employee_id": employee.employee_id,
                "phone": employee.phone,
                "email": employee.email,
                "role": employee.role.name if employee.role else None,
                "property": {
                    "id": employee.property.id,
                    "name": employee.property.name,
                } if employee.property else None,
                "department": employee.department,
                "employment_status": employee.employment_status,
                "hire_date": employee.hire_date.isoformat() if employee.hire_date else None,
                "termination_date": employee.termination_date.isoformat() if employee.termination_date else None,
            }
        except:
            return None
    
    def _export_travel_agent_profile(self) -> Optional[Dict[str, Any]]:
        """Export travel agent profile if user is a travel agent"""
        try:
            travel_agent = self.user.travelagentprofile
            return {
                "id": travel_agent.id,
                "agency_id": travel_agent.agency.id if travel_agent.agency else None,
                "agency_name": travel_agent.agency.name if travel_agent.agency else None,
                "contracts": self._export_agent_contracts(travel_agent),
            }
        except:
            return None
    
    def _export_agent_contracts(self, travel_agent) -> List[Dict[str, Any]]:
        """Export contracts for travel agent"""
        contracts = Contract.objects.filter(
            travel_agency=travel_agent.agency
        ).values('id', 'property__name', 'status', 'start_date', 'end_date')
        return list(contracts)
    
    def _export_bookings(self) -> List[Dict[str, Any]]:
        """Export all bookings for the user"""
        bookings = Booking.objects.filter(guest__user=self.user).values(
            'id', 'check_in_date', 'check_out_date', 'guest__first_name',
            'guest__last_name', 'number_of_guests', 'special_requests',
            'status', 'booking_source', 'created_at', 'updated_at',
            'base_price', 'actual_price'
        )
        
        result = []
        for booking in bookings:
            # Convert dates to ISO format
            booking_data = dict(booking)
            for date_field in ['check_in_date', 'check_out_date', 'created_at', 'updated_at']:
                if booking_data.get(date_field):
                    booking_data[date_field] = booking_data[date_field].isoformat()
            result.append(booking_data)
        
        return result
    
    def _export_payments(self) -> List[Dict[str, Any]]:
        """Export all payments for the user's bookings"""
        payments = Payment.objects.filter(
            booking__guest__user=self.user
        ).values(
            'id', 'booking__id', 'amount', 'currency',
            'payment_method__name', 'status',
            'created_at', 'updated_at'
        )
        
        result = []
        for payment in payments:
            payment_data = dict(payment)
            for date_field in ['created_at', 'updated_at']:
                if payment_data.get(date_field):
                    payment_data[date_field] = payment_data[date_field].isoformat()
            result.append(payment_data)
        
        return result
    
    def _export_invoices(self) -> List[Dict[str, Any]]:
        """Export all invoices for the user"""
        invoices = Invoice.objects.filter(
            guest__user=self.user
        ).values(
            'id', 'invoice_number', 'booking__id',
            'amount', 'tax_amount', 'total_amount', 'issued_date',
            'due_date', 'status', 'mydata_transmitted', 'created_at'
        )
        
        result = []
        for invoice in invoices:
            invoice_data = dict(invoice)
            for date_field in ['issued_date', 'due_date', 'created_at']:
                if invoice_data.get(date_field):
                    if hasattr(invoice_data[date_field], 'isoformat'):
                        invoice_data[date_field] = invoice_data[date_field].isoformat()
            result.append(invoice_data)
        
        return result
    
    def _export_refunds(self) -> List[Dict[str, Any]]:
        """Export all refunds for the user"""
        refunds = RefundRequest.objects.filter(
            guest__user=self.user
        ).values(
            'id', 'reason', 'refund_amount',
            'status', 'requested_at'
        )
        
        result = []
        for refund in refunds:
            refund_data = dict(refund)
            for date_field in ['requested_at']:
                if refund_data.get(date_field):
                    refund_data[date_field] = refund_data[date_field].isoformat()
            result.append(refund_data)
        
        return result
    
    def _export_contracts(self) -> List[Dict[str, Any]]:
        """Export contracts (if user is travel agent or property manager)"""
        # Contracts where user is travel agent
        try:
            travel_agent = self.user.travel_agent_profile
            contracts = Contract.objects.filter(
                travel_agency=travel_agent.agency
            ).values(
                'id', 'property__name', 'travel_agency__name',
                'status', 'start_date', 'end_date', 'created_at'
            )
        except Exception as e:
            logger.debug(f"User {self.user.id} has no travel agent profile: {str(e)}")
            contracts = []
        
        result = []
        for contract in contracts:
            contract_data = dict(contract)
            for date_field in ['start_date', 'end_date', 'created_at']:
                if contract_data.get(date_field):
                    if hasattr(contract_data[date_field], 'isoformat'):
                        contract_data[date_field] = contract_data[date_field].isoformat()
            result.append(contract_data)
        
        return result
    
    def _export_notifications(self) -> List[Dict[str, Any]]:
        """Export all notifications for the user"""
        notifications = Notification.objects.filter(
            user=self.user
        ).values(
            'id', 'notification_type', 'title', 'message',
            'status', 'created_at', 'read_at'
        )
        
        result = []
        for notification in notifications:
            notif_data = dict(notification)
            notif_data['is_read'] = notif_data.get('read_at') is not None
            for date_field in ['created_at', 'read_at']:
                if notif_data.get(date_field):
                    notif_data[date_field] = notif_data[date_field].isoformat()
            result.append(notif_data)
        
        return result
    
    def _export_communication_logs(self) -> List[Dict[str, Any]]:
        """Export email and communication logs for the user"""
        logs = NotificationLog.objects.filter(
            notification__user=self.user
        ).values(
            'id', 'notification__title', 'action', 'details',
            'timestamp'
        )
        
        result = []
        for log in logs:
            log_data = dict(log)
            if log_data.get('timestamp'):
                log_data['timestamp'] = log_data['timestamp'].isoformat()
            result.append(log_data)
        
        return result
    
    def _export_custom_reports(self) -> List[Dict[str, Any]]:
        """Export custom reports created by the user (if employee)"""
        try:
            reports = CustomReport.objects.filter(
                created_by__user=self.user
            ).values(
                'id', 'name', 'description', 'report_type',
                'filters', 'created_at', 'updated_at'
            )
            return list(reports)
        except:
            return []
    
    def _export_audit_trail(self) -> Dict[str, Any]:
        """
        Export activity and audit trail
        This is a placeholder for audit trail data if available
        """
        return {
            "note": "Activity audit trail data is handled separately by " \
                    "Django admin logs and application-specific audit records.",
            "data_subject_access_request_date": self.export_date.isoformat(),
        }
    
    def export_to_json_string(self) -> str:
        """
        Export all data as formatted JSON string
        
        Returns:
            JSON string with all user data
        """
        data = self.export_all_data()
        return json.dumps(data, cls=GDPRDataSerializer, indent=2)
    
    def export_to_dict(self) -> Dict[str, Any]:
        """
        Export all data as dictionary
        
        Returns:
            Dictionary with all user data
        """
        return self.export_all_data()


def get_gdpr_export(user: User) -> Dict[str, Any]:
    """
    Convenience function to get GDPR export for a user
    
    Args:
        user: Django User instance
    
    Returns:
        Dictionary containing all user data
    """
    service = GDPRExportService(user)
    return service.export_to_dict()


def get_gdpr_export_json(user: User) -> str:
    """
    Convenience function to get GDPR export as JSON string
    
    Args:
        user: Django User instance
    
    Returns:
        JSON string with all user data
    """
    service = GDPRExportService(user)
    return service.export_to_json_string()
