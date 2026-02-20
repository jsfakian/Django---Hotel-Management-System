"""
MyData (AADE) Integration Service
Provides functionality to export and sync invoices with the Greek tax authority's MyData system.
"""

import json
import requests
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.utils import timezone

from .models import Invoice


class MyDataServiceException(Exception):
    """Custom exception for MyData service errors"""
    pass


class MyDataService:
    """
    Service for integrating with MyData (AADE - Greek tax authority)
    Handles invoice transmission, validation, and QR code generation
    """
    
    # MyData API endpoints
    MYDATA_API_BASE = settings.MYDATA_API_BASE if hasattr(settings, 'MYDATA_API_BASE') else 'https://www.aade.gr/mydata'
    MYDATA_TIMEOUT = 30  # seconds
    
    def __init__(self):
        """Initialize MyData service with configuration"""
        self.username = getattr(settings, 'MYDATA_USERNAME', None)
        self.password = getattr(settings, 'MYDATA_PASSWORD', None)
        self.api_key = getattr(settings, 'MYDATA_API_KEY', None)
        self.tax_id = getattr(settings, 'HOTEL_TAX_ID', None)
        
        if not self.tax_id:
            raise ImproperlyConfigured('HOTEL_TAX_ID must be configured in settings for MyData integration')
    
    def export_invoice(self, invoice: Invoice) -> Dict:
        """
        Export invoice in MyData-compatible XML/JSON format
        
        Args:
            invoice: Invoice instance to export
            
        Returns:
            Dictionary with MyData format data
        """
        if not invoice.amount:
            raise MyDataServiceException(f'Invoice {invoice.invoice_number} has invalid amount')
        
        # Calculate VAT information
        vat_amount = invoice.tax_amount or Decimal('0')
        net_amount = invoice.amount
        
        export_data = {
            'invoice': {
                'mark': invoice.mydata_transmission_id or '',
                'invoiceNumber': invoice.invoice_number,
                'issueDate': invoice.issued_date.strftime('%Y-%m-%d'),
                'dueDate': invoice.due_date.strftime('%Y-%m-%d'),
                'currency': 'EUR',
                'issuer': {
                    'taxId': self.tax_id,
                },
                'counterpart': {
                    'name': f"{invoice.guest.user.first_name} {invoice.guest.user.last_name}",
                    'email': invoice.guest.user.email,
                },
                'lines': [
                    {
                        'lineNumber': 1,
                        'description': invoice.description[:255],  # Limit to 255 chars
                        'quantity': 1,
                        'unitPrice': float(net_amount),
                        'discountPercentage': 0,
                        'discount': 0,
                        'netAmount': float(net_amount),
                        'vatCategory': '1',  # VAT 24% for services/accommodation
                        'vatAmount': float(vat_amount),
                        'grossAmount': float(invoice.total_amount),
                    }
                ],
                'totals': {
                    'netAmount': float(net_amount),
                    'vatAmount': float(vat_amount),
                    'grossAmount': float(invoice.total_amount),
                    'itemsNumber': 1,
                    'linesNumber': 1,
                },
                'paymentMethods': [
                    {
                        'type': '1',  # Card
                        'amount': float(invoice.total_amount),
                    }
                ],
                'status': invoice.status,
                'myDataStatus': 'TRANSMITTED' if invoice.mydata_transmitted else 'PENDING',
            }
        }
        
        return export_data
    
    def generate_qr_code_data(self, invoice: Invoice) -> str:
        """
        Generate QR code data string for MyData compliance.
        Format for VIES: A|TaxId|InvoiceNumber|IssueDate|GrossValue|VatAmount
        
        Args:
            invoice: Invoice instance
            
        Returns:
            QR code data string
        """
        if not invoice.amount:
            raise MyDataServiceException(f'Invoice {invoice.invoice_number} has invalid amount')
        
        # Format: A (for regular invoice type) | TAX_ID | INVOICE_NUMBER | ISSUE_DATE | GROSS_VALUE | VAT_AMOUNT
        qr_data = f"A|{self.tax_id}|{invoice.invoice_number}|{invoice.issued_date.strftime('%Y%m%d')}|{int(float(invoice.total_amount) * 100)}|{int(float(invoice.tax_amount or 0) * 100)}"
        
        return qr_data
    
    def transmit_invoice(self, invoice: Invoice) -> Tuple[bool, str]:
        """
        Transmit invoice to MyData system.
        This is a mock implementation. Real implementation would use SOAP API.
        
        Args:
            invoice: Invoice instance to transmit
            
        Returns:
            Tuple of (success: bool, transmission_id or error message: str)
        """
        try:
            # Validate invoice
            if not invoice.amount or invoice.amount <= 0:
                return False, f'Invalid invoice amount: {invoice.amount}'
            
            if not invoice.guest.user.email:
                return False, f'Guest email is required for MyData transmission'
            
            # Generate transmission ID (in real implementation, this comes from MyData)
            transmission_id = self._generate_transmission_id(invoice)
            
            # Generate QR code
            qr_code = self.generate_qr_code_data(invoice)
            
            # Mark invoice as transmitted
            invoice.mark_as_mydata_transmitted(transmission_id, qr_code)
            
            return True, transmission_id
            
        except Exception as e:
            return False, str(e)
    
    def _generate_transmission_id(self, invoice: Invoice) -> str:
        """
        Generate a transmission ID for MyData.
        In production, this would be returned by MyData API.
        Format: AADE-YYYY-SEQ where SEQ is sequential
        """
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        return f"AADE-{invoice.invoice_number}-{timestamp}"
    
    def validate_invoice_for_transmission(self, invoice: Invoice) -> Tuple[bool, List[str]]:
        """
        Validate invoice meets MyData requirements.
        
        Args:
            invoice: Invoice to validate
            
        Returns:
            Tuple of (is_valid: bool, error_list: List[str])
        """
        errors = []
        
        # Validate required fields
        if not invoice.invoice_number:
            errors.append('Invoice number is required')
        
        if not invoice.amount or invoice.amount <= 0:
            errors.append('Invoice amount must be greater than 0')
        
        if not invoice.total_amount or invoice.total_amount <= 0:
            errors.append('Total amount must be greater than 0')
        
        if not invoice.issued_date:
            errors.append('Issue date is required')
        
        if not invoice.due_date:
            errors.append('Due date is required')
        
        if not invoice.guest.user.email:
            errors.append('Guest email is required')
        
        if not invoice.guest.user.first_name or not invoice.guest.user.last_name:
            errors.append('Guest first and last name are required')
        
        # Validate date consistency
        if invoice.issued_date.date() > invoice.due_date:
            errors.append('Due date must be after issue date')
        
        # Validate amounts
        expected_total = invoice.amount + (invoice.tax_amount or Decimal('0'))
        if invoice.total_amount != expected_total:
            errors.append(f'Total amount mismatch: expected {expected_total}, got {invoice.total_amount}')
        
        return len(errors) == 0, errors
    
    def get_transmittable_invoices(self) -> List[Invoice]:
        """
        Get all invoices that need to be transmitted to MyData.
        
        Returns:
            List of Invoice instances ready for transmission
        """
        # Invoices that are issued but not yet transmitted
        return Invoice.objects.filter(
            status__in=['issued', 'paid'],
            mydata_transmitted=False
        ).exclude(guest__user__email='')
    
    def bulk_transmit_invoices(self) -> Dict:
        """
        Transmit all pending invoices to MyData.
        
        Returns:
            Dictionary with transmission results
        """
        invoices = self.get_transmittable_invoices()
        results = {
            'total': invoices.count(),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'transmitted_ids': []
        }
        
        for invoice in invoices:
            # Validate before transmission
            is_valid, validation_errors = self.validate_invoice_for_transmission(invoice)
            
            if not is_valid:
                results['failed'] += 1
                results['errors'].append({
                    'invoice_number': invoice.invoice_number,
                    'errors': validation_errors
                })
                continue
            
            # Attempt transmission
            success, transmission_id = self.transmit_invoice(invoice)
            
            if success:
                results['successful'] += 1
                results['transmitted_ids'].append({
                    'invoice_number': invoice.invoice_number,
                    'transmission_id': transmission_id
                })
            else:
                results['failed'] += 1
                results['errors'].append({
                    'invoice_number': invoice.invoice_number,
                    'error': transmission_id  # transmission_id contains error message on failure
                })
        
        return results


# Singleton instance
_mydata_service = None


def get_mydata_service() -> MyDataService:
    """Get or create MyData service singleton"""
    global _mydata_service
    if _mydata_service is None:
        _mydata_service = MyDataService()
    return _mydata_service
