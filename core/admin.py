from urllib.parse import urlencode
from django.contrib import admin
from django.db.models.aggregates import Count
from django.utils.html import format_html
from django.urls import reverse
from . import models
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from .models import Bill, Inquiry, InquiryReply


@admin.register(models.Room)
class RoomAdmin(admin.ModelAdmin):
    autocomplete_fields = ["apartment"]
    list_display = [
        "id",
        "apartment_address",
        "size",
        "price_per_month",
        "renter",
        "apartment",
    ]
    list_editable = ["price_per_month", "apartment", "renter"]
    list_filter = ["apartment"]
    list_per_page = 10
    list_select_related = ["apartment"]
    search_fields = [
        "size",
        "apartment__address",
        "apartment__city",
        "apartment__street",
        "apartment__building_number",
        "apartment__apartment_number",
        "apartment__floor",
    ]

    def apartment_address(self, room):
        return room.apartment.address

    class Media:
        css = {"all": ["core/styles.css"]}


@admin.register(models.Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ["id", "address", "rooms_count", "owner"]
    search_fields = [
        "address",
        "city",
        "street",
        "building_number",
        "apartment_number",
        "floor",
    ]

    @admin.display(ordering="rooms_count")
    def rooms_count(self, apartment):
        url = (
            reverse("admin:core_room_changelist")
            + "?"
            + urlencode({"apartment__id": str(apartment.id)})
        )
        return format_html('<a href="{}">{} Rooms</a>', url, apartment.rooms_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(rooms_count=Count("rooms"))

    def save_model(self, request, obj, form, change):
        if not obj.owner:
            if request.user.user_type != "owner":
                raise PermissionDenied("Only owners can create apartments.")
            obj.owner = request.user
        obj.save()


class CustomUserAdmin(UserAdmin):
    model = models.CustomUser
    list_display = ("id", "username", "email", "user_type", "is_staff", "first_name")
    list_filter = ("user_type",)
    list_editable = ["user_type"]

    ordering = ["first_name", "last_name"]
    list_per_page = 10
    search_fields = ["first_name__istartswith", "last_name__istartswith"]

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "user_type", "avatar")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )


@admin.register(models.Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ["id", "start_date", "end_date"]
    list_filter = ["room", "start_date", "end_date"]
    search_fields = [
        "apartment__name",
        "room__name",
        "tenant__first_name",
        "tenant__last_name",
    ]


from django.contrib import admin


class BillAdmin(admin.ModelAdmin):
    list_display = ("id", "apartment", "bill_type", "created_at", "updated_at")
    list_filter = ("bill_type", "paid", "created_at")
    search_fields = ("apartment__address", "bill_type")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        else:
            return queryset.filter(apartment__owner=request.user)


class InquiryReplyInline(admin.TabularInline):
    model = InquiryReply


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "apartment",
        "sender",
        "receiver",
        "type",
        "status",
        "created_at",
    )
    list_filter = ("type", "status", "created_at")
    search_fields = (
        "apartment__address",
        "message",
        "sender__email",
        "receiver__email",
    )
    inlines = [InquiryReplyInline]


@admin.register(InquiryReply)
class InquiryReplyAdmin(admin.ModelAdmin):
    list_display = ("id", "inquiry", "sender", "created_at")
    search_fields = ("inquiry__apartment__address", "message", "sender__email")


admin.site.register(Bill, BillAdmin)


admin.site.register(models.CustomUser, CustomUserAdmin)
