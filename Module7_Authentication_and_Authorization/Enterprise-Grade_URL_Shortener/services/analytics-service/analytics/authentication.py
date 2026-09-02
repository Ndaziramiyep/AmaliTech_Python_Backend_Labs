from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class ServiceUser:
    """A stand-in for django.contrib.auth's User, built entirely from JWT claims."""

    def __init__(self, user_id, email="", is_staff=False, tier="Free"):
        """Populate identity fields from the decoded token's claims."""
        self.id = user_id
        self.pk = user_id
        self.email = email
        self.is_staff = is_staff
        self.tier = tier
        self.is_authenticated = True
        self.is_anonymous = False

    def __str__(self):
        """Return the user's email, falling back to their id."""
        return self.email or str(self.id)


class StatelessJWTAuthentication(JWTAuthentication):
    """Verifies JWTs like JWTAuthentication but reconstructs `request.user` purely from token claims, without a DB lookup."""

    def get_user(self, validated_token):
        """Build a ServiceUser from the validated token's claims instead of querying a Users table."""
        user_id = validated_token.get("user_id")
        if user_id is None:
            raise InvalidToken("Token contained no recognizable user identification")
        # simplejwt encodes user_id as a string claim; cast back to int so
        # equality/filter comparisons against owner_id (an IntegerField) work correctly.
        return ServiceUser(
            user_id=int(user_id),
            email=validated_token.get("email", ""),
            is_staff=validated_token.get("is_staff", False),
            tier=validated_token.get("tier", "Free"),
        )


class StatelessJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """Tells drf-spectacular how to document StatelessJWTAuthentication so Swagger gets an "Authorize" button."""

    target_class = "analytics.authentication.StatelessJWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        """Return the OpenAPI bearer-JWT security scheme definition."""
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
