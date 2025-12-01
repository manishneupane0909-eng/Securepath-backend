# api/auth.py - DEV ONLY: Accepts token 'root'
from ninja.security import HttpBearer
from django.conf import settings  # NEW: Import settings
import os

# Get the API token from environment variables or use a fallback
API_TOKEN = os.getenv('API_TOKEN', 'root')


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        if token == API_TOKEN:
            return token
        return None


auth_bearer = AuthBearer()


# NEW FUNCTION: For URLs that pass the token via query string (like Report Export)
def token_query_auth(request):
    """Checks for the token in the URL query parameter 'token'."""
    token = request.GET.get('token')

    # Use the token from environment variables for comparison
    expected_token = settings.API_TOKEN

    if token == expected_token:
        return token
    return None