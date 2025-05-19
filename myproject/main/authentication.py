from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
import logging
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken


from .models import Notification

logger = logging.getLogger(__name__)

CustomUser = get_user_model()


class CookieJWTAuthentication(BaseAuthentication):
    """
    Custom authentication class to validate JWT tokens from cookies.
    """

    def authenticate(self, request):
        access_token = request.COOKIES.get('access_token')

        if not access_token:
            logger.debug("No access token found in cookies")
            return None

        try:
            # Validate the token
            token = AccessToken(access_token)
            user_id = token.payload.get('user_id')
            if not user_id:
                logger.error("No user_id in token payload")
                raise AuthenticationFailed('Invalid token')

            # Get the user
            user = CustomUser.objects.get(id=user_id)
            if not user.is_active:
                logger.error(f"User {user_id} is inactive")
                raise AuthenticationFailed('User account is disabled')

            logger.debug(f"Authenticated user: {user.username}")
            return (user, token)

        except (TokenError, InvalidToken) as e:
            logger.error(f"Invalid access token: {str(e)}")
            raise AuthenticationFailed('Invalid or expired token')
        except CustomUser.DoesNotExist:
            logger.error(f"User with ID {user_id} not found")
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            raise AuthenticationFailed('Invalid token')
