from core.models import Apartment, Room
from core.serializers import (
    ApartmentImageSerializer,
    RoomSerializer,
)
from rest_framework import serializers


class SearcherApartmentSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.email")
    images = ApartmentImageSerializer(many=True, read_only=True)

    def get_bill_ids(self, obj):
        bills = obj.bills.only("id")
        return [bill.id for bill in bills]

    class Meta:
        model = Apartment
        fields = [
            "id",
            "owner",
            "address",
            "city",
            "street",
            "building_number",
            "apartment_number",
            "floor",
            "description",
            "size",
            "balcony",
            "bbq_allowed",
            "smoking_allowed",
            "allowed_pets",
            "ac",
            "images",
        ]


class SearcherRoomSerializer(RoomSerializer):
    apartment = SearcherApartmentSerializer(read_only=True)

    class Meta:
        model = Room
        fields = [
            "id",
            "description",
            "size",
            "price_per_month",
            "window",
            "apartment_id",
            "contract",
            "renter",
            "images",
            "apartment",
            "renter_search",
            "images",
        ]
