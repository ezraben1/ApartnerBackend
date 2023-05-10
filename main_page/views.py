from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from rest_framework import viewsets
from login.authentication import ExpiredTokenAuthentication
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.conf import settings
from django.middleware import csrf
from rest_framework import status


def index(request):
    return JsonResponse(
        {
            "core": "http://127.0.0.1:8000/core/",
            "owner": "http://127.0.0.1:8000/owner/",
        }
    )
