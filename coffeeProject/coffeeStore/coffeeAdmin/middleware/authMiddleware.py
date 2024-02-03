
from ..models import User
from django.urls import reverse
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from django.http import HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.conf import settings
import jwt

class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        if '/login/' != request.path and '/join/' != request.path and '/user-join' != request.path and '/user-login' != request.path and '/user-logout' != request.path:

            if not (request.COOKIES.get('token')):
                return HttpResponseNotAllowed(['GET'])

            authorization = request.COOKIES.get('token')

            try:
                prefix = authorization.split(' ')[0]
                if prefix.lower() != 'jwt':
                    raise exceptions.AuthenticationFailed('Token is not jwt')

                token = authorization.split(' ')[1]
                payload = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=['HS256']
                )
            except jwt.ExpiredSignatureError:
                raise exceptions.AuthenticationFailed('access_token expired')
            except IndexError:
                raise exceptions.AuthenticationFailed('Token prefix missing')

            if payload['phone'] is not None:
                if self.authenticate_credentials(request, payload['phone']):
                    return self.get_response(request)
        else:
            return self.get_response(request)

    def authenticate_credentials(self, request, key):
        user = User(key, '')

        if user.isUser() is None:
            raise exceptions.AuthenticationFailed('User not found')

        self.enforce_csrf(request)

        return (user, None)

    def enforce_csrf(self, request):
        check = CSRFCheck()

        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied(f'CSRF Failed: {reason}')
