from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class ServiceUser:
    """
    A stand-in for django.contrib.auth's User, built entirely from JWT
    """

    def __init__(self, user_id, email=""):
        self.id = user_id
        self.pk = user_id
        self.email = email
        self.is_authenticated = True
        self.is_anonymous = False

    def __str__(self):
        return self.email or str(self.id)


class StatelessJWTAuthentication(JWTAuthentication):
    """
    Verifies the JWT signature/expiry exactly like JWTAuthentication, but
    never queries a local Users table for the token's subject 
    """

    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        if user_id is None:
            raise InvalidToken("Token contained no recognizable user identification")
        return ServiceUser(user_id=user_id, email=validated_token.get("email", ""))


class StatelessJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    Tells drf-spectacular how to document StatelessJWTAuthentication 
    """

    target_class = "url_shortener.authentication.StatelessJWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
