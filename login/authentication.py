from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from datetime import datetime
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import CSRFCheck
from rest_framework import exceptions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from django.middleware import csrf

def enforce_csrf(get_response):
    def middleware(request):
        check = CSRFCheck()
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)
        return get_response(request)
    return middleware

class CustomAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        
        if header is None:
            raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE']) or None
        else:
            raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        enforce_csrf(request)
        return self.get_user(validated_token), validated_token
    
class ExpiredTokenAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            user_auth_tuple = super().authenticate(request)
            if user_auth_tuple is not None:
                user, auth = user_auth_tuple
                return user, auth
        except InvalidToken:
            pass

        # Token is invalid, try to refresh it
        refresh_token = request.COOKIES.get('refresh', None)
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                if token.access_token_expired():
                    raise TokenError('Access token expired')
                if token.access_token.needs_refresh:
                    token = token.refresh()
                    response = Response()
                    response.set_cookie(
                        key=settings.SIMPLE_JWT['AUTH_COOKIE'], 
                        value=str(token.access_token),
                        expires=datetime.now() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
                    )
                    csrf.get_token(request)
                    response.data = {"Success": "Token refreshed successfully"}
                    return None, response

                user = self.authenticate_credentials(token.access_token)
                return user, token

            except TokenError:
                pass

        return None, None
