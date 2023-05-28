import os
from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from core.permissions import IsAuthenticated, IsRoomRenter
from rest_framework import permissions
from rest_framework.response import Response
from core.serializers import (
    BillSerializer,
    ContractSerializer,
    RoomSerializer,
)
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from core.models import Apartment, Bill, Contract, Room
from core.serializers import ApartmentSerializer
from rest_framework.response import Response
from core.serializers import RoomSerializer
from rest_framework.decorators import action
from rest_framework import permissions, status
from django.core.mail import send_mail

from renter.serializers import RenterApartmentSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
import requests


class RenterApartmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RenterApartmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsRoomRenter]

    def get_apartment(self):
        user = self.request.user
        room = Room.objects.filter(renter=user).first()
        apartment = room.apartment if room else None
        return apartment

    def get_queryset(self):
        return Apartment.objects.none()

    def list(self, request, *args, **kwargs):
        apartment = self.get_apartment()
        if apartment:
            serializer = self.get_serializer(apartment)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class RenterRoomViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated, IsRoomRenter]

    def get_queryset(self):
        return Room.objects.filter(renter=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().first()
        if not queryset:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


class RenterBillViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated, IsRoomRenter]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        user = self.request.user
        try:
            room = user.rooms_rented
            apartment = room.apartment
            return Bill.objects.filter(apartment=apartment)
        except Room.DoesNotExist:
            return Bill.objects.none()

    @action(detail=True, methods=["post", "patch"])
    def pay(self, request, pk=None):
        bill = self.get_object()
        if not bill.paid:
            bill.paid = True
            bill.save()
            return Response({"status": "success"})
        return Response(
            {"status": "error", "message": "This bill has already been paid."}
        )

    @action(
        detail=False, methods=["get"], url_path=r"my-bills/(?P<bill_id>\d+)/download"
    )
    @action(detail=True, methods=["get"])
    def download(self, request, apartment_id=None, bill_id=None, *args, **kwargs):
        bill = self.get_object()
        if not bill.file:
            return Response(
                {"error": "No file available."}, status=status.HTTP_404_NOT_FOUND
            )
        file_url = bill.file.url
        if not file_url.endswith(".pdf"):
            file_url += ".pdf"

        try:
            file_response = FileResponse(requests.get(file_url, stream=True))
            file_response["Content-Disposition"] = 'attachment; filename="bill.pdf"'
            return file_response
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": "Failed to download the file."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RenterContractViewSet(viewsets.ModelViewSet):
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, IsRoomRenter]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.user_type == "renter":
            room_id = self.kwargs["room_id"]
            contract_id = self.kwargs["pk"]
            try:
                contract = Contract.objects.select_related("room__apartment").get(
                    id=contract_id, room__id=room_id, room__renter=user
                )
            except Contract.DoesNotExist:
                raise Http404
            return Contract.objects.filter(id=contract.id)
        else:
            return Contract.objects.none()

    @action(detail=True, methods=["get"])
    def download(self, request, *args, **kwargs):
        contract = self.get_object()
        if not contract.file:
            return Response(
                {"error": "No file available."}, status=status.HTTP_404_NOT_FOUND
            )
        file_url = contract.file.url
        if not file_url.endswith(".pdf"):
            file_url += ".pdf"

        try:
            file_response = FileResponse(requests.get(file_url, stream=True))
            file_response["Content-Disposition"] = 'attachment; filename="contract.pdf"'
            return file_response
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": "Failed to download the file."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
