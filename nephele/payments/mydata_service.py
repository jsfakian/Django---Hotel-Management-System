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
    
    def _counterpart_afm(self, invoice: Invoice) -> str:
        """Guest AFM/VAT when available; empty for B2C (never use document_number)."""
        guest = invoice.guest
        if not guest:
            return ""
        prefs = getattr(guest, "preferences", None) or {}
        for key in ("afm", "vat_number", "tax_id"):
            val = prefs.get(key) if isinstance(prefs, dict) else None
            if val:
                return str(val)
        return ""

    def _counterpart_for_invoice(self, invoice: Invoice) -> Dict:
        guest = invoice.guest
        name = ""
        email = self._guest_email_for_invoice(invoice)
        if guest:
            if getattr(guest, "user_id", None) and guest.user:
                name = f"{guest.user.first_name} {guest.user.last_name}".strip()
            if not name:
                name = f"{guest.first_name} {guest.last_name}".strip()
        return {
            "name": name,
            "email": email,
            "afm": self._counterpart_afm(invoice),
            "vatNumber": self._counterpart_afm(invoice),
        }

    def _resolve_line_items_source(self, invoice: Invoice) -> List[Dict]:
        lines_src = getattr(invoice, "line_items", None) or []
        if lines_src or not invoice.booking_id:
            return list(lines_src)
        from payments.invoice_lines import booking_invoice_lines, lines_as_jsonable

        return lines_as_jsonable(booking_invoice_lines(invoice.booking))

    def _summary_mydata_line(
        self, invoice: Invoice, net_amount: Decimal, vat_amount: Decimal
    ) -> Dict:
        return {
            "lineNumber": 1,
            "description": (invoice.description or "")[:255],
            "quantity": 1,
            "unitPrice": float(net_amount),
            "discountPercentage": 0,
            "discount": 0,
            "netAmount": float(net_amount),
            "netValue": float(net_amount),
            "vatCategory": "1",
            "vatAmount": float(vat_amount),
            "grossAmount": float(invoice.total_amount),
        }

    @staticmethod
    def _structured_mydata_line(idx: int, item: Dict) -> Dict:
        amount = float(item.get("amount") or 0)
        qty = int(item.get("quantity") or 1)
        unit = float(item.get("unit_amount") or (amount / qty if qty else amount))
        is_vat = item.get("code") == "VAT" or item.get("tax_category") == "vat"
        net = 0.0 if is_vat else amount
        vat = amount if is_vat else 0.0
        return {
            "lineNumber": idx,
            "description": str(item.get("description") or "")[:255],
            "quantity": qty,
            "unitPrice": unit,
            "discountPercentage": 0,
            "discount": 0,
            "netAmount": net,
            "netValue": net,
            "vatCategory": str(item.get("vat_category") or "1"),
            "vatAmount": vat,
            "grossAmount": amount,
            "code": item.get("code"),
        }

    def _mydata_lines_for_invoice(
        self, invoice: Invoice, net_amount: Decimal, vat_amount: Decimal
    ) -> List[Dict]:
        """Prefer structured booking lines; fall back to a single summary line."""
        lines_src = self._resolve_line_items_source(invoice)
        if not lines_src:
            return [self._summary_mydata_line(invoice, net_amount, vat_amount)]
        return [
            self._structured_mydata_line(idx, item)
            for idx, item in enumerate(lines_src, start=1)
        ]

    def _invoice_series_aa(self, invoice: Invoice) -> Tuple[str, str]:
        """Split invoice_number into series + sequential aa for AADE header."""
        number = invoice.invoice_number or "INV-0"
        parts = number.rsplit("-", 1)
        if len(parts) == 2 and parts[1]:
            return parts[0], parts[1]
        return "INV", number

    def _aade_invoice_details(
        self, lines: List[Dict], net_amount: Decimal, vat_amount: Decimal
    ) -> List[Dict]:
        """AADE invoiceDetails rows (netValue / vatCategory / vatAmount)."""
        details = []
        for line in lines:
            net = float(line.get("netValue", line.get("netAmount", 0)) or 0)
            vat = float(line.get("vatAmount", 0) or 0)
            if line.get("code") == "VAT":
                continue
            details.append(
                {
                    "lineNumber": line.get("lineNumber"),
                    "netValue": net,
                    "vatCategory": str(line.get("vatCategory") or "1"),
                    "vatAmount": vat,
                    "quantity": line.get("quantity", 1),
                    "description": line.get("description", ""),
                }
            )
        if details:
            # Attach invoice-level VAT on first non-VAT line when lines lack VAT.
            if details[0]["vatAmount"] == 0 and float(vat_amount) > 0:
                details[0]["vatAmount"] = float(vat_amount)
            return details
        return [
            {
                "lineNumber": 1,
                "netValue": float(net_amount),
                "vatCategory": "1",
                "vatAmount": float(vat_amount),
                "quantity": 1,
                "description": "",
            }
        ]

    def build_aade_invoice_doc(self, invoice: Invoice) -> Dict:
        """
        AADE myDATA-shaped document used for live SendInvoices POST.

        Mirrors documented fields: issuer/counterpart AFM (vatNumber),
        invoiceHeader, invoiceDetails (vatCategory, netValue, vatAmount),
        invoiceSummary. Also includes a compact XML-ish string for debugging.
        """
        if not invoice.amount:
            raise MyDataServiceException(
                f"Invoice {invoice.invoice_number} has invalid amount"
            )
        vat_amount = invoice.tax_amount or Decimal("0")
        net_amount = invoice.amount
        lines = self._mydata_lines_for_invoice(invoice, net_amount, vat_amount)
        series, aa = self._invoice_series_aa(invoice)
        counterpart = self._counterpart_for_invoice(invoice)
        counterpart_afm = counterpart.get("vatNumber") or counterpart.get("afm") or ""
        details = self._aade_invoice_details(lines, net_amount, vat_amount)
        header = {
            "series": series,
            "aa": aa,
            "issueDate": invoice.issued_date.strftime("%Y-%m-%d"),
            "invoiceType": "2.1",
            "currency": "EUR",
        }
        issuer = {
            "vatNumber": str(self.tax_id),
            "afm": str(self.tax_id),
            "country": "GR",
            "branch": 0,
        }
        counterpart_block = {
            "vatNumber": counterpart_afm,
            "afm": counterpart_afm,
            "name": counterpart.get("name") or "",
            "country": "GR",
            "branch": 0,
        }
        summary = {
            "totalNetValue": float(net_amount),
            "totalVatAmount": float(vat_amount),
            "totalGrossValue": float(invoice.total_amount),
        }
        invoice_node = {
            "issuer": issuer,
            "counterpart": counterpart_block,
            "invoiceHeader": header,
            "paymentMethods": {
                "paymentMethodDetails": [
                    {"type": 1, "amount": float(invoice.total_amount)}
                ]
            },
            "invoiceDetails": details,
            "invoiceSummary": summary,
        }
        xmlish = (
            f"<InvoicesDoc><invoice>"
            f"<issuer><vatNumber>{issuer['vatNumber']}</vatNumber></issuer>"
            f"<counterpart><vatNumber>{counterpart_afm}</vatNumber></counterpart>"
            f"<invoiceHeader><series>{series}</series><aa>{aa}</aa>"
            f"<issueDate>{header['issueDate']}</issueDate>"
            f"<invoiceType>{header['invoiceType']}</invoiceType>"
            f"<currency>EUR</currency></invoiceHeader>"
            f"<invoiceDetails><lineNumber>1</lineNumber>"
            f"<netValue>{summary['totalNetValue']}</netValue>"
            f"<vatCategory>1</vatCategory>"
            f"<vatAmount>{summary['totalVatAmount']}</vatAmount>"
            f"</invoiceDetails>"
            f"<invoiceSummary>"
            f"<totalNetValue>{summary['totalNetValue']}</totalNetValue>"
            f"<totalVatAmount>{summary['totalVatAmount']}</totalVatAmount>"
            f"<totalGrossValue>{summary['totalGrossValue']}</totalGrossValue>"
            f"</invoiceSummary></invoice></InvoicesDoc>"
        )
        return {
            "InvoicesDoc": {"invoice": [invoice_node]},
            "xml": xmlish,
        }

    def export_invoice(self, invoice: Invoice) -> Dict:
        """
        Export invoice in MyData-compatible JSON format.

        Sandbox / UI export keeps the legacy ``invoice`` envelope. Live
        transmission uses :meth:`build_aade_invoice_doc` instead.
        """
        if not invoice.amount:
            raise MyDataServiceException(f'Invoice {invoice.invoice_number} has invalid amount')
        
        # Calculate VAT information
        vat_amount = invoice.tax_amount or Decimal('0')
        net_amount = invoice.amount
        lines = self._mydata_lines_for_invoice(invoice, net_amount, vat_amount)
        counterpart = self._counterpart_for_invoice(invoice)
        series, aa = self._invoice_series_aa(invoice)

        export_data = {
            'invoice': {
                'mark': invoice.mydata_transmission_id or '',
                'invoiceNumber': invoice.invoice_number,
                'issueDate': invoice.issued_date.strftime('%Y-%m-%d'),
                'dueDate': invoice.due_date.strftime('%Y-%m-%d'),
                'currency': 'EUR',
                'issuer': {
                    'taxId': self.tax_id,
                    'afm': self.tax_id,
                    'vatNumber': self.tax_id,
                },
                'counterpart': counterpart,
                'invoiceHeader': {
                    'series': series,
                    'aa': aa,
                    'issueDate': invoice.issued_date.strftime('%Y-%m-%d'),
                    'invoiceType': '2.1',
                    'currency': 'EUR',
                },
                'invoiceDetails': self._aade_invoice_details(
                    lines, net_amount, vat_amount
                ),
                'lines': lines,
                'totals': {
                    'netAmount': float(net_amount),
                    'vatAmount': float(vat_amount),
                    'grossAmount': float(invoice.total_amount),
                    'itemsNumber': len(lines),
                    'linesNumber': len(lines),
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
    
    @staticmethod
    def _guest_email_for_invoice(invoice: Invoice) -> str:
        if not invoice.guest_id:
            return ''
        guest_email = ''
        if getattr(invoice.guest, 'user_id', None) and invoice.guest.user:
            guest_email = invoice.guest.user.email or ''
        return guest_email or getattr(invoice.guest, 'email', '') or ''

    @staticmethod
    def _response_body(response) -> Dict:
        try:
            return response.json()
        except ValueError:
            return {'raw': response.text}

    def _sandbox_transmit(self, invoice: Invoice, qr_code: str) -> Tuple[bool, str]:
        transmission_id = self._generate_transmission_id(invoice)
        invoice.mark_as_mydata_transmitted(transmission_id, qr_code)
        return True, transmission_id

    def _live_transmit(self, invoice: Invoice, qr_code: str) -> Tuple[bool, str]:
        if not self.username or not self.subscription_key:
            return (
                False,
                'MYDATA_USERNAME and MYDATA_SUBSCRIPTION_KEY (or MYDATA_API_KEY) '
                'required when MYDATA_SANDBOX_MODE=False',
            )

        aade_payload = self.build_aade_invoice_doc(invoice)
        headers = self._auth_headers()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{self.api_base}/SendInvoices',
            json=aade_payload,
            headers=headers,
            timeout=self.timeout,
        )
        body = self._response_body(response)
        if response.status_code >= 400:
            return False, f'MyData HTTP {response.status_code}: {body}'

        transmission_id = (
            str(body.get('transmission_id') or body.get('mark') or body.get('uid') or '')
            or self._generate_transmission_id(invoice)
        )
        invoice.mark_as_mydata_transmitted(transmission_id, qr_code)
        return True, transmission_id

    def transmit_invoice(self, invoice: Invoice) -> Tuple[bool, str]:
        """
        Transmit invoice to MyData.

        When MYDATA_SANDBOX_MODE is True, keep the local mock MARK.
        When False, POST AADE-shaped InvoicesDoc to MYDATA_API_BASE.
        """
        try:
            if not invoice.amount or invoice.amount <= 0:
                return False, f'Invalid invoice amount: {invoice.amount}'

            if not self._guest_email_for_invoice(invoice):
                return False, 'Guest email is required for MyData transmission'

            qr_code = self.generate_qr_code_data(invoice)

            if self.sandbox_mode:
                # Sandbox still validates export shape without remote HTTP.
                self.export_invoice(invoice)
                return self._sandbox_transmit(invoice, qr_code)
            return self._live_transmit(invoice, qr_code)

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
