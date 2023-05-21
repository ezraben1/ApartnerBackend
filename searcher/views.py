from django.http import Http404
from rest_framework import permissions
from core import serializers
from core.filters import RoomFilter
from core.models import Contract, Room
from rest_framework import viewsets, permissions
from django.db.models import Q
from core.pagination import DefaultPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from core.permissions import IsAuthenticated
from core.views import ContractViewSet

from searcher.serializers import SearcherRoomSerializer


from django.db.models import Q


class SearcherRoomViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SearcherRoomSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RoomFilter
    pagination_class = DefaultPagination
    search_fields = [
        "apartment__city",
        "apartment__street",
        "apartment__building_number",
        "apartment__apartment_number",
        "apartment__floor",
    ]

    ordering_fields = ["price_per_month"]

    def get_queryset(self):
        query = self.request.query_params.get("search")
        queryset = Room.objects.filter(renter=None)
        if query:
            queryset = queryset.filter(
                Q(apartment__city__icontains=query)
                | Q(apartment__street__icontains=query)
                | Q(apartment__building_number__icontains=query)
                | Q(apartment__apartment_number__icontains=query)
                | Q(apartment__floor__icontains=query)
                | Q(size__icontains=query)
            )
        queryset = queryset.select_related("apartment").prefetch_related("images")
        return queryset


class SearcherContractViewSet(ContractViewSet):
    serializer_class = serializers.ContractSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.user_type == "searcher":
            try:
                room_id = self.kwargs.get("room_id")
                contract_id = self.kwargs.get("pk")
                if contract_id is not None:
                    contract = Contract.objects.select_related("room__apartment").get(
                        id=contract_id,
                        room__id=room_id,
                    )
                    return Contract.objects.filter(id=contract.id)
                else:
                    return Contract.objects.filter(room__id=room_id)
            except Contract.DoesNotExist:
                raise Http404
        else:
            return Contract.objects.none()
