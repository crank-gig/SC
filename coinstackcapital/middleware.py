# middleware.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.middleware import AuthenticationMiddleware

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'Authorization' in request.headers:
            jwt_authentication = JWTAuthentication()
            try:
                user, _ = jwt_authentication.authenticate(request)
                request.user = user
            except AuthenticationFailed:
                print("here I am")
                # Token is invalid or expired
                request.user = None
        else:
            # No Authorization header present, don't perform JWT authentication
            request.user = None

        response = self.get_response(request)
        return response


"""
class CustomAuthenticationMiddleware(AuthenticationMiddleware):
    def process_request(self, request):
        super().process_request(request)
        if not request.user.is_authenticated and 'Authorization' not in request.headers:
            # Handle session authentication here
            # For example:
            if 'session_key' in request.COOKIES:
                user = User.objects.get(session_key=request.COOKIES['session_key'])
                request.user = user
"""