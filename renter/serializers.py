from rest_framework import serializers

from core.models import Apartment
from core.serializers import ApartmentImageSerializer


class RenterApartmentSerializer(serializers.ModelSerializer):
    images = ApartmentImageSerializer(many=True, read_only=True)
    owner_email = serializers.ReadOnlyField(source="owner.email")
    owner_first_name = serializers.ReadOnlyField(source="owner.first_name")
    owner_last_name = serializers.ReadOnlyField(source="owner.last_name")
    owner_phone = serializers.ReadOnlyField(source="owner.phone")
    owner_id = serializers.ReadOnlyField(source="owner.id")

    class Meta:
        model = Apartment
        fields = [
            "id",
            "owner",
            "owner_email",
            "owner_first_name",
            "owner_last_name",
            "owner_phone",
            "owner_id",
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
            "rooms",
            "images",
        ]
