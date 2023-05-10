from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from .models import (
    ApartmentImage,
    Contract,
    CustomUser,
    Inquiry,
    InquiryReply,
    Review,
    Room,
    RoomImage,
    Bill,
    Apartment,
)
from . import serializers
from rest_framework import permissions
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.filters import OrderingFilter, SearchFilter
from core.filters import RoomFilter
from core.pagination import DefaultPagination
from core.permissions import (
    IsApartmentOwner,
    IsAuthenticated,
    IsSearcher,
)
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings
import os
import mimetypes
from django.http import FileResponse
from rest_framework import mixins, viewsets
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist


class ApartmentImageViewSet(ModelViewSet):
    serializer_class = serializers.ApartmentImageSerializer
    queryset = ApartmentImage.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsApartmentOwner]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoomImageViewSet(ModelViewSet):
    serializer_class = serializers.RoomImageSerializer
    queryset = RoomImage.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsApartmentOwner]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApartmentViewSet(ModelViewSet):
    serializer_class = serializers.ApartmentSerializer
    queryset = Apartment.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "size",
        "balcony",
        "bbq_allowed",
        "smoking_allowed",
        "allowed_pets",
        "ac",
    ]
    search_fields = [
        "city",
        "street",
        "building_number",
        "apartment_number",
        "floor",
        "description",
        "size",
    ]
    ordering_fields = ["price", "size"]
    permission_classes_by_action = {
        "create": [permissions.IsAuthenticated, IsApartmentOwner],
        "update": [permissions.IsAuthenticated, IsApartmentOwner],
        "partial_update": [permissions.IsAuthenticated, IsApartmentOwner],
        "destroy": [permissions.IsAuthenticated, IsApartmentOwner],
        "contracts": [permissions.IsAuthenticated, IsApartmentOwner],
        "bills": [permissions.IsAuthenticated, IsApartmentOwner],
        "send_email": [permissions.IsAuthenticated, IsSearcher],
    }

    def get_permissions(self):
        try:
            return [
                permission()
                for permission in self.permission_classes_by_action[self.action]
            ]
        except KeyError:
            return [permission() for permission in self.permission_classes]

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

    @action(detail=True, methods=["post"])
    def send_email(self, request, pk=None):
        apartment = self.get_object()
        owner_email = apartment.owner.email
        subject = "Regarding Apartment %d" % apartment.id
        message = (
            "I am interested in the apartment. Please contact me at this email address: %s"
            % request.user.email
        )
        send_mail(
            subject, message, "from@example.com", [owner_email], fail_silently=False
        )
        return Response({"message": "Email sent"})

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.user_type == "owner":
            return Apartment.objects.filter(owner=user)
        else:
            return Apartment.objects.none()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PublicRoomViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.RoomSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RoomFilter
    pagination_class = DefaultPagination
    search_fields = [
        "apartment__city",
        "apartment__street",
        "apartment__building_number",
        "apartment__apartment_number",
        "apartment__floor",
        "size",
    ]
    ordering_fields = ["price_per_month"]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Room.objects.filter(renter=None)


