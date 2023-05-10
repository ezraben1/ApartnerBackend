from django.urls import path
from rest_framework_nested import routers
from core.views import (
    ApartmentInquiryViewSet,
    ContractViewSet,
    CustomUserViewSet,
    ReviewViewSet,
    RoomViewSet,
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
        "searcher-search/<int:apartment_id>/room/<int:pk>/contracts/",
        RoomViewSet.as_view({"get": "contracts"}),
        name="room-contracts",
    ),
    path(
        "searcher-search/<int:apartment_id>/room/<int:pk>/sign-contract/",
        RoomViewSet.as_view({"post": "sign_contract"}),
        name="room-sign-contract",
    ),
    path(
        "searcher-search/<int:room_id>/contract/",
        SearcherContractViewSet.as_view({"get": "retrieve"}),
        name="contract",
    ),
    path(
        "searcher-search/<int:room_id>/contract/<int:pk>/",
        SearcherContractViewSet.as_view({"get": "retrieve"}),
        name="contract-detail",
    ),
    path(
        "searcher-search/<int:room_id>/contract/<int:pk>/download/",
        SearcherContractViewSet.as_view({"get": "download"}),
        name="contract-download",
    ),
] + router.urls
