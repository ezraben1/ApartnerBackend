from django.urls import path
from rest_framework_nested import routers
from core.views import (
    ApartmentInquiryViewSet,
    CustomUserViewSet,
    ReviewViewSet,
)
from renter.views import (
    RenterApartmentViewSet,
    RenterBillViewSet,
    RenterContractViewSet,
    RenterRoomViewSet,
)

app_name = "renter"


router = routers.DefaultRouter()
router.register("me", CustomUserViewSet, basename="me")
router.register("my-room", RenterRoomViewSet, basename="my-room")
router.register("my-apartment", RenterApartmentViewSet, basename="my-aprtment")
router.register("my-bills", RenterBillViewSet, basename="my-bills")


urlpatterns = [
    path(
        "my-apartment/inquiries/",
        ApartmentInquiryViewSet.as_view({"get": "list", "post": "create"}),
        name="renter-inquiries",
    ),
    path(
        "my-room/<int:room_id>/contracts/<int:pk>/",
        RenterContractViewSet.as_view({"get": "retrieve"}),
        name="contract_detail",
    ),
    path(
        "my-room/<int:room_id>/bills/",
        RenterRoomViewSet.as_view({"get": "get_bills"}),
        name="room-bills",
    ),
    path(
        "renter-search/<int:room_id>/review/<int:pk>/",
        ReviewViewSet.as_view({"get": "retrieve"}),
        name="review-detail",
    ),
    path(
        "my-bills/<int:bill_id>/download/",
        RenterBillViewSet.as_view({"get": "download"}),
        name="bill-download-file",
    ),
    path(
        "my-room/<int:room_id>/contracts/<int:pk>/download/",
        RenterContractViewSet.as_view({"get": "download"}),
        name="contract-download-file",
    ),
] + router.urls
