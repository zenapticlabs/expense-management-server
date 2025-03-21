from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings

from users.models import User


class HasResetClaim(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        try:
            # Authenticate the user and get the validated token
            auth_header = request.headers.get('Authorization', '').split()
            if len(auth_header) != 2 or auth_header[0].lower() != 'bearer':
                return False

            token = auth_header[1]

            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            if validated_token['scope'] != 'password_reset':
                return False
            
            request.user_id_from_token = validated_token['uid']
            
            return True
        except InvalidToken:
            return False

class PasswordResetRequestAuthentication(BaseAuthentication):
    """Authenticates users for both password reset request and confirmation"""

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            print("TOKEN EXPIRED")
            # raise AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError:
            print("INVALID TOKEN")
            # raise AuthenticationFailed("Invalid token.")

        scope = decoded_token.get("scope")

        if scope == "password_reset_request":
            email = decoded_token.get("email")
            if not email:
                raise AuthenticationFailed("Invalid token payload: missing email.")

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise AuthenticationFailed("User not found.")

        elif scope == "password_reset":
            user_id = decoded_token.get("user_id")
            if not user_id:
                raise AuthenticationFailed("Invalid token payload: missing user ID.")

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise AuthenticationFailed("User not found.")

        else:
            raise AuthenticationFailed("Invalid token scope.")
        request.user = user
        return (user, None)
