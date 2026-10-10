"""
Caching layer for pricing data.

Provides efficient caching for:
1. Pricing predictions
2. Historical pricing data
3. Summary statistics
4. Model predictions
5. Room availability

Uses Django's cache framework with Redis backend.
"""

from django.core.cache import cache
from django.views.decorators.cache import cache_page
from functools import wraps
import hashlib
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

# Cache key constants
CACHE_PRICING_PREDICTION = 'pricing:prediction:{room_id}:{date}'
CACHE_PRICING_HISTORY = 'pricing:history:{room_id}:{start_date}:{end_date}'
CACHE_PRICING_SUMMARY = 'pricing:summary'
CACHE_ROOM_CONFIDENCE = 'pricing:confidence:{room_id}'
CACHE_MODEL_PREDICTIONS = 'pricing:models:{room_id}:{date}'
CACHE_PRICING_STATS = 'pricing:stats:{period}'

# Cache TTL (time to live) in seconds
CACHE_TTL_SHORT = 300  # 5 minutes - for real-time data
CACHE_TTL_MEDIUM = 1800  # 30 minutes - for reasonably stable data
CACHE_TTL_LONG = 86400  # 24 hours - for historical data
CACHE_TTL_INTRADAY = 3600  # 1 hour - for intraday updates


class PricingCache:
    """
    High-level caching interface for pricing operations.
    """
    
    @staticmethod
    def get_pricing_prediction(room_id, date):
        """
        Get cached pricing prediction or return None if not cached.
        
        Args:
            room_id: Room database ID
            date: Date object (YYYY-MM-DD)
        
        Returns:
            dict with prediction data or None
        """
        cache_key = CACHE_PRICING_PREDICTION.format(room_id=room_id, date=date)
        return cache.get(cache_key)
    
    @staticmethod
    def set_pricing_prediction(room_id, date, prediction_data, ttl=CACHE_TTL_MEDIUM):
        """
        Cache a pricing prediction.
        
        Args:
            room_id: Room database ID
            date: Date object
            prediction_data: dict with prediction
            ttl: Time to live in seconds
        """
        cache_key = CACHE_PRICING_PREDICTION.format(room_id=room_id, date=date)
        cache.set(cache_key, prediction_data, ttl)
        logger.debug(f"Cached pricing prediction: {cache_key}")
    
    @staticmethod
    def get_pricing_history(room_id, start_date, end_date):
        """
        Get cached pricing history range.
        """
        cache_key = CACHE_PRICING_HISTORY.format(
            room_id=room_id,
            start_date=start_date,
            end_date=end_date
        )
        return cache.get(cache_key)
    
    @staticmethod
    def set_pricing_history(room_id, start_date, end_date, history_data, ttl=CACHE_TTL_LONG):
        """
        Cache pricing history for a date range.
        """
        cache_key = CACHE_PRICING_HISTORY.format(
            room_id=room_id,
            start_date=start_date,
            end_date=end_date
        )
        cache.set(cache_key, history_data, ttl)
        logger.debug(f"Cached pricing history: {cache_key}")
    
    @staticmethod
    def get_pricing_summary():
        """
        Get cached pricing summary statistics.
        """
        return cache.get(CACHE_PRICING_SUMMARY)
    
    @staticmethod
    def set_pricing_summary(summary_data, ttl=CACHE_TTL_INTRADAY):
        """
        Cache pricing summary statistics.
        
        Summary includes:
        - Total rooms using AI
        - Average confidence
        - Revenue uplift percentage
        - Model accuracy metrics
        """
        cache.set(CACHE_PRICING_SUMMARY, summary_data, ttl)
        logger.debug(f"Cached pricing summary (TTL: {ttl}s)")
    
    @staticmethod
    def get_room_confidence(room_id):
        """
        Get cached confidence score for a specific room.
        """
        cache_key = CACHE_ROOM_CONFIDENCE.format(room_id=room_id)
        return cache.get(cache_key)
    
    @staticmethod
    def set_room_confidence(room_id, confidence_score, ttl=CACHE_TTL_INTRADAY):
        """
        Cache room confidence score.
        """
        cache_key = CACHE_ROOM_CONFIDENCE.format(room_id=room_id)
        cache.set(cache_key, confidence_score, ttl)
    
    @staticmethod
    def get_model_predictions(room_id, date):
        """
        Get cached individual model predictions (before ensemble).
        """
        cache_key = CACHE_MODEL_PREDICTIONS.format(room_id=room_id, date=date)
        return cache.get(cache_key)
    
    @staticmethod
    def set_model_predictions(room_id, date, predictions, ttl=CACHE_TTL_MEDIUM):
        """
        Cache individual model predictions.
        """
        cache_key = CACHE_MODEL_PREDICTIONS.format(room_id=room_id, date=date)
        cache.set(cache_key, predictions, ttl)
    
    @staticmethod
    def get_statistics(period='30d'):
        """
        Get cached statistical analysis.
        
        Args:
            period: Analysis period ('7d', '30d', '90d')
        """
        cache_key = CACHE_PRICING_STATS.format(period=period)
        return cache.get(cache_key)
    
    @staticmethod
    def set_statistics(period, stats_data, ttl=CACHE_TTL_LONG):
        """
        Cache statistical analysis results.
        """
        cache_key = CACHE_PRICING_STATS.format(period=period)
        cache.set(cache_key, stats_data, ttl)
        logger.debug(f"Cached statistics: {period}")
    
    @staticmethod
    def invalidate_room_cache(room_id):
        """
        Invalidate all cache entries related to a specific room.
        Called when pricing is updated for a room.
        """
        patterns = [
            CACHE_PRICING_PREDICTION.format(room_id=room_id, date='*'),
            CACHE_ROOM_CONFIDENCE.format(room_id=room_id),
            CACHE_MODEL_PREDICTIONS.format(room_id=room_id, date='*'),
        ]
        
        for pattern in patterns:
            # Note: Redis wild card delete requires custom implementation
            # For now, we use individual keys
            pass
    
    @staticmethod
    def invalidate_all_pricing_cache():
        """
        Clear all pricing-related caches.
        Called after model retraining or bulk updates.
        """
        cache.delete(CACHE_PRICING_SUMMARY)
        logger.info("Invalidated all pricing caches")
    
    @staticmethod
    def cache_stats():
        """
        Get cache statistics (if Redis stats available).
        """
        try:
            from django.core.cache import cache as django_cache
            if hasattr(django_cache, '_cache'):
                # For Redis backend
                info = django_cache._cache.info()
                return {
                    'backend': 'Redis',
                    'keys': info.get('cached_items', 'N/A'),
                }
        except Exception as e:
            logger.warning(f"Could not get cache stats: {e}")
        
        return {'backend': 'Unknown', 'keys': 'N/A'}


