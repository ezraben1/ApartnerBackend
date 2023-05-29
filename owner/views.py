from core import serializers
from core.models import Apartment, ApartmentImage, Bill, Contract, Room, RoomImage
from core.permissions import IsApartmentOwner
from rest_framework import permissions, status, viewsets
from core.views import ApartmentViewSet, RoomViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from cloudinary.uploader import upload
from owner.serializers import OwnerContractSuggestionSerializer


class OwnerApartmentViewSet(ApartmentViewSet):
    serializer_class = serializers.ApartmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsApartmentOwner]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.user_type == "owner":
            return (
                Apartment.objects.filter(owner=user)
                .select_related("owner")
                .prefetch_related("rooms", "bills", "images")
            )
        else:
            return Apartment.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            apartment = serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update_apartment(self, request, apartment):
        data = request.data
        serializer = self.get_serializer(apartment, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    def update_apartment_details(self, request, pk=None):
        apartment = self.get_object()
        return self.update_apartment(request, apartment)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(
        detail=True, methods=["patch"], parser_classes=[FormParser, MultiPartParser]
    )
    def upload_image(self, request, pk=None):
        apartment = self.get_object()

        if "images" in request.FILES:
            for img in request.FILES.getlist("images"):
                upload_result = upload(img)
                image_url = upload_result["url"]

                ApartmentImage.objects.create(apartment=apartment, image=image_url)

        return Response(
            {"detail": "Images uploaded successfully."}, status=status.HTTP_201_CREATED
        )

    @action(detail=True)
    def contracts(self, request, pk=None):
        apartment = self.get_object()
        contracts = Contract.objects.filter(room__apartment=apartment)
        serializer = serializers.ContractSerializer(contracts, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def bills(self, request, pk=None):
        apartment = self.get_object()
        bills = Bill.objects.filter(apartment=apartment)
        serializer = serializers.BillSerializer(bills, many=True)
        return Response(serializer.data)


class OwnerRoomViewSet(RoomViewSet):
    parser_classes = (MultiPartParser,)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.user_type == "owner":
            return Room.objects.select_related("apartment").filter(
                apartment__owner=self.request.user
            )

    @action(
        detail=True, methods=["patch"], parser_classes=[FormParser, MultiPartParser]
    )
    def upload_image(self, request, pk=None):
        room = self.get_object()

        if "images" in request.FILES:
            for img in request.FILES.getlist("images"):
                upload_result = upload(img)
                image_url = upload_result["url"]

                RoomImage.objects.create(room=room, image=image_url)

        return Response(
            {"detail": "Images uploaded successfully."}, status=status.HTTP_201_CREATED
        )

    def create(self, request, *args, **kwargs):
        apartment_id = self.kwargs.get("apartment_id")
        mutable_data = request.data.copy()
        mutable_data["apartment_id"] = apartment_id
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class OwnerContractSuggestionViewSet(viewsets.ModelViewSet):
    serializer_class = OwnerContractSuggestionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.user_type == "owner":
            return Contract.objects.filter(owner=user)
        else:
            return Contract.objects.none()
