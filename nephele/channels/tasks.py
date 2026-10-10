"""
Celery tasks for channel integration
"""

from celery import shared_task
from django.db import transaction
from datetime import timedelta
import logging

from .models import Channel, ChannelBooking
from inventory.models import RoomAvailability, AvailabilitySyncLog
from room.models import Room

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5)
def sync_availability_to_channel(self, channel_id, sync_type='full_sync', date_from=None, date_to=None):
    """
    Synchronize room availability to a specific channel/OTA platform.
    
    Handles Trivago, Booking.com, Airbnb, Expedia, Agoda, VRBO, etc.
    """
    try:
        channel = Channel.objects.get(id=channel_id)
    except Channel.DoesNotExist:
        logger.error(f"Channel {channel_id} not found")
        return
    
    if not channel.sync_enabled or not channel.is_active:
        logger.info(f"Channel {channel} sync is disabled")
        return
    
    try:
        with transaction.atomic():
            # Create sync log
            sync_log = AvailabilitySyncLog.objects.create(
                property=channel.property,
                channel=channel,
                sync_type=sync_type,
                sync_status='in_progress',
                date_from=date_from,
                date_to=date_to
            )
            
            # Get rooms to sync
            rooms = Room.objects.filter(property=channel.property)
            rooms_affected = 0
            
            # Build availability data for channel API
            for room in rooms:
                # Get mapping from channel config
                mappings = channel.mapping_config.get('room_mappings', {})
                channel_room_id = mappings.get(str(room.id))
                
                if not channel_room_id:
                    logger.warning(f"No mapping for room {room.id} in channel {channel}")
                    continue
                
                # Get availability records
                avail_records = RoomAvailability.objects.filter(room=room)
                if date_from and date_to:
                    avail_records = avail_records.filter(
                        date__gte=date_from,
                        date__lt=date_to
                    )
                else:
                    # Default to next 30 days
                    from_date = avail_records.aggregate(models.Min('date'))['date__min'] or datetime.now().date()
                    to_date = from_date + timedelta(days=30)
                    avail_records = avail_records.filter(date__gte=from_date, date__lt=to_date)
                
                # Format for channel API (placeholder - actual implementation depends on channel)
                for avail in avail_records:
                    channel_payload = {
                        'room_id': channel_room_id,
                        'date': avail.date.isoformat(),
                        'available': avail.available_units,
                        'booked': avail.booked_units,
                        'price': float(avail.dynamic_price) if avail.dynamic_price else float(avail.base_price)
                    }
                    
                    # Call channel-specific API (implement per channel)
                    _sync_to_channel_api(channel, channel_payload)
                
                rooms_affected += 1
            
            # Mark sync as successful
            sync_log.sync_status = 'success'
            sync_log.completed_at = __import__('django.utils.timezone', fromlist=['now']).now()
            sync_log.rooms_affected = rooms_affected
            sync_log.save()
            
            # Update channel last sync timestamp
            channel.last_sync_at = sync_log.completed_at
            channel.error_count = 0
            channel.last_error = ''
            channel.save()
            
            logger.info(f"Successfully synced {rooms_affected} rooms to {channel}")
    
    except Exception as exc:
        logger.error(f"Error syncing to channel {channel_id}: {exc}")
        
        # Update channel error tracking
        channel.error_count += 1
        channel.last_error = str(exc)
        channel.save()
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries  # 2, 4, 8, 16, 32...
            raise self.retry(exc=exc, countdown=countdown)
        else:
            sync_log = AvailabilitySyncLog.objects.filter(
                channel=channel, sync_status='in_progress'
            ).first()
            if sync_log:
                sync_log.sync_status = 'failed'
                sync_log.error_message = str(exc)
                sync_log.completed_at = __import__('django.utils.timezone', fromlist=['now']).now()
                sync_log.save()


@shared_task
def sync_availability_to_channels(property_id, exclude_channel_id=None, room_ids=None, date_from=None, date_to=None):
    """
    Sync availability to all active channels for a property.
    Used after a booking is created/cancelled to update all OTA platforms.
    """
    try:
        channels = Channel.objects.filter(
            property_id=property_id,
            is_active=True,
            sync_enabled=True
        )
        
        if exclude_channel_id:
            channels = channels.exclude(id=exclude_channel_id)
        
        for channel in channels:
            sync_availability_to_channel.delay(
                channel_id=channel.id,
                sync_type='incremental_sync',
                date_from=date_from,
                date_to=date_to
            )
    except Exception as e:
        logger.error(f"Error syncing availability to channels for property {property_id}: {e}")


def _sync_to_channel_api(channel, payload):
    """
    Internal helper to sync availability to specific channel.
    Implementation varies by channel.
    """
    # This would include actual API calls to each platform
    # For now, this is a placeholder that would be implemented per-channel
    
    if channel.channel_name == 'booking_com':
        _sync_to_booking_com(channel, payload)
    elif channel.channel_name == 'trivago':
        _sync_to_trivago(channel, payload)
    elif channel.channel_name == 'airbnb':
        _sync_to_airbnb(channel, payload)
    elif channel.channel_name == 'expedia':
        _sync_to_expedia(channel, payload)
    # ... other channels


def _sync_to_booking_com(channel, payload):
    """Sync availability to Booking.com"""
    # Implement Booking.com PropertyManagement API
    # https://developers.booking.com/
    logger.warning("Booking.com sync not yet implemented")


def _sync_to_trivago(channel, payload):
    """Sync availability to Trivago"""
    # Implement Trivago API
    logger.warning("Trivago sync not yet implemented")


def _sync_to_airbnb(channel, payload):
    """Sync availability to Airbnb"""
    # Implement Airbnb API
    logger.warning("Airbnb sync not yet implemented")


def _sync_to_expedia(channel, payload):
    """Sync availability to Expedia"""
    # Implement Expedia EAN API
    logger.warning("Expedia sync not yet implemented")
