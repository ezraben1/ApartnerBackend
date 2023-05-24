from django.urls import path
from rest_framework_nested import routers
from core.views import (
    ApartmentInquiryViewSet,
    CustomUserViewSet,
    ReviewViewSet,
    RoomViewSet,
    SignatureStatusView,
    SuggestedContractViewSet,
)
from searcher.views import SearcherContractViewSet, SearcherRoomViewSet

app_name = "searcher"


router = routers.DefaultRouter()
router.register("searcher-search", SearcherRoomViewSet, basename="search")
router.register("me", CustomUserViewSet, basename="me")

rooms_router = routers.NestedSimpleRouter(router, "searcher-search", lookup="pk")
rooms_router.register("reviews", ReviewViewSet, basename="room-reviews")


urlpatterns = [
    path(
        "searcher-search/<int:pk>/inquiries/",
        ApartmentInquiryViewSet.as_view({"get": "list", "post": "create"}),
        name="searcher-inquiries",
    ),
    path(
        "searcher-search/<int:room_id>/contract/",
        SearcherContractViewSet.as_view({"get": "list"}),
        name="contract-list",
    ),
    path(
        "searcher-search/<int:room_id>/contract/<int:pk>/",
        SearcherContractViewSet.as_view({"get": "retrieve", "patch": "update"}),
        name="contract-detail",
    ),
    path(
        "searcher-search/<int:room_id>/contract/<int:pk>/send-for-signing",
        SearcherContractViewSet.as_view({"post": "send_for_signing"}),
        name="contract-sign",
    ),
    path(
        "searcher-search/<int:room_id>/contract/<int:pk>/upload-signed-document",
        SearcherContractViewSet.as_view({"patch": "upload_signed_document"}),
        name="upload-signed-document",
    ),
    path(
        "searcher-search/<int:room_id>/contract/<int:pk>/suggestedcontracts",
        SuggestedContractViewSet.as_view({"get": "list", "post": "create"}),
        name="suggestedcontracts",
    ),
    path(
        "searcher-search/<int:room_id>/contract/<int:pk>/signature-status/<str:signature_request_id>/",
        SignatureStatusView.as_view(),
        name="signature-status",
    ),
    path(
        "searcher-search/<int:room_id>/contract/<int:pk>/download/",
        SearcherContractViewSet.as_view({"get": "download"}),
        name="contract-download",
    ),
] + router.urls
