"""
Celery tasks for accounts app including GDPR data export
"""
import logging
from io import BytesIO
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from celery import current_app as app
from .services.gdpr_export import GDPRExportService
import json

User = get_user_model()
logger = logging.getLogger(__name__)


@app.task(
    name='accounts.export_user_data_async',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def export_user_data_async(self, user_id: int, send_email: bool = True) -> dict:
    """
    Asynchronously export user data for GDPR compliance
    
    Large exports can take time, so this task runs in background.
    Optionally sends the export to user via email.
    
    Args:
        user_id: ID of user to export
        send_email: Whether to email the export to user
    
    Returns:
        Dictionary with export status and file path
    """
    try:
        logger.info(f"Starting async GDPR export for user {user_id}")
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Export data
        service = GDPRExportService(user)
        export_data = service.export_to_dict()
        
        # Convert to JSON
        json_data = json.dumps(
            export_data,
            default=str,
            indent=2
        ).encode('utf-8')
        
        logger.info(f"Export completed for user {user_id}, size: {len(json_data)} bytes")
        
        # Send email if requested
        if send_email:
            send_gdpr_export_email.delay(user_id, json_data.decode('utf-8'))
        
        return {
            'status': 'completed',
            'user_id': user_id,
            'data_size': len(json_data),
            'email_sent': send_email,
        }
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for GDPR export")
        return {'status': 'error', 'reason': 'User not found'}
    except Exception as exc:
        logger.error(f"Error during GDPR export for user {user_id}: {str(exc)}")
        # Retry task with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@app.task(
    name='accounts.send_gdpr_export_email',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_gdpr_export_email(self, user_id: int, json_data: str) -> dict:
    """
    Send GDPR export via email to user
    
    Args:
        user_id: ID of user to receive export
        json_data: JSON string with export data
    
    Returns:
        Dictionary with send status
    """
    try:
        logger.info(f"Preparing to send GDPR export email to user {user_id}")
        
        user = User.objects.get(id=user_id)
        
        # Create email
        email = EmailMessage(
            subject='Your Data Export - GDPR Data Subject Access Request',
            body=f"""
Dear {user.first_name or user.username},

Your requested data export is attached. This file contains all personal data
we hold about you, in accordance with GDPR Article 20 (Right to Data Portability).

File format: JSON
Contents: User profile, bookings, payments, communications, and all related records.

If you have any questions about this export, please contact our Data Protection Officer.

Best regards,
NEPHELE Hotel Management System
Data Protection Team
            """,
            from_email='dpo@nephele.io',
            to=[user.email]
        )
        
        # Attach JSON file
        email.attach(
            f'data_export_{user.id}.json',
            json_data,
            'application/json'
        )
        
        # Send email
        email.send(fail_silently=False)
        
        logger.info(f"GDPR export email sent to {user.email}")
        
        return {
            'status': 'sent',
            'user_id': user_id,
            'recipient': user.email,
        }
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for email send")
        return {'status': 'error', 'reason': 'User not found'}
    except Exception as exc:
        logger.error(f"Error sending GDPR export email to user {user_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@app.task(
    name='accounts.delete_user_data',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def delete_user_data(self, user_id: int) -> dict:
    """
    Soft-delete user data for GDPR right to be forgotten (Article 17)
    
    Anonymizes user data instead of hard deletion to maintain referential integrity.
    
    Args:
        user_id: ID of user to delete
    
    Returns:
        Dictionary with deletion status
    """
    try:
        logger.warning(f"Starting GDPR deletion request for user {user_id}")
        
        user = User.objects.get(id=user_id)
        
        # Anonymize user data
        user.first_name = "Deleted"
        user.last_name = "User"
        user.email = f"deleted_user_{user_id}@invalid.local"
        user.username = f"deleted_user_{user_id}"
        user.is_active = False
        user.save()
        
        # Anonymize guest profile if exists
        try:
            guest = user.guest
            guest.phone = "[ANONYMIZED]"
            guest.address = "[ANONYMIZED]"
            guest.city = "[ANONYMIZED]"
            guest.country = "[ANONYMIZED]"
            guest.postal_code = "[ANONYMIZED]"
            guest.nationality = "[ANONYMIZED]"
            guest.preferences = {}
            guest.save()
        except:
            pass
        
        # Anonymize employee profile if exists
        try:
            employee = user.employee
            employee.phone = "[ANONYMIZED]"
            employee.email = f"deleted_user_{user_id}@invalid.local"
            employee.save()
        except:
            pass
        
        logger.warning(f"GDPR deletion completed for user {user_id}")
        
        return {
            'status': 'completed',
            'user_id': user_id,
            'action': 'user_anonymized',
        }
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for deletion")
        return {'status': 'error', 'reason': 'User not found'}
    except Exception as exc:
        logger.error(f"Error during GDPR deletion for user {user_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
