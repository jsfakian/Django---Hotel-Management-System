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
        self.api_key = getattr(settings, 'MYDATA_API_KEY', None) or getattr(
            settings, 'MYDATA_SUBSCRIPTION_KEY', None
        )
        self.subscription_key = getattr(settings, 'MYDATA_SUBSCRIPTION_KEY', None) or self.api_key
        self.tax_id = getattr(settings, 'HOTEL_TAX_ID', None)
        self.sandbox_mode = getattr(settings, 'MYDATA_SANDBOX_MODE', True)
        self.api_base = getattr(
            settings, 'MYDATA_API_BASE', 'https://www1.mydata.aade.gr/api'
        ).rstrip('/')
        self.timeout = getattr(settings, 'MYDATA_TIMEOUT', 30)

        if not self.tax_id:
            raise ImproperlyConfigured('HOTEL_TAX_ID must be configured in settings for MyData integration')

    def _auth_headers(self) -> Dict[str, str]:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if self.username:
            headers['aade-user-id'] = self.username
        if self.subscription_key:
            headers['Ocp-Apim-Subscription-Key'] = self.subscription_key
        elif self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers
    
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
        Transmit invoice to MyData.

        When MYDATA_SANDBOX_MODE is True, keep the local mock MARK.
        When False, POST to MYDATA_API_BASE with username / subscription key.
        """
        try:
            if not invoice.amount or invoice.amount <= 0:
                return False, f'Invalid invoice amount: {invoice.amount}'

            guest_email = ''
            if invoice.guest_id:
                if getattr(invoice.guest, 'user_id', None) and invoice.guest.user:
                    guest_email = invoice.guest.user.email or ''
                guest_email = guest_email or getattr(invoice.guest, 'email', '') or ''
            if not guest_email:
                return False, 'Guest email is required for MyData transmission'

            export_data = self.export_invoice(invoice)
            qr_code = self.generate_qr_code_data(invoice)

            if self.sandbox_mode:
                transmission_id = self._generate_transmission_id(invoice)
                invoice.mark_as_mydata_transmitted(transmission_id, qr_code)
                return True, transmission_id

            if not self.username or not self.subscription_key:
                return (
                    False,
                    'MYDATA_USERNAME and MYDATA_SUBSCRIPTION_KEY (or MYDATA_API_KEY) '
                    'required when MYDATA_SANDBOX_MODE=False',
                )

            url = f'{self.api_base}/SendInvoices'
            response = requests.post(
                url,
                json=export_data,
                headers=self._auth_headers(),
                timeout=self.timeout,
            )
            try:
                body = response.json()
            except ValueError:
                body = {'raw': response.text}

            if response.status_code >= 400:
                return False, f'MyData HTTP {response.status_code}: {body}'

            transmission_id = (
                str(body.get('transmission_id') or body.get('mark') or body.get('uid') or '')
                or self._generate_transmission_id(invoice)
            )
            invoice.mark_as_mydata_transmitted(transmission_id, qr_code)
            return True, transmission_id

        except requests.RequestException as e:
            return False, f'MyData network error: {e}'
        except Exception as e:
            return False, str(e)

    def poll_status(self, transmission_id: str) -> Dict:
        """
        Poll MyData for the status of a previously submitted invoice MARK/UID.

        Sandbox mode returns a synthetic accepted status.
        """
        if self.sandbox_mode:
            return {
                'transmission_id': transmission_id,
                'status': 'accepted',
                'sandbox': True,
            }

        if not self.username or not self.subscription_key:
            raise MyDataServiceException(
                'MYDATA credentials required to poll status outside sandbox'
            )

        url = f'{self.api_base}/RequestDocs'
        response = requests.get(
            url,
            params={'mark': transmission_id},
            headers=self._auth_headers(),
            timeout=self.timeout,
        )
        try:
            body = response.json()
        except ValueError:
            body = {'raw': response.text}
        if response.status_code >= 400:
            raise MyDataServiceException(
                f'MyData status poll failed ({response.status_code}): {body}'
            )
        return {
            'transmission_id': transmission_id,
            'status': body.get('status') or body.get('response') or 'unknown',
            'sandbox': False,
            'raw': body,
        }

    def _generate_transmission_id(self, invoice: Invoice) -> str:
        """
        Generate a transmission ID for MyData.
        In production, this would be returned by MyData API.
        Format: AADE-YYYY-SEQ where SEQ is sequential
        """
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        return f"AADE-{invoice.invoice_number}-{timestamp}"
    
    @staticmethod
    def _required_field_errors(invoice: Invoice) -> List[str]:
        errors = []
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
        return errors

    @staticmethod
    def _guest_field_errors(invoice: Invoice) -> List[str]:
        errors = []
        user = invoice.guest.user
        if not user.email:
            errors.append('Guest email is required')

        if not user.first_name or not user.last_name:
            errors.append('Guest first and last name are required')
        return errors

    @staticmethod
    def _consistency_errors(invoice: Invoice) -> List[str]:
        errors = []
        # Validate date consistency
        if invoice.issued_date.date() > invoice.due_date:
            errors.append('Due date must be after issue date')

        # Validate amounts
        expected_total = invoice.amount + (invoice.tax_amount or Decimal('0'))
        if invoice.total_amount != expected_total:
            errors.append(f'Total amount mismatch: expected {expected_total}, got {invoice.total_amount}')
        return errors

    def validate_invoice_for_transmission(self, invoice: Invoice) -> Tuple[bool, List[str]]:
        """
        Validate invoice meets MyData requirements.
        
        Args:
            invoice: Invoice to validate
            
        Returns:
            Tuple of (is_valid: bool, error_list: List[str])
        """
        errors = []
        errors.extend(self._required_field_errors(invoice))
        errors.extend(self._guest_field_errors(invoice))
        errors.extend(self._consistency_errors(invoice))

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
