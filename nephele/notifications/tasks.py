"""
Celery tasks for notifications

Handles email, SMS, and in-app notifications for various events.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_channel_booking_alert(booking_id, channel_name):
    """
    Send staff notification email when a booking is received from an OTA channel.
    
    This task is called when:
    - Booking received from Trivago
    - Booking received from Booking.com
    - Booking received from Airbnb
    - Booking received from any other OTA platform
    """
    try:
        from room.models import Booking
        from django.contrib.auth.models import User
        
        booking = Booking.objects.get(id=booking_id)
        property = booking.room.property
        
        # Get all active staff at property
        staff_users = User.objects.filter(
            employee__property=property,
            employee__status='active',
            is_active=True
        ).distinct()
        
        if not staff_users.exists():
            logger.warning(f"No active staff found for property {property}")
            return
        
        # Prepare email data
        context = {
            'channel_name': channel_name,
            'guest_name': f"{booking.guest.first_name} {booking.guest.last_name}",
            'guest_email': booking.guest.email,
            'guest_phone': booking.guest.phone or 'Not provided',
            'room_number': booking.room.room_number,
            'room_type': booking.room.get_room_type_display(),
            'check_in': booking.check_in_date,
            'check_out': booking.check_out_date,
            'nights': (booking.check_out_date - booking.check_in_date).days,
            'guests': booking.number_of_guests,
            'price': booking.actual_price or booking.base_price,
            'currency': 'USD',  # Configurable
            'special_requests': booking.special_requests or 'None',
            'booking_id': booking.id,
            'property_name': property.name,
        }
        
        # Send email to each staff member
        subject = f"New {channel_name} Booking - {booking.room.room_number}, {booking.check_in_date.strftime('%b %d')} to {booking.check_out_date.strftime('%b %d')}"
        
        # Simple HTML email (can be enhanced with template later)
        html_message = f"""
<html>
<head></head>
<body>
<p>Hi,</p>
<p>A new booking has been received from <strong>{channel_name}</strong></p>

<h2>Booking Details</h2>
<ul>
<li><strong>Guest:</strong> {context['guest_name']} ({context['guest_email']})</li>
<li><strong>Phone:</strong> {context['guest_phone']}</li>
<li><strong>Room:</strong> {context['room_number']} ({context['room_type']})</li>
<li><strong>Check-in:</strong> {context['check_in']} at 3:00 PM</li>
<li><strong>Check-out:</strong> {context['check_out']} at 11:00 AM</li>
<li><strong>Nights:</strong> {context['nights']}</li>
<li><strong>Guests:</strong> {context['guests']} {('adult' if context['guests'] == 1 else 'adults')}</li>
<li><strong>Total Price:</strong> ${context['price']} USD</li>
<li><strong>Special Requests:</strong> {context['special_requests']}</li>
</ul>

<p><a href="/admin/room/booking/{booking_id}/change/">View in NEPHELE</a></p>

<p>Best regards,<br/>NEPHELE</p>
</body>
</html>
"""
        
        # Send to all staff
        recipient_list = [user.email for user in staff_users if user.email]
        
        if recipient_list:
            try:
                send_mail(
                    subject=subject,
                    message=strip_tags(html_message),
                    from_email='nephele-alerts@nephele.io',
                    recipient_list=recipient_list,
                    html_message=html_message,
                    fail_silently=False
                )
                logger.info(f"Channel booking alert sent to {len(recipient_list)} staff for booking {booking_id}")
            except Exception as e:
                logger.error(f"Failed to send channel booking alert: {e}")
        else:
            logger.warning(f"No email addresses found for staff at property {property}")
    
    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_id} not found")
    except Exception as e:
        logger.error(f"Error sending channel booking alert: {e}")


@shared_task
def send_travel_agent_availability_update(property_id, room_ids=None, channel=None):
    """
    Send optional email to travel agents when availability updates.
    
    Triggered when room availability increases (e.g., cancellation).
    """
    try:
        from contracts.models import Contract
        from properties.models import Property
        
        property = Property.objects.get(id=property_id)
        
        # Get travel agents with active contracts
        contracts = Contract.objects.filter(
            property=property,
            status='active',
            start_date__lte=__import__('django.utils.timezone', fromlist=['now']).now().date(),
            end_date__gte=__import__('django.utils.timezone', fromlist=['now']).now().date()
        )
        
        if not contracts.exists():
            logger.info(f"No active contracts for property {property}")
            return
        
        # Notify travel agencies (implementation per agency preference)
        for contract in contracts:
            logger.info(f"Would send availability update to {contract.travel_agency.name}")
            # TODO: Implement email sending to travel agencies
    
    except Exception as e:
        logger.error(f"Error sending travel agent availability update: {e}")


@shared_task
def send_booking_confirmation(booking_id):
    """Send booking confirmation email to guest"""
    try:
        from room.models import Booking
        
        booking = Booking.objects.get(id=booking_id)
        
        subject = f"Booking Confirmation - {booking.room.property.name}"
        html_message = f"""
<html>
<body>
<p>Dear {booking.guest.first_name},</p>
<p>Thank you for your booking!</p>
<p>Your booking reference: {booking.id}</p>
<p>Check-in: {booking.check_in_date}</p>
<p>Check-out: {booking.check_out_date}</p>
<p>Total: ${booking.actual_price or booking.base_price}</p>
<p>We look forward to welcoming you!</p>
</body>
</html>
"""
        
        send_mail(
            subject=subject,
            message=strip_tags(html_message),
            from_email='bookings@nephele.io',
            recipient_list=[booking.guest.email],
            html_message=html_message,
            fail_silently=True
        )
    except Exception as e:
        logger.error(f"Error sending booking confirmation: {e}")
