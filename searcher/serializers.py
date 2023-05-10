from core.models import Room
from core.serializers import ApartmentSerializer, RoomSerializer


class SearcherRoomSerializer(RoomSerializer):
    apartment = ApartmentSerializer()

    class Meta:
        model = Room
        fields = [
            "id",
            "description",
            "size",
            "price_per_month",
            "window",
            "images",
            "apartment_id",
            "contract",
            "renter",
            "apartment",
            "images",
            "renter_search",
        ]
