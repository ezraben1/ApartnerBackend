import os
from django.http import FileResponse, Http404
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import permissions
from core import serializers
from core.filters import RoomFilter
from core.models import Contract, Room
from rest_framework import viewsets, permissions
from django.db.models import Q
from core.pagination import DefaultPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import status
from core.permissions import IsAuthenticated, IsSearcher

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
        if query:
            queryset = Room.objects.filter(
                Q(apartment__city__icontains=query)
                | Q(apartment__street__icontains=query)
                | Q(apartment__building_number__icontains=query)
                | Q(apartment__apartment_number__icontains=query)
                | Q(apartment__floor__icontains=query)
                | Q(size__icontains=query),
                renter=None,
            )
        else:
            queryset = Room.objects.filter(renter=None)
        return queryset


class SearcherContractViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.ContractSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.user_type == "searcher":
            try:
                room_id = self.kwargs["room_id"]
                contract_id = self.kwargs["pk"]
                contract = Contract.objects.select_related("room__apartment").get(
                    id=contract_id,
                    room__id=room_id,
                )
            except Contract.DoesNotExist:
                raise Http404
            return Contract.objects.filter(id=contract.id)
        else:
            return Contract.objects.none()

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, *args, **kwargs):
        contract = self.get_object()
        if not contract.file:
            return Response(
                {"error": "No file available."},
                status=status.HTTP_404_NOT_FOUND,
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
                {"error": "File not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
