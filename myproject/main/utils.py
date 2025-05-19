import logging
from django.db import transaction
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import APIException, AuthenticationFailed, NotAuthenticated, PermissionDenied
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF to provide consistent error responses.
    """
    response = drf_exception_handler(exc, context)

    if response is not None:
        response.data['status_code'] = response.status_code
        logger.error(f"API Exception: {str(exc)}")
        return response

    if isinstance(exc, ValidationError):
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, ObjectDoesNotExist):
        return Response({'error': str(exc)}, status=status.HTTP_404_NOT_FOUND)

    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return Response(
        {'error': 'An unexpected error occurred.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def transaction_atomic(func):
    """
    Decorator to wrap view methods in a database transaction.
    """
    return transaction.atomic()(func)
