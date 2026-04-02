"""
Custom DRF authentication — verifica Supabase JWT tokens.
"""

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class SupabaseUser:
    """Lightweight user object built from Supabase JWT claims."""

    def __init__(self, payload: dict):
        self.id = payload.get("sub")
        self.email = payload.get("email", "")
        self.role = payload.get("user_metadata", {}).get("role", "usuario")
        self.is_authenticated = True

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def __str__(self) -> str:
        return self.email


class SupabaseAuthentication(BaseAuthentication):
    """
    Reads a Bearer token from the Authorization header, decodes it with
    the Supabase JWT secret, and returns a SupabaseUser.
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split("Bearer ", 1)[1]

        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token expirado.")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Token invalido.")

        return (SupabaseUser(payload), token)
