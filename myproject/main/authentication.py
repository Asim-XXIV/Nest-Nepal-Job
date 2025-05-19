# authentication.py
from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()


class CookieJWTAuthentication(BaseAuthentication):
    """
    Authentication using JWT token stored in cookies
    """

    def authenticate(self, request):
        access_token = request.COOKIES.get('access_token')
        if not access_token:
            return None  # No token in cookies, skip authentication

        try:
            token = AccessToken(access_token)
            user_id = token['user_id']
            user = User.objects.get(id=user_id)

            if not user.is_active:
                raise AuthenticationFailed('User inactive or deleted')

            return (user, None)  # return authenticated user

        except TokenError:
            raise AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')
