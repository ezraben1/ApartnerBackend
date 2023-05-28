import json
import os
import time
import traceback
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from core.utils import download_and_upload_signed_contract
from .models import (
    ApartmentImage,
    Contract,
    CustomUser,
    Inquiry,
    InquiryReply,
    Room,
    RoomImage,
    Bill,
    Apartment,
    SuggestedContract,
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
    IsRoomRenter,
    IsSearcher,
)
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse
from django.http import FileResponse, HttpResponse, JsonResponse
from rest_framework import mixins, viewsets
from django.db.models import Q
import cloudinary
import requests
from rest_framework.parsers import MultiPartParser, FormParser
from hellosign_sdk import HSClient
import tempfile
from django.views.decorators.csrf import csrf_exempt
from dropbox_sign import ApiClient, ApiException, Configuration, apis, models
from rest_framework.views import APIView


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
            return (
                Apartment.objects.filter(owner=user)
                .select_related("owner")
                .prefetch_related("rooms", "bills", "images")
            )
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


class SignUpLoginViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = serializers.CustomUserSerializer
    permission_classes = [permissions.AllowAny]

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


class SignatureStatusView(APIView):
    def get(self, request, *args, **kwargs):
        signature_request_id = self.kwargs.get("signature_request_id")

        configuration = Configuration(
            username="c35b8f89b102910d72f6c05bf78097f62e8e9e2f28c164a587ba0ab331bca22d"
        )

        with ApiClient(configuration) as api_client:
            signature_request_api = apis.SignatureRequestApi(api_client)

            try:
                response = signature_request_api.signature_request_get(
                    signature_request_id
                )
                return Response(
                    {"status": response.signature_request.signatures[0].status_code},
                    status=status.HTTP_200_OK,
                )
            except ApiException as e:
                return Response(
                    {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


@csrf_exempt
def hellosign_webhook(request):
    try:
        if request.method != "POST":
            print("Not a POST request")
            return JsonResponse(
                {"error": "Only POST requests are allowed."}, status=405
            )

        print("Request body:", request.body)

        if "json" not in request.POST:
            print("json not found in the request")
            return JsonResponse({"error": "json not found in the request"}, status=400)

        event_str = request.POST["json"]
        print("Event String:", event_str)
        event = json.loads(event_str)

        event_type = event.get("event", {}).get("event_type")
        event_hash = event.get("event", {}).get("event_hash")

        print(f"Event Type: {event_type}, Event Hash: {event_hash}")

        if event_type == "callback_test":
            if event_hash is not None:
                print("Event Hash:", event_hash)
                return HttpResponse("Hello API Event Received.")
            else:
                print("No event_hash in the event")
                print("Event Payload:", event)
                return JsonResponse({"error": "No event_hash in the event"}, status=400)

        if event_type == "signature_request_all_signed":
            signature_request_id = event["signature_request"]["signature_request_id"]
            client = HSClient(
                api_key="c35b8f89b102910d72f6c05bf78097f62e8e9e2f28c164a587ba0ab331bca22d"
            )
            details = client.get_signature_request(signature_request_id)

            # Get the signed document URL
            signed_document_url = details.signature_request.files_url

            # Download the signed document
            response = requests.get(signed_document_url, stream=True)
            with open("signed_document.pdf", "wb") as f:
                f.write(response.content)

            # Upload the signed document to Cloudinary
            cloudinary.config(
                cloud_name="dnis06cto",
                api_key="419768594117284",
                api_secret="zexmum1c5fbT8-959jXEb1VQj2w",
            )
            upload_response = cloudinary.uploader.upload("signed_document.pdf")

            # Retrieve the related contract and update the file field with the new URL
            contract = Contract.objects.get(signature_request_id=signature_request_id)
            contract.file = upload_response["url"]
            contract.save()

            return HttpResponse("Hello API Event Received.")

        print(f"Unknown event type: {event_type}")
        return JsonResponse({"error": f"Unknown event type: {event_type}"}, status=400)

    except Exception as e:
        print(f"Exception in hellosign_webhook: {type(e).__name__} - {str(e)}")
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


def get_embedded_sign_url(signature_id):
    configuration = Configuration(
        username="c35b8f89b102910d72f6c05bf78097f62e8e9e2f28c164a587ba0ab331bca22d"
    )

    with ApiClient(configuration) as api_client:
        embedded_api = apis.EmbeddedApi(api_client)

        try:
            response = embedded_api.embedded_sign_url(signature_id)
            sign_url = response["embedded"]["sign_url"]
            client_id = "b0e3cae5b0eaa2ab368de095fe5ea46a"
            sign_url_with_client_id = f"{sign_url}&client_id={client_id}"

            return sign_url_with_client_id
        except ApiException as e:
            print("Exception when calling Dropbox Sign API: %s\n" % e)
            return None
        except Exception as e:
            print("Unexpected error occurred: ", e)
            raise


class ContractViewSet(ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = serializers.ContractSerializer
    permission_classes = [IsAuthenticated, IsApartmentOwner]
    parser_classes = (MultiPartParser, FormParser)
    client = HSClient(
        api_key="c35b8f89b102910d72f6c05bf78097f62e8e9e2f28c164a587ba0ab331bca22d"
    )

    @action(detail=True, methods=["post"], url_path="send-for-signing")
    def send_for_signing(self, request, *args, **kwargs):
        configuration = Configuration(
            username="c35b8f89b102910d72f6c05bf78097f62e8e9e2f28c164a587ba0ab331bca22d"
        )
        with ApiClient(configuration) as api_client:
            signature_request_api = apis.SignatureRequestApi(api_client)
            embedded_api = apis.EmbeddedApi(api_client)
            contract = self.get_object()

            user = self.request.user
            signer_email = user.email
            signer_name = user.first_name + " " + user.last_name

            signer = models.SubSignatureRequestSigner(
                email_address=signer_email,
                name=signer_name,
                order=0,
            )

            signing_options = models.SubSigningOptions(
                draw=True,
                type=True,
                upload=True,
                phone=True,
                default_type="draw",
            )

            response = requests.get(contract.file.url, stream=True)

            # Save the file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                temp_file_path = temp_file.name

            try:
                with open(temp_file_path, "rb") as f:
                    embedded_request = models.SignatureRequestCreateEmbeddedRequest(
                        client_id="b0e3cae5b0eaa2ab368de095fe5ea46a",
                        title="Sign Contract",
                        subject="The contract for your new apartment is ready for signature",
                        message="Please sign this contract to confirm your agreement",
                        signers=[signer],
                        files=[f],
                        signing_options=signing_options,
                        test_mode=True,
                    )

                    response = signature_request_api.signature_request_create_embedded(
                        embedded_request
                    )

                os.remove(temp_file_path)  # remove the temporary file after use
                print("response", response)

                if response.signature_request.signatures:
                    signature_id = response.signature_request.signatures[0].signature_id
                    contract.signature_request_id = (
                        response.signature_request.signature_request_id
                    )
                    contract.save()
                    print(
                        "contract signature_request_id:", contract.signature_request_id
                    )

                    # user.user_type = "renter"  # update user type to Renter
                    # user.save()

                    # room = Room.objects.get(contract=contract)
                    # room.renter = user  # Set the Room's renter to the new renter
                    # room.save()

                    sign_url = get_embedded_sign_url(signature_id)
                    return Response({"sign_url": sign_url})

                else:
                    print("No signatures in the response")
                    # handle the case when there are no signatures

            except ApiException as e:
                print("Exception when calling Dropbox Sign API: %s\n" % e)
                raise e
            except Exception as e:  # add this
                print("Unexpected error occurred: ", e)
                raise

    @action(detail=True, methods=["patch"], url_path="upload-signed-document")
    def upload_signed_document(self, request, *args, **kwargs):
        contract = self.get_object()

        for _ in range(12):  # try for roughly one minute
            uploaded_url = download_and_upload_signed_contract(
                contract.signature_request_id
            )

            if uploaded_url is not None:
                contract.file = uploaded_url
                contract.save()

                user = self.request.user
                user.user_type = "renter"  # update user type to Renter
                user.save()

                room = Room.objects.get(contract=contract)
                room.renter = user  # Set the Room's renter to the new renter
                room.save()

                return Response({"message": "Signed document uploaded successfully"})

            time.sleep(5)  # wait for 5 seconds before trying again

        return Response(
            {"error": "Failed to download and upload the signed document"}, status=400
        )

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

    @action(detail=True, methods=["delete"], url_path="delete-file")
    def delete_file(self, request, *args, **kwargs):
        contract = self.get_object()
        if contract.file:
            public_id = contract.file.public_id
            cloudinary.uploader.destroy(public_id, resource_type="raw")
            contract.file = None
            contract.save()
            return Response({"message": "File deleted successfully."})
        else:
            return Response({"message": "No file to delete."})


class SuggestedContractViewSet(viewsets.ModelViewSet):
    queryset = SuggestedContract.objects.all()
    serializer_class = serializers.SuggestedContractSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        contract_id = self.kwargs["contract_pk"]
        suggestion_id = self.kwargs["pk"]
        return queryset.filter(contract_id=contract_id, id=suggestion_id)

    def perform_create(self, serializer):
        contract_id = self.kwargs["pk"]
        contract = get_object_or_404(Contract, id=contract_id)
        serializer.save(contract=contract)

    @action(detail=True, methods=["post"])
    def accept(self, request, contract_pk=None, pk=None):
        suggestion = self.get_object()
        contract = suggestion.contract

        contract.rent_amount = suggestion.suggested_rent_amount
        contract.save()

        # Retrieve the room and apartment related to the contract
        room = contract.room
        apartment = room.apartment

        # Retrieve the sender CustomUser instance
        sender = room.apartment.owner

        # Create Inquiry instance
        receiver = suggestion.price_suggested_by
        message = f"The contract {contract.pk} has been accepted."
        type = "other"  # You may choose a more appropriate type

        inquiry = Inquiry.objects.create(
            sender=sender,
            receiver=receiver,
            apartment=apartment,
            message=message,
            type=type,
        )
        inquiry.save()

        suggestion.delete()

        return Response({"detail": "Suggestion accepted"})

    @action(detail=True, methods=["delete"])
    def decline(self, request, contract_pk=None, pk=None):
        suggestion = self.get_object()

        room = suggestion.contract.room
        apartment = room.apartment

        sender = room.apartment.owner

        receiver = suggestion.price_suggested_by
        message = f"The suggestion {suggestion.pk} has been declined."
        type = "other"

        inquiry = Inquiry.objects.create(
            sender=sender,
            receiver=receiver,
            apartment=apartment,
            message=message,
            type=type,
        )
        inquiry.save()

        suggestion.delete()

        return Response({"detail": "Suggestion declined"})


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

    @action(detail=True, methods=["delete"], url_path="delete-file")
    def delete_file(self, request, *args, **kwargs):
        bill = self.get_object()
        if bill.file:
            public_id = bill.file.public_id
            cloudinary.uploader.destroy(public_id, resource_type="raw")
            bill.file = None
            bill.save()
            return Response({"message": "File deleted successfully."})
        else:
            return Response({"message": "No file to delete."})


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


class SimpleInquiryViewst(viewsets.ReadOnlyModelViewSet):
    queryset = Inquiry.objects.all()

    serializer_class = serializers.SimpleInquirySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Inquiry.objects.filter(Q(sender=user) | Q(receiver=user))


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
        "apartment__city",
        "apartment__street",
        "apartment__building_number",
        "apartment__apartment_number",
        "sender__username",
        "receiver__username",
    ]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        user = self.request.user
        return self.queryset.select_related("sender", "receiver", "apartment").filter(
            Q(sender=user) | Q(receiver=user)
        )

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
        return InquiryReply.objects.select_related("inquiry", "sender").filter(
            inquiry__id=inquiry_id
        )

    def perform_create(self, serializer):
        inquiry_id = self.kwargs.get("pk")
        inquiry = Inquiry.objects.get(pk=inquiry_id)
        serializer.save(inquiry=inquiry, sender=self.request.user)


class DepositGuaranteeBillViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.DepositGuaranteeBillSerializer
    permission_classes = [permissions.IsAuthenticated, IsRoomRenter]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        user = self.request.user
        try:
            room = user.rooms_rented
            apartment = room.apartment
            return Bill.objects.filter(
                apartment=apartment, bill_type=Bill.DEPOSITS_GUARANTEES
            )
        except Room.DoesNotExist:
            return Bill.objects.none()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_object(self):
        pk = self.kwargs.get("pk")
        return get_object_or_404(Bill, pk=pk)

    def perform_create(self, serializer):
        user = self.request.user
        room = user.rooms_rented
        apartment = room.apartment
        serializer.save(
            apartment=apartment, bill_type=Bill.DEPOSITS_GUARANTEES, created_by=user
        )

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
