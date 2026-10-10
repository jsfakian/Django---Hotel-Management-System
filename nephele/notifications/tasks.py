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


def _channel_alert_context(booking, channel_name, property):
    return {
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


def _channel_alert_html(context, channel_name, booking_id):
    # Simple HTML email (can be enhanced with template later)
    return f"""
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


def _deliver_channel_alert(booking, staff_users, property, subject, html_message):
    """Email the alert to all staff with an address (failures are only logged)."""
    recipient_list = [user.email for user in staff_users if user.email]

    if not recipient_list:
        logger.warning(f"No email addresses found for staff at property {property}")
        return

    try:
        send_mail(
            subject=subject,
            message=strip_tags(html_message),
            from_email='nephele-alerts@nephele.io',
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Channel booking alert sent to {len(recipient_list)} staff for booking {booking.id}")
    except Exception as e:
        logger.error(f"Failed to send channel booking alert: {e}")


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
        
        context = _channel_alert_context(booking, channel_name, property)
        html_message = _channel_alert_html(context, channel_name, booking_id)
        subject = f"New {channel_name} Booking - {booking.room.room_number}, {booking.check_in_date.strftime('%b %d')} to {booking.check_out_date.strftime('%b %d')}"

        _deliver_channel_alert(booking, staff_users, property, subject, html_message)
    
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


def _property_name_for_booking(booking):
    if booking.room_id and booking.room.property_id:
        return booking.room.property.name
    if booking.room_type_id and booking.room_type.property_id:
        return booking.room_type.property.name
    return 'Nephele'


def _guest_contact(booking):
    guest_name = booking.guest.first_name if booking.guest_id else 'Guest'
    guest_email = booking.guest.email if booking.guest_id else None
    return guest_name, guest_email


def _normalize_locale(value):
    if not value:
        return None
    raw = str(value).lower().split(',')[0].strip().split(';')[0].strip()
    lang = raw.split('-')[0] if raw else ''
    if lang == 'el':
        return 'el'
    if lang == 'en':
        return 'en'
    return None


def _resolve_confirmation_locale(booking, locale=None, accept_language=None):
    """guest language → Accept-Language → booking.locale → default en."""
    if booking.guest_id:
        prefs = getattr(booking.guest, 'preferences', None) or {}
        if isinstance(prefs, dict):
            normalized = _normalize_locale(prefs.get('language') or prefs.get('locale'))
            if normalized:
                return normalized
    for candidate in (
        accept_language,
        locale,
        getattr(booking, 'locale', None),
    ):
        normalized = _normalize_locale(candidate)
        if normalized:
            return normalized
    return 'en'


def _confirmation_email_context(booking, property_name, guest_name):
    return {
        'guest_name': guest_name,
        'confirmation_number': f'NEPH-{booking.id}',
        'check_in': booking.check_in_date,
        'check_out': booking.check_out_date,
        'vat': booking.vat_amount or 0,
        'climate': booking.climate_resilience_fee or 0,
        'total': booking.actual_price or booking.base_price,
        'property_name': property_name,
    }


def _confirmation_subject(locale, property_name):
    from django.utils import translation
    from django.utils.translation import gettext as _

    with translation.override(locale or 'en'):
        return str(_("Booking Confirmation - %(property)s")) % {
            "property": property_name
        }


def _booking_confirmation_html(booking, property_name, guest_name, locale='en'):
    from django.template.exceptions import TemplateDoesNotExist

    context = _confirmation_email_context(booking, property_name, guest_name)
    template_name = f'notifications/email/booking_confirmation_{locale}.html'
    try:
        return render_to_string(template_name, context)
    except TemplateDoesNotExist:
        if locale != 'en':
            return render_to_string(
                'notifications/email/booking_confirmation_en.html', context
            )
        # Last-resort bilingual fallback if templates are missing
        return (
            f"<html><body><p>Dear {guest_name}, / Αγαπητέ/ή {guest_name},</p>"
            f"<p>Confirmation / Επιβεβαίωση: {context['confirmation_number']}</p>"
            f"<p>Total / Σύνολο: €{context['total']}</p>"
            f"<p>{property_name}</p></body></html>"
        )


@shared_task
def send_booking_confirmation(booking_id, locale=None, accept_language=None):
    """Send booking confirmation email to guest (en/el templates)."""
    try:
        from room.models import Booking

        booking = Booking.objects.select_related(
            'room', 'room__property', 'room_type', 'room_type__property', 'guest'
        ).get(id=booking_id)

        property_name = _property_name_for_booking(booking)
        guest_name, guest_email = _guest_contact(booking)
        if not guest_email:
            logger.warning('No guest email for booking %s; skip confirmation', booking_id)
            return

        lang = _resolve_confirmation_locale(
            booking, locale=locale, accept_language=accept_language
        )
        html_message = _booking_confirmation_html(
            booking, property_name, guest_name, locale=lang
        )
        send_mail(
            subject=_confirmation_subject(lang, property_name),
            message=strip_tags(html_message),
            from_email='bookings@nephele.io',
            recipient_list=[guest_email],
            html_message=html_message,
            fail_silently=True
        )
    except Exception as e:
        logger.error(f"Error sending booking confirmation: {e}")
