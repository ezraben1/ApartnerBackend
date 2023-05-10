import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.functional import SimpleLazyObject
from django.contrib.auth.middleware import get_user

User = get_user_model()

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        access_token = request.COOKIES.get('access_token')

        if access_token:
            try:
                payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')
                request.user = User.objects.get(pk=user_id)
            except jwt.ExpiredSignatureError:
                pass
            except (jwt.exceptions.DecodeError, User.DoesNotExist):
                pass

        response = self.get_response(request)
        response['Authorization'] = f'Bearer {access_token}'

        return response
