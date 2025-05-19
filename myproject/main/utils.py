from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import logging
import functools
from django.core.exceptions import ValidationError, ObjectDoesNotExist

logger = logging.getLogger(__name__)


def exception_handler(func):
    """
    Decorator to handle exceptions in view methods
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.error(f"Validation error in {func.__name__}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            logger.error(f"Object not found in {func.__name__}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An unexpected error occurred. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return wrapper


def transaction_atomic(func):
    """
    Decorator to wrap function in a transaction
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with transaction.atomic():
            return func(*args, **kwargs)

    return wrapper
