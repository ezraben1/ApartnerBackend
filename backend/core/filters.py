from django_filters.rest_framework import FilterSet
from .models import Room
import django_filters


class RoomFilter(FilterSet):
    balcony = django_filters.BooleanFilter(field_name="apartment__balcony")
    bbq_allowed = django_filters.BooleanFilter(field_name="apartment__bbq_allowed")
    smoking_allowed = django_filters.BooleanFilter(
        field_name="apartment__smoking_allowed"
    )
    allowed_pets = django_filters.BooleanFilter(field_name="apartment__allowed_pets")
    ac = django_filters.BooleanFilter(field_name="apartment__ac")

    class Meta:
        model = Room
        fields = {"price_per_month": ["gt", "lt"]}
