from rest_framework import permissions
from .models import Apartment, ApartmentImage, Bill, Contract, Review, Room, RoomImage
from rest_framework.permissions import BasePermission


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated


class IsApartmentOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Apartment):
            return obj.owner == request.user
        elif isinstance(obj, Bill):
            return obj.apartment.owner == request.user
        elif isinstance(obj, Room):
            return (
                obj.apartment.owner == request.user
            )  # Check the owner of the room's apartment
        elif isinstance(obj, Contract):
            return (
                obj.room.apartment.owner == request.user
            )  # Check the owner of the room's apartment
        elif isinstance(obj, Review):
            return obj.apartment.owner == request.user
        elif isinstance(obj, ApartmentImage):
            return obj.apartment.owner == request.user
        elif isinstance(obj, RoomImage):
            return obj.room.apartment.owner == request.user
        else:
            return False


class IsRoomRenter(BasePermission):
    message = "You must be the renter of a room in this apartment."

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and request.user.user_type == "renter":
            if isinstance(obj, Bill):
                # Check if the user is the renter of a room in the apartment
                apartment = obj.apartment
                rented_rooms_in_apartment = Room.objects.filter(
                    apartment=apartment, renter=request.user
                )
                if rented_rooms_in_apartment.exists():
                    return True
            elif isinstance(obj, Contract):
                # Check if the user is the renter of the room in the contract
                room_renter = obj.room.renter == request.user
                if room_renter:
                    return True
                # Check if the user is the owner of the apartment
                apartment_owner = obj.room.apartment.owner == request.user
                if apartment_owner:
                    return True
                # Check if the renter of the room is the user
                room_renter = obj.room.renter == request.user
                if room_renter:
                    return True
            elif isinstance(obj, Room):
                # Check if the user is the renter of this room
                if obj.renter == request.user:
                    return True
        return False


class IsSearcher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == "searcher"


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.apartment.owner == request.user
