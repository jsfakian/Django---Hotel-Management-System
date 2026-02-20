import uuid
from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.db import transaction as db_transaction

from accounts.models import Guest
from accounts.permissions import require_role, get_user_role
from room.models import Booking
from .models import Payment, PaymentMethod, Invoice, RefundRequest
from .forms import PaymentForm, PaymentVerificationForm, RefundRequestForm, InvoiceFilterForm


def generate_transaction_id():
    """Generate unique transaction ID"""
    return f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"


def generate_reference_code():
    """Generate unique reference code for payment"""
    return f"REF-{str(uuid.uuid4())[:12].upper()}"


def send_verification_email(payment, verification_code):
    """Send verification code to guest's email"""
    try:
        guest = payment.guest
        subject = 'Hotel Management System - Payment Verification Code'
        message = f"""
        Hello {guest.user.first_name or guest.user.username},
        
        Your payment verification code is: {verification_code}
        
        Please enter this code to complete your payment. This code will expire in 30 minutes.
        
        If you did not initiate this payment, please contact us immediately.
        
        Best regards,
        Hotel Management System
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [guest.user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        return False


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def process_payment(request, booking_id=None):
    """
    Process payment for a booking or service
    """
    role = get_user_role(request.user)
    
    # Get guest
    try:
        guest = Guest.objects.get(user=request.user)
    except Guest.DoesNotExist:
        messages.error(request, 'Guest profile not found. Please complete your profile.')
        return redirect('guest-edit', pk=request.user.id)
    
    # Get booking if provided
    booking = None
    if booking_id:
        booking = get_object_or_404(Booking, id=booking_id, guest=guest)
    
    # Get payment methods
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            amount = form.cleaned_data['amount']
            
            # Create payment record
            with db_transaction.atomic():
                payment = Payment.objects.create(
                    guest=guest,
                    booking=booking,
                    payment_method=payment_method,
                    amount=amount,
                    currency='EUR',
                    transaction_id=generate_transaction_id(),
                    reference_code=generate_reference_code(),
                    status='processing',
                    description=f'Payment for booking' if booking else 'Service payment'
                )
                
                # Generate verification code if required
                if payment_method.requires_verification:
                    code = payment.generate_verification_code()
                    success = send_verification_email(payment, code)
                    
                    if success:
                        messages.success(request, 'Verification code sent to your email.')
                        return redirect('payment-verify', payment_id=payment.id)
                    else:
                        messages.error(request, 'Failed to send verification code. Please try again.')
                        payment.delete()
                        return redirect('payment-process', booking_id=booking_id)
                else:
                    # Mark as completed for non-verification methods
                    payment.mark_as_completed()
                    messages.success(request, f'Payment of {amount} {payment.currency} completed successfully!')
                    
                    # Send confirmation email
                    try:
                        send_mail(
                            'Payment Confirmation',
                            f'Your payment of {amount} {payment.currency} has been processed successfully. Reference: {payment.reference_code}',
                            settings.DEFAULT_FROM_EMAIL,
                            [guest.user.email],
                            fail_silently=True,
                        )
                    except:
                        pass
                    
                    return redirect('payment-success', payment_id=payment.id)
    else:
        # Calculate amount based on booking
        initial_amount = 0
        if booking:
            from datetime import date as date_class
            start = datetime.strptime(str(booking.startDate), '%Y-%m-%d').date()
            end = datetime.strptime(str(booking.endDate), '%Y-%m-%d').date()
            days = (end - start).days
            initial_amount = booking.roomNumber.price * days
        
        form = PaymentForm(initial={'amount': initial_amount})
    
    context = {
        'role': role,
        'form': form,
        'booking': booking,
        'payment_methods': payment_methods,
    }
    
    return render(request, 'common_pages/payment-process.html', context)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def verify_payment(request, payment_id):
    """
    Verify payment with code
    """
    role = get_user_role(request.user)
    
    try:
        guest = Guest.objects.get(user=request.user)
    except Guest.DoesNotExist:
        messages.error(request, 'Guest profile not found.')
        return redirect('home')
    
    payment = get_object_or_404(Payment, id=payment_id, guest=guest)
    
    # Check if payment is expired
    if payment.is_expired():
        payment.mark_as_failed('Verification code expired')
        messages.error(request, 'Payment verification code has expired. Please try again.')
        return redirect('payment-process', booking_id=payment.booking.id if payment.booking else None)
    
    if request.method == 'POST':
        form = PaymentVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['verification_code']
            if payment.verify(code):
                messages.success(request, 'Payment verified and completed successfully!')
                return redirect('payment-success', payment_id=payment.id)
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
    else:
        form = PaymentVerificationForm()
    
    context = {
        'role': role,
        'form': form,
        'payment': payment,
    }
    
    return render(request, 'common_pages/payment-verify.html', context)


@login_required(login_url='login')
@require_http_methods(["GET"])
def payment_success(request, payment_id):
    """
    Payment success page
    """
    role = get_user_role(request.user)
    
    try:
        guest = Guest.objects.get(user=request.user)
    except Guest.DoesNotExist:
        messages.error(request, 'Guest profile not found.')
        return redirect('home')
    
    payment = get_object_or_404(Payment, id=payment_id, guest=guest, status='completed')
    invoice = getattr(payment, 'invoice', None)
    
    context = {
        'role': role,
        'payment': payment,
        'invoice': invoice,
    }
    
    return render(request, 'common_pages/payment-success.html', context)


@login_required(login_url='login')
@require_http_methods(["GET"])
def payment_history(request):
    """
    View payment history
    """
    role = get_user_role(request.user)
    
    try:
        guest = Guest.objects.get(user=request.user)
    except Guest.DoesNotExist:
        messages.error(request, 'Guest profile not found.')
        return redirect('home')
    
    payments = Payment.objects.filter(guest=guest).select_related('booking', 'payment_method')
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        payments = payments.filter(status=status)
    
    context = {
        'role': role,
        'payments': payments,
        'status_choices': Payment.STATUS_CHOICES,
        'selected_status': status,
    }
    
    return render(request, 'common_pages/payment-history.html', context)


@login_required(login_url='login')
@require_http_methods(["GET"])
def invoice_list(request):
    """
    View list of invoices
    """
    role = get_user_role(request.user)
    
    try:
        guest = Guest.objects.get(user=request.user)
    except Guest.DoesNotExist:
        messages.error(request, 'Guest profile not found.')
        return redirect('home')
    
    invoices = Invoice.objects.filter(guest=guest)
    
    # Apply filters
    form = InvoiceFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('status'):
            invoices = invoices.filter(status=form.cleaned_data['status'])
        
        if form.cleaned_data.get('start_date'):
            invoices = invoices.filter(issued_date__date__gte=form.cleaned_data['start_date'])
        
        if form.cleaned_data.get('end_date'):
            invoices = invoices.filter(issued_date__date__lte=form.cleaned_data['end_date'])
    
    context = {
        'role': role,
        'invoices': invoices,
        'form': form,
    }
    
    return render(request, 'common_pages/invoice-list.html', context)


@login_required(login_url='login')
@require_http_methods(["GET"])
def invoice_detail(request, invoice_id):
    """
    View invoice details
    """
    role = get_user_role(request.user)
    
    try:
        guest = Guest.objects.get(user=request.user)
    except Guest.DoesNotExist:
        messages.error(request, 'Guest profile not found.')
        return redirect('home')
    
    invoice = get_object_or_404(Invoice, id=invoice_id, guest=guest)
    
    context = {
        'role': role,
        'invoice': invoice,
    }
    
    return render(request, 'common_pages/invoice-detail.html', context)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def request_refund(request, payment_id):
    """
    Request refund for a payment
    """
    role = get_user_role(request.user)
    
    try:
        guest = Guest.objects.get(user=request.user)
    except Guest.DoesNotExist:
        messages.error(request, 'Guest profile not found.')
        return redirect('home')
    
    payment = get_object_or_404(Payment, id=payment_id, guest=guest)
    
    # Check if payment can be refunded
    if payment.status != 'completed':
        messages.error(request, 'Only completed payments can be refunded.')
        return redirect('payment-history')
    
    if request.method == 'POST':
        form = RefundRequestForm(request.POST)
        if form.is_valid():
            refund = RefundRequest.objects.create(
                payment=payment,
                guest=guest,
                refund_amount=payment.amount,
                reason=form.cleaned_data['reason'],
                description=form.cleaned_data['description'],
            )
            messages.success(request, 'Refund request submitted successfully. We will review it and contact you soon.')
            return redirect('payment-history')
    else:
        form = RefundRequestForm()
    
    context = {
        'role': role,
        'form': form,
        'payment': payment,
    }
    
    return render(request, 'common_pages/request-refund.html', context)


@login_required(login_url='login')
@require_http_methods(["GET"])
def refund_history(request):
    """
    View refund request history
    """
    role = get_user_role(request.user)
    
    try:
        guest = Guest.objects.get(user=request.user)
    except Guest.DoesNotExist:
        messages.error(request, 'Guest profile not found.')
        return redirect('home')
    
    refunds = RefundRequest.objects.filter(guest=guest)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        refunds = refunds.filter(status=status)
    
    context = {
        'role': role,
        'refunds': refunds,
        'status_choices': RefundRequest.STATUS_CHOICES,
        'selected_status': status,
    }
    
    return render(request, 'common_pages/refund-history.html', context)


@require_role('admin', 'manager')
@require_http_methods(["GET", "POST"])
def manage_refund(request, refund_id):
    """
    Manage refund requests (approve/reject)
    """
    role = get_user_role(request.user)
    
    refund = get_object_or_404(RefundRequest, id=refund_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            refund.approve(request.user)
            messages.success(request, 'Refund approved. Processing will begin shortly.')
        
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '')
            refund.reject(reason, request.user)
            messages.success(request, 'Refund request rejected.')
        
        elif action == 'process':
            if refund.status == 'approved':
                refund.process(request.user)
                messages.success(request, 'Refund processed successfully.')
            else:
                messages.error(request, 'Only approved refunds can be processed.')
        
        return redirect('refund-detail', refund_id=refund.id)
    
    context = {
        'role': role,
        'refund': refund,
    }
    
    return render(request, 'common_pages/manage-refund.html', context)


# ============= MyData (AADE) Integration Views =============

@login_required(login_url='login')
@require_http_methods(["POST"])
def transmit_invoice_to_mydata(request, invoice_id):
    """
    Transmit an invoice to MyData (Greek tax authority system)
    """
    try:
        from .mydata_service import get_mydata_service
        
        invoice = get_object_or_404(Invoice, id=invoice_id)
        
        # Permission check: User should be staff or the invoice guest
        if not (request.user.is_staff or (hasattr(request.user, 'guest') and request.user.guest == invoice.guest)):
            messages.error(request, 'You do not have permission to transmit this invoice.')
            return redirect('invoice-detail', invoice_id=invoice_id)
        
        # Check if already transmitted
        if invoice.mydata_transmitted:
            messages.warning(request, 'This invoice has already been transmitted to MyData.')
            return redirect('invoice-detail', invoice_id=invoice_id)
        
        # Validate invoice
        mydata_service = get_mydata_service()
        is_valid, validation_errors = mydata_service.validate_invoice_for_transmission(invoice)
        
        if not is_valid:
            for error in validation_errors:
                messages.error(request, f'Validation error: {error}')
            return redirect('invoice-detail', invoice_id=invoice_id)
        
        # Transmit invoice
        success, result = mydata_service.transmit_invoice(invoice)
        
        if success:
            messages.success(request, f'Invoice transmitted to MyData. Transmission ID: {result}')
        else:
            messages.error(request, f'MyData transmission failed: {result}')
        
        return redirect('invoice-detail', invoice_id=invoice_id)
        
    except Exception as e:
        messages.error(request, f'Error transmitting invoice: {str(e)}')
        return redirect('invoice-detail', invoice_id=invoice_id)


@login_required(login_url='login')
@require_http_methods(["GET"])
def mydata_transmission_status(request, invoice_id):
    """
    Get MyData transmission status for an invoice
    """
    from django.http import JsonResponse
    
    try:
        invoice = get_object_or_404(Invoice, id=invoice_id)
        
        # Permission check
        if not (request.user.is_staff or (hasattr(request.user, 'guest') and request.user.guest == invoice.guest)):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        return JsonResponse({
            'invoice_number': invoice.invoice_number,
            'mydata_transmitted': invoice.mydata_transmitted,
            'transmission_id': invoice.mydata_transmission_id or '',
            'transmission_date': invoice.mydata_transmission_date.isoformat() if invoice.mydata_transmission_date else None,
            'qr_code': invoice.mydata_qr_code or '',
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='login')
@require_http_methods(["GET"])
def bulk_transmit_invoices_to_mydata(request):
    """
    Bulk transmit all pending invoices to MyData.
    Staff only operation.
    """
    from django.http import JsonResponse
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        from .mydata_service import get_mydata_service
        
        mydata_service = get_mydata_service()
        results = mydata_service.bulk_transmit_invoices()
        
        if request.GET.get('format') == 'json':
            return JsonResponse(results)
        
        # Redirect with success message
        success_msg = f"MyData transmission complete: {results['successful']} successful, {results['failed']} failed"
        messages.success(request, success_msg)
        
        if results['failed'] > 0:
            for error in results['errors'][:5]:  # Show first 5 errors
                messages.warning(request, f"{error.get('invoice_number')}: {error.get('error', str(error.get('errors')))}")
        
        return redirect('invoice-list')
        
    except Exception as e:
        error_msg = f'Bulk MyData transmission failed: {str(e)}'
        if request.GET.get('format') == 'json':
            return JsonResponse({'error': error_msg}, status=400)
        
        messages.error(request, error_msg)
        return redirect('invoice-list')


@login_required(login_url='login')
@require_http_methods(["GET"])
def invoice_mydata_export(request, invoice_id):
    """
    Export invoice in MyData-compatible format (JSON)
    """
    from django.http import JsonResponse
    
    try:
        invoice = get_object_or_404(Invoice, id=invoice_id)
        
        # Permission check
        if not (request.user.is_staff or (hasattr(request.user, 'guest') and request.user.guest == invoice.guest)):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        from .mydata_service import get_mydata_service
        
        mydata_service = get_mydata_service()
        export_data = mydata_service.export_invoice(invoice)
        
        return JsonResponse(export_data, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