class RoomViewSet(ModelViewSet):
    serializer_class = serializers.RoomSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RoomFilter
    pagination_class = DefaultPagination
    search_fields = [
        "apartment__city",
        "apartment__street",
        "apartment__building_number",
        "apartment__apartment_number",
        "apartment__floor",
        "size",
    ]
    ordering_fields = ["price_per_month"]

    def get_permissions(self):
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "create_contract",
            "update_contract",
            "delete_contract",
            "sign_contract",
            "contact_owner",
            "room_contracts",
        ]:
            permission_classes = [IsAuthenticated, IsApartmentOwner]
        elif (
            self.action == "sign_contract"
            or self.action == "contact_owner"
            or self.action == "room_contracts"
        ):
            permission_classes = [IsAuthenticated, IsSearcher]
        else:
            permission_classes = [IsAuthenticated, IsApartmentOwner]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.user_type == "owner":
                return Room.objects.filter(apartment__owner=self.request.user)
            elif user.user_type == "searcher":
                return Room.objects.prefetch_related("images").all()
        return Room.objects.prefetch_related("images").filter(is_available=True)

    @action(
        detail=True,
        url_path="contracts",
        permission_classes=[permissions.IsAuthenticated],
    )
    def room_contracts(self, request, pk=None):
        room = self.get_object()
        contracts = Contract.objects.filter(room=room)
        serializer = serializers.ContractSerializer(contracts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsApartmentOwner])
    def create_contract(self, request, pk=None):
        room = self.get_object()
        serializer = serializers.ContractSerializer(data=request.data)
        if serializer.is_valid():
            # create a new Contract object
            contract = serializer.save(room=room)

            # redirect the user to the contract detail endpoint
            return redirect(reverse("contract_detail", kwargs={"pk": contract.pk}))
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @create_contract.mapping.put
    def update_contract(self, request, *args, **kwargs):
        contract = get_object_or_404(Contract, pk=kwargs["pk"])
        self.check_object_permissions(request, contract)
        serializer = serializers.ContractSerializer(
            contract, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @create_contract.mapping.delete
    def delete_contract(self, request, *args, **kwargs):
        contract = get_object_or_404(Contract, pk=kwargs["pk"])
        self.check_object_permissions(request, contract)
        contract.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def sign_contract(self, request, pk=None):
        room = self.get_object()
        data = request.data.copy()
        data["room"] = room.pk
        data["tenant"] = request.user.pk
        serializer = serializers.ContractSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CustomUserViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = serializers.CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["patch"])
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if self.action == "patch":
                return CustomUser.objects.filter(id=user.id)
            return CustomUser.objects.filter(id=user.id)
        else:
            return CustomUser.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        if CustomUser.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # If the avatar field is included in the request, save the file and update the user model
        if "avatar" in request.FILES:
            instance.avatar = request.FILES["avatar"]
            instance.save()

        self.perform_update(serializer)
        return Response(serializer.data)


