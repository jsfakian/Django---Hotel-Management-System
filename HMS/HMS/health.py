from django.db import connection
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def healthz(request):
    """Legacy health check endpoint (deprecated, use /health/ instead)."""
    return health_check(request)


def health_check(request):
    """
    Comprehensive health check endpoint.
    
    Returns JSON with status of:
    - Application
    - Database
    - Cache (Redis)
    - Services
    
    Returns 200 if all OK, 503 if any service is down.
    """
    health_status = {
        'status': 'healthy',
        'services': {},
        'timestamp': __import__('django.utils.timezone', fromlist=['now']).now().isoformat()
    }
    http_status = 200
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        health_status['services']['database'] = 'ok'
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        health_status['services']['database'] = 'down'
        health_status['status'] = 'unhealthy'
        http_status = 503
    
    # Check cache (Redis)
    try:
        test_key = 'health_check_test'
        cache.set(test_key, 'test_value', 10)
        cached_value = cache.get(test_key)
        if cached_value == 'test_value':
            cache.delete(test_key)
            health_status['services']['cache'] = 'ok'
        else:
            health_status['services']['cache'] = 'down'
            health_status['status'] = 'unhealthy'
            http_status = 503
    except Exception as exc:
        logger.error(f"Cache health check failed: {exc}")
        health_status['services']['cache'] = 'down'
        health_status['status'] = 'unhealthy'
        http_status = 503
    
    # Check Celery (if configured)
    try:
        if hasattr(settings, 'CELERY_BROKER_URL'):
            from celery import current_app
            current_app.control.inspect().active() is not None
            health_status['services']['celery'] = 'ok'
    except Exception as exc:
        logger.warning(f"Celery health check failed (optional): {exc}")
        health_status['services']['celery'] = 'warning'
    
    return JsonResponse(health_status, status=http_status)


def health_db(request):
    """Database-only health check."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        return JsonResponse({'status': 'ok'}, status=200)
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        return JsonResponse({'status': 'down', 'error': str(exc)}, status=503)


def health_cache(request):
    """Cache-only health check."""
    try:
        test_key = 'cache_health_check'
        cache.set(test_key, 'ok', 10)
        if cache.get(test_key) == 'ok':
            cache.delete(test_key)
            return JsonResponse({'status': 'ok'}, status=200)
        else:
            return JsonResponse({'status': 'down'}, status=503)
    except Exception as exc:
        logger.error(f"Cache health check failed: {exc}")
        return JsonResponse({'status': 'down', 'error': str(exc)}, status=503)
