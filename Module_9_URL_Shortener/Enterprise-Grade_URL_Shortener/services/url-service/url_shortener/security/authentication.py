from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class ServiceUser:
    """A stand-in for django.contrib.auth's User, built entirely from JWT claims rather than a local DB row."""

    def __init__(self, user_id, email="", is_staff=False, tier="Free"):
        """Store the JWT's user id, email, is_staff, and tier claims as attributes mimicking a Django User."""
        self.id = user_id
        self.pk = user_id
        self.email = email
        self.is_staff = is_staff
        self.tier = tier
        self.is_authenticated = True
        self.is_anonymous = False

    def __str__(self):
        """Return the user's email, or their id if no email is set."""
        return self.email or str(self.id)


class StatelessJWTAuthentication(JWTAuthentication):
    """Verifies a JWT like JWTAuthentication but reconstructs request.user purely from its claims."""

    def get_user(self, validated_token):
        """Build a ServiceUser from the validated token's claims without querying a local Users table."""
        user_id = validated_token.get("user_id")
        if user_id is None:
            raise InvalidToken("Token contained no recognizable user identification")
        return ServiceUser(
            # simplejwt encodes user_id as a string claim; cast back to int so
            # equality checks against owner_id (an IntegerField) work correctly.
            user_id=int(user_id),
            email=validated_token.get("email", ""),
            is_staff=validated_token.get("is_staff", False),
            tier=validated_token.get("tier", "Free"),
        )


class StatelessJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """Tells drf-spectacular how to document StatelessJWTAuthentication so Swagger gets an Authorize button."""

    target_class = "url_shortener.security.authentication.StatelessJWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        """Return the OpenAPI security scheme describing this service's bearer JWT authentication."""
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
