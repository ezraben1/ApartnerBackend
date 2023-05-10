from django.urls import path
from rest_framework_nested import routers
from . import views
from core.views import (
    ApartmentImageViewSet,
    ContractViewSet,
    BillViewSet,
    RoomImageViewSet,
    RoomViewSet,
)

app_name = "owner"

router = routers.DefaultRouter()
router.register("owner-apartments", views.OwnerApartmentViewSet, basename="apartments")
router.register("owner-rooms", views.OwnerRoomViewSet, basename="rooms")
router.register("owner-contarcts", ContractViewSet, basename="contracts")
router.register("owner-bills", BillViewSet, basename="bills")


urlpatterns = [
    path(
        "owner-apartments/<int:pk>/upload_image/",
        views.OwnerApartmentViewSet.as_view({"patch": "upload_image"}),
        name="apartment-upload-image",
    ),
    path(
        "owner-apartments/<int:apartment_id>/rooms/",
        views.OwnerRoomViewSet.as_view(
            {
                "get": "list",
                "put": "update",
                "delete": "destroy",
                "post": "create",
                "patch": "partial_update",
            }
        ),
        name="rooms",
    ),
    path(
        "owner-apartments/<int:apartment_id>/rooms/",
        views.OwnerRoomViewSet.as_view(
            {
                "get": "list",
                "put": "update",
                "delete": "destroy",
                "post": "create",
                "patch": "partial_update",
            }
        ),
        name="owner-room-detail",
    ),
    path(
        "owner-apartments/<int:apartment_id>/room/<int:pk>/",
        RoomViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "delete": "destroy",
                "post": "create_contract",
                "patch": "partial_update",
            }
        ),
        name="room-detail",
    ),
    path(
        "owner-apartments/<int:apartment_id>/contracts/<int:pk>/",
        ContractViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
                "post": "create",
            }
        ),
        name="contract_detail",
    ),
    path(
        "owner-apartments/<int:apartment_id>/room/<int:room_id>/contracts/",
        ContractViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="contracts",
    ),
    path(
        "owner-apartments/<int:apartment_id>/room/<int:room_id>/contracts/<int:pk>/",
        ContractViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
                "post": "create",
            }
        ),
        name="contract_detail",
    ),
    path(
        "owner-apartments/<int:apartment_id>/bills/<int:pk>/",
        BillViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
                "post": "create",
            }
        ),
        name="bill_detail",
    ),
    path(
        "owner-apartments/<int:apartment_id>/bills/<int:pk>/upload_file/",
        BillViewSet.as_view(
            {
                "patch": "upload_file",
                "post": "upload_fle",
            }
        ),
        name="bill-upload-file",
    ),
    path(
        "owner-apartments/<int:apartment_id>/bills/<int:bill_id>/download/",
        BillViewSet.as_view({"get": "download"}),
        name="bill-download-file",
    ),
    path(
        "owner-rooms/<int:room_id>/contracts/<int:pk>/",
        ContractViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
                "post": "create",
            }
        ),
        name="contract_detail",
    ),
    path(
        "owner-rooms/<int:pk>/create_contract/",
        ContractViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
                "post": "create",
            }
        ),
        name="create_contract",
    ),
    path(
        "owner-apartments/<int:apartment_id>/bills/<int:pk>/delete-file/",
        BillViewSet.as_view({"delete": "delete_file"}),
        name="delete_bill_file",
    ),
    path(
        "owner-apartments/<int:apartment_id>/room/<int:room_id>/contracts/<int:pk>/delete-file/",
        ContractViewSet.as_view({"delete": "delete_file"}),
        name="delete_contract_file",
    ),
    path(
        "owner-apartments/<int:apartment_id>/images/",
        ApartmentImageViewSet.as_view({"get": "list"}),
        name="apartment_image_list",
    ),
    path(
        "owner-apartments/<int:apartment_id>/images/<int:pk>/",
        ApartmentImageViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="apartment_image_detail",
    ),
    path(
        "owner-rooms/<int:room_id>/images/",
        RoomImageViewSet.as_view({"get": "list"}),
        name="room_image_list",
    ),
    path(
        "owner-rooms/<int:room_id>/images/<int:pk>/",
        RoomImageViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="room_image_detail",
    ),
] + router.urls
