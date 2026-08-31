from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class ServiceUser:
    """
    A stand-in for django.contrib.auth's User, built entirely from JWT
    claims. This service doesn't own the Users table (auth-service does),
    so `request.user` here is never backed by a local DB row.
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
    never queries a local Users table for the token's subject — it
    reconstructs `request.user` purely from the token's claims.
    """

    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        if user_id is None:
            raise InvalidToken("Token contained no recognizable user identification")
        return ServiceUser(user_id=user_id, email=validated_token.get("email", ""))


class StatelessJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    Tells drf-spectacular how to document StatelessJWTAuthentication — without
    this, Swagger has no "Authorize" button because it only auto-detects the
    stock JWTAuthentication class, not this subclass. Paste the access token
    issued by auth-service's /api/auth/login/ here (no "Bearer " prefix needed
    in the Swagger dialog — it's added automatically).
    """

    target_class = "analytics.authentication.StatelessJWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
