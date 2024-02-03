from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, CSRFCheck

from django.conf import settings
import jwt
from ..models import User


class Authentication(BaseAuthentication):

    def authenticate(self, request):
        authorization_header = request.headers.get('Authorization')

        if not authorization_header:
            return None

        try:
            prefix = authorization_header.split(' ')[0]
            if prefix.lower() != 'jwt':
                raise exceptions.AuthenticationFailed('Token is not jwt')

            access_token = authorization_header.split(' ')[1]
            payload = jwt.decode(
                access_token, settings.SECRET_KEY, algorithms=['HS256']
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('access_token expired')
        except IndexError:
            raise exceptions.AuthenticationFailed('Token prefix missing')

        return self.authenticate_credentials(request, payload['user_id'])

    def authenticate_credentials(self, request, key):
        # user = User.objects.filter(id=key).first()
        #
        # if user is None:
        #     raise exceptions.AuthenticationFailed('User not found')
        #
        # if not user.is_active:
        #     raise exceptions.AuthenticationFailed('User is inactive')
        #
        # self.enforce_csrf(request)
        #return (user, None)
        return True

    def enforce_csrf(self, request):
        check = CSRFCheck()

        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied(f'CSRF Failed: {reason}')