"""
Custom Exception Handling for NEPHELE HMS API

Per Task 4: Error Handling & Logging specifications
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler to provide consistent error response format.
    
    Response format per Task 4 API Design:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "User-friendly message",
            "details": [{"field": "...", "message": "..."}]
        },
        "meta": {
            "timestamp": "...",
            "request_id": "..."
        }
    }
    """
    
    # Get the standard exception handler response
    response = exception_handler(exc, context)
    
    if response is not None:
        # Extract error code and message from response
        if isinstance(response.data, dict):
            # Handle validation errors
            if 'detail' in response.data:
                error_message = str(response.data['detail'])
                error_code = 'VALIDATION_ERROR'
            else:
                # Field-level validation errors
                error_code = 'VALIDATION_ERROR'
                error_message = 'Invalid input parameters'
                
            # Format the response
            formatted_response = {
                'error': {
                    'code': error_code,
                    'message': error_message,
                    'details': response.data if isinstance(response.data, list) 
                                else [{'field': k, 'message': v[0]} 
                                     for k, v in response.data.items() 
                                     if k != 'detail']
                },
                'meta': {
                    'timestamp': context['request'].META.get('HTTP_X_REQUEST_TIME', ''),
                    'request_id': context['request'].META.get('HTTP_X_REQUEST_ID', '')
                }
            }
            response.data = formatted_response
        
        # Log the error
        if response.status_code >= 400:
            logger.warning(
                f"API Error: {response.status_code} - {exc.__class__.__name__}",
                extra={'status_code': response.status_code, 'exception': str(exc)}
            )
    else:
        # Handle unexpected errors
        logger.error(
            f"Unhandled Exception: {exc.__class__.__name__}",
            exc_info=True,
            extra={'exception': str(exc)}
        )
        
        response = Response(
            {
                'error': {
                    'code': 'INTERNAL_SERVER_ERROR',
                    'message': 'An unexpected error occurred',
                    'details': [] if not logger.root.level == logging.DEBUG else [str(exc)]
                },
                'meta': {
                    'timestamp': context['request'].META.get('HTTP_X_REQUEST_TIME', ''),
                    'request_id': context['request'].META.get('HTTP_X_REQUEST_ID', '')
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response