class ContractViewSet(ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = serializers.ContractSerializer
    permission_classes = [IsAuthenticated, IsApartmentOwner]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.user_type == "owner":
            # Filter apartments by owner
            apartments = Apartment.objects.filter(owner=user)
            # Filter rooms by apartments
            rooms = Room.objects.filter(apartment__in=apartments)
            # Filter contracts by rooms
            contracts = Contract.objects.filter(room__in=rooms)
            return contracts
        else:
            return Contract.objects.none()

    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type != "owner":
            return Response(
                {"error": "Only owners can create Contracts."},
                status=status.HTTP_403_FORBIDDEN,
            )
        room_id = self.kwargs["room_id"]
        room = get_object_or_404(Room, id=room_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contract = self.perform_create(serializer)
        room.contract = contract
        room.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        room_id = self.kwargs["room_id"]
        room = get_object_or_404(Room, id=room_id)
        return serializer.save(owner=self.request.user, room=room)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, *args, **kwargs):
        contract = self.get_object()
        if not contract.file:
            return Response(
                {"error": "No file available."}, status=status.HTTP_404_NOT_FOUND
            )

        file_path = contract.file.path
        if os.path.exists(file_path):
            response = FileResponse(
                open(file_path, "rb"), content_type="application/octet-stream"
            )
            response[
                "Content-Disposition"
            ] = f"attachment; filename={os.path.basename(file_path)}"
            return response
        else:
            return Response(
                {"error": "File not found."}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["delete"], url_path="delete-file")
    def delete_file(
        self, request, apartment_id=None, room_id=None, pk=None, *args, **kwargs
    ):
        contract = self.get_object()
        contract.file.delete()
        contract.save()
        return Response({"message": "File deleted successfully."})


class BillViewSet(ModelViewSet):
    serializer_class = serializers.BillSerializer
    permission_classes = [permissions.IsAuthenticated, IsApartmentOwner]

    def get_queryset(self):
        """
        Return bills for the current user's owned apartments.
        """
        user = self.request.user
        owned_apartments = user.apartments_owned.all()
        return Bill.objects.filter(apartment__in=list(owned_apartments))

    def perform_create(self, serializer):
        """
        Set the created_by field to the current user, and set the apartment owner to the current user.
        """
        user = self.request.user
        apartment = serializer.validated_data["apartment"]
        if apartment.owner != user:
            raise serializers.ValidationError(
                "You are not the owner of this apartment."
            )
        serializer.save(
            created_by=user,
            apartment=apartment,
        )

    def get_apartment(self):
        apartment_id = self.kwargs.get("apartment_id")
        apartment = get_object_or_404(
            Apartment, id=apartment_id, owner=self.request.user
        )
        return apartment

    @action(detail=True, methods=["get"])
    def download(self, request, apartment_id=None, bill_id=None):
        bill = get_object_or_404(Bill, id=bill_id, apartment_id=apartment_id)
        file_path = os.path.join(settings.MEDIA_ROOT, str(bill.file))
        if os.path.exists(file_path):
            content_type, encoding = mimetypes.guess_type(file_path)
            content_type = content_type or "application/octet-stream"
            with open(file_path, "rb") as fh:
                response = HttpResponse(fh.read(), content_type=content_type)
                response[
                    "Content-Disposition"
                ] = f"attachment; filename={os.path.basename(file_path)}"
                if encoding:
                    response["Content-Encoding"] = encoding
                return response
        return Response(
            {"message": "File not found."}, status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=True, methods=["delete"], url_path="delete-file")
    def delete_file(self, request, apartment_id=None, bill_id=None, *args, **kwargs):
        bill = self.get_object()
        bill.file.delete()
        bill.save()
        return Response({"message": "File deleted successfully."})


class ReviewViewSet(ModelViewSet):
    serializer_class = serializers.ReviewSerializer

    def get_queryset(self):
        if "room_pk" in self.kwargs:
            return Review.objects.filter(room_id=self.kwargs["room_pk"])
        else:
            return Review.objects.all()

    def get_serializer_context(self):
        if "room_pk" in self.kwargs:
            return {"room_id": self.kwargs["room_pk"]}
        else:
            return {}


class ApartmentInquiryViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = Inquiry.objects.all()
    serializer_class = serializers.InquirySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs.get("pk", None)
        is_room = self.request.query_params.get("is_room", "false").lower() == "true"
        apartment = self.get_user_apartment(user, pk, is_room)
        if apartment:
            return self.queryset.filter(
                Q(apartment=apartment) & (Q(sender=user) | Q(receiver=user))
            )
        elif is_room:
            return self.queryset.filter(room__renter=user)
        else:
            return Inquiry.objects.none()

    def perform_create(self, serializer):
        is_room = self.request.query_params.get("is_room", "false").lower() == "true"
        pk = self.kwargs.get("pk", None)
        apartment = self.get_user_apartment(self.request.user, pk, is_room)

        if not apartment:
            print("Apartment not found for the user")
            return Response({"detail": "Apartment not found for the user."}, status=404)

        receiver = apartment.owner

        if serializer.is_valid():
            print("Serializer is valid")
            inquiry = serializer.save(
                apartment=apartment, sender=self.request.user, receiver=receiver
            )
            print("Inquiry created:", inquiry)
            # Return a successful response with the created Inquiry data
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("Serializer is invalid:", serializer.errors)

        return Response(serializer.errors, status=400)

    def get_user_apartment(self, user, pk=None, is_room=False):
        if pk:
            if is_room:
                room = Room.objects.filter(pk=pk).first()
                return room.apartment if room else None
            else:
                return Apartment.objects.filter(pk=pk).first()
        else:
            room = Room.objects.filter(renter=user).first()
            return room.apartment if room else None


class UserInquiryViewSet(viewsets.ModelViewSet):
    queryset = Inquiry.objects.all()
    serializer_class = serializers.InquirySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    pagination_class = DefaultPagination

    filterset_fields = [
        "status",
        "type",
        "apartment",
        "sender",
        "receiver",
    ]
    search_fields = [
        "message",
        "apartment__city",  # Example of how to use search_fields with a ForeignKey field
        "apartment__street",
        "apartment__building_number",
        "apartment__apartment_number",
        "sender__username",  # Example of how to use search_fields with a related model
        "receiver__username",
    ]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(Q(sender=user) | Q(receiver=user))

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        inquiry = self.get_object()

        if request.user.user_type != "owner":
            return Response(
                {"detail": "Only owner users can close inquiries."}, status=403
            )

        inquiry.status = Inquiry.InquiryStatus.CLOSED
        inquiry.save()
        serializer = self.get_serializer(inquiry)
        return Response(serializer.data)


class InquiryReplyViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = InquiryReply.objects.all()
    serializer_class = serializers.InquiryReplySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        inquiry_id = self.kwargs.get("pk")
        return InquiryReply.objects.filter(inquiry__id=inquiry_id)

    def perform_create(self, serializer):
        inquiry_id = self.kwargs.get("pk")
        inquiry = Inquiry.objects.get(pk=inquiry_id)
        serializer.save(inquiry=inquiry, sender=self.request.user)