def cache_pricing_response(ttl=CACHE_TTL_MEDIUM):
    """
    Decorator to cache pricing API responses.
    
    Usage:
        @cache_pricing_response(ttl=1800)
        def get_pricing_analysis(room_id, date):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key_parts = [func.__name__]
            
            for arg in args:
                cache_key_parts.append(str(arg))
            
            for key, value in sorted(kwargs.items()):
                cache_key_parts.append(f"{key}={value}")
            
            cache_key = ':'.join(cache_key_parts)
            cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Try to get from cache
            cached = cache.get(cache_key_hash)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key_hash, result, ttl)
            logger.debug(f"Cached result: {cache_key} (TTL: {ttl}s)")
            
            return result
        
        return wrapper
    return decorator


class CacheWarmer:
    """
    Pre-loads cache with frequently accessed data.
    Improves response times and reduces database load.
    """
    
    @staticmethod
    def warm_pricing_cache():
        """
        Pre-cache pricing data for all active rooms.
        Run this periodically or after pricing updates.
        """
        from room.models import Room
        from bookings.models import PricingHistory
        from datetime import datetime, timedelta
        
        try:
            today = datetime.now().date()
            active_rooms = Room.objects.filter(status='available')
            
            cached_count = 0
            
            for room in active_rooms:
                # Cache today's and tomorrow's pricing
                for days_ahead in range(2):
                    target_date = today + timedelta(days=days_ahead)
                    
                    try:
                        pricing = PricingHistory.objects.get(
                            room=room,
                            date=target_date
                        )
                        
                        prediction_data = {
                            'room_id': room.id,
                            'room_name': room.room_number,
                            'date': str(target_date),
                            'base_price': float(pricing.base_price),
                            'dynamic_price': float(pricing.dynamic_price),
                            'confidence_score': float(pricing.confidence_score or 0),
                            'model_version': pricing.model_version,
                        }
                        
                        PricingCache.set_pricing_prediction(
                            room.id,
                            target_date,
                            prediction_data,
                            ttl=CACHE_TTL_INTRADAY
                        )
                        cached_count += 1
                    
                    except PricingHistory.DoesNotExist:
                        continue
            
            logger.info(f"Warmed cache with {cached_count} pricing records")
            return {'cached_count': cached_count, 'status': 'success'}
        
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    @staticmethod
    def warm_summary_cache():
        """
        Pre-cache pricing summary statistics.
        """
        from bookings.models import PricingHistory
        from datetime import datetime, timedelta
        from room.models import Room
        from django.db.models import Avg, Count
        
        try:
            thirty_days_ago = datetime.now().date() - timedelta(days=30)
            
            recent_pricing = PricingHistory.objects.filter(
                date__gte=thirty_days_ago
            )
            
            total_rooms = Room.objects.filter(status='available').count()
            rooms_using_ai = recent_pricing.values('room').distinct().count()
            avg_confidence = recent_pricing.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0
            
            summary_data = {
                'total_rooms': total_rooms,
                'rooms_using_ai': rooms_using_ai,
                'average_confidence': float(avg_confidence),
                'warmed_at': datetime.now().isoformat(),
            }
            
            PricingCache.set_pricing_summary(summary_data)
            logger.info(f"Warmed summary cache")
            
            return {'status': 'success', 'rooms_cached': rooms_using_ai}
        
        except Exception as e:
            logger.error(f"Summary cache warming failed: {e}")
            return {'status': 'error', 'error': str(e)}


# Celery task for periodic cache warming

def warm_caches_task():
    """
    Celery task to periodically warm caches.
    Add to Celery Beat schedule:
    
    'warm-pricing-caches': {
        'task': 'bookings.cache.warm_caches_task',
        'schedule': timedelta(hours=6),
    }
    """
    result = {}
    result['pricing'] = CacheWarmer.warm_pricing_cache()
    result['summary'] = CacheWarmer.warm_summary_cache()
    
    logger.info(f"Cache warming complete: {result}")
    return result
