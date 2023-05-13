from rest_framework import serializers
from .models import (
    ApartmentImage,
    Inquiry,
    InquiryReply,
    Room,
    Apartment,
    RoomImage,
    Review,
    CustomUser,
    Contract,
    Bill,
)
from django.shortcuts import get_object_or_404
from django.utils import timezone
from cloudinary.uploader import upload
import cloudinary


class CustomUserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(max_length=None, use_url=True)

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "email",
            "password",
            "user_type",
            "first_name",
            "last_name",
            "avatar",
            "age",
            "gender",
            "bio",
            "preferred_location",
            "preferred_roommates",
            "preferred_rent",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password")
        avatar = validated_data.pop("avatar", None)

        user = CustomUser(**validated_data)

        if avatar is not None:
            user.avatar = avatar

        user.set_password(password)
        user.save()
        return user


class BillSerializer(serializers.ModelSerializer):
    file = serializers.ImageField(max_length=None, use_url=True, required=False)

    class Meta:
        model = Bill
        fields = [
            "id",
            "apartment",
            "bill_type",
            "amount",
            "date",
            "created_by",
            "created_at",
            "file",
        ]
        read_only_fields = ["created_by", "created_at"]

    def validate(self, data):
        user = self.context["request"].user
        if "apartment" in data and data["apartment"].owner != user:
            raise serializers.ValidationError(
                "You are not the owner of this apartment."
            )

        # Validate date is not in the future
        if "date" in data and data["date"] > timezone.localdate():
            raise serializers.ValidationError("Date cannot be in the future.")

        return data


class ApartmentImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(max_length=None, use_url=True)

    def create(self, validated_data):
        print(validated_data)  # Debug: print the validated data
        apartment_id = self.context["apartment_id"]
        return ApartmentImage.objects.create(
            apartment_id=apartment_id, **validated_data
        )

    class Meta:
        model = ApartmentImage
        fields = ["id", "image", "apartment_id"]


class ApartmentSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.email")
    owner_id = serializers.ReadOnlyField(source="owner.id")
    rooms = serializers.SerializerMethodField()
    bill_ids = serializers.SerializerMethodField()
    images = ApartmentImageSerializer(many=True, read_only=True)

    def get_rooms(self, obj):
        rooms_queryset = obj.rooms.all()
        context = self.context.copy()
        context["nested"] = True
        return RoomSerializer(rooms_queryset, many=True, context=context).data

    def get_bill_ids(self, obj):
        bills = obj.bills.all()
        return [bill.id for bill in bills]

    class Meta:
        model = Apartment
        fields = [
            "id",
            "owner",
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
            "bill_ids",
            "rooms",
            "images",
        ]


class ContractSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, use_url=True)

    room_id = serializers.IntegerField(source="room.id", read_only=True)
    apartment_id = serializers.PrimaryKeyRelatedField(
        source="room.apartment.id", read_only=True
    )

    class Meta:
        model = Contract
        fields = [
            "id",
            "room_id",
            "apartment_id",
            "start_date",
            "end_date",
            "deposit_amount",
            "rent_amount",
            "file",
        ]

    def get_file(self, obj):
        if obj.file and not obj.file.url.endswith(".pdf"):
            return obj.file.url + ".pdf"
        return obj.file.url

    def create(self, validated_data):
        file = validated_data.pop("file", None)

        if file:
            upload_result = upload(file, resource_type="raw")
            validated_data["file"] = upload_result["url"]

        contract = Contract.objects.create(**validated_data)

        return contract

    def update(self, instance, validated_data):
        file = validated_data.get("file", None)

        if file:
            if instance.file:
                public_id = instance.file.split("/")[-1].split(".")[0]
                cloudinary.uploader.destroy(public_id, resource_type="raw")

            upload_result = upload(file, resource_type="raw")
            validated_data["file"] = upload_result["url"]

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()

        return instance


class RoomImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(max_length=None, use_url=True)

    def create(self, validated_data):
        room_id = self.context["room_id"]
        return RoomImage.objects.create(room_id=room_id, **validated_data)

    class Meta:
        model = RoomImage
        fields = ["id", "image", "room_id"]


class RoomSerializer(serializers.ModelSerializer):
    images = RoomImageSerializer(many=True, read_only=True)
    apartment = serializers.PrimaryKeyRelatedField(
        queryset=Apartment.objects.all(), write_only=True
    )
    contract = ContractSerializer(read_only=True)
    renter = CustomUserSerializer(read_only=True)

    renter_search = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )
    city = serializers.ReadOnlyField(source="apartment.city")
    street = serializers.ReadOnlyField(source="apartment.street")
    building_number = serializers.ReadOnlyField(source="apartment.building_number")
    apartment_number = serializers.ReadOnlyField(source="apartment.apartment_number")
    floor = serializers.ReadOnlyField(source="apartment.floor")

    def to_representation(self, instance):
        if self.context.get("nested"):
            self.fields.pop("apartment", None)
        return super().to_representation(instance)

    class Meta:
        model = Room
        fields = [
            "id",
            "description",
            "size",
            "price_per_month",
            "window",
            "images",
            "contract",
            "renter",
            "apartment_id",
            "apartment",
            "city",
            "street",
            "building_number",
            "apartment_number",
            "floor",
            "renter_search",
        ]

    def create(self, validated_data):
        apartment = validated_data.pop("apartment")
        room = Room.objects.create(apartment=apartment, **validated_data)
        return room

    def update(self, instance, validated_data):
        renter_search = validated_data.pop("renter_search", None)
        if renter_search is not None:
            if renter_search != "":
                renter = get_object_or_404(
                    CustomUser, user_type="renter", username__icontains=renter_search
                )
                instance.renter = renter
            else:
                instance.renter = None
            instance.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "date", "name", "description"]

    def create(self, validated_data):
        product_id = self.context["product_id"]
        return Review.objects.create(product_id=product_id, **validated_data)


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "first_name", "last_name"]


class InquirySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(max_length=None, use_url=True)

    sender = SimpleUserSerializer(read_only=True)
    receiver = SimpleUserSerializer(read_only=True)
    apartment = ApartmentSerializer(read_only=True)
    status = serializers.ChoiceField(choices=Inquiry.InquiryStatus.choices)
    apartment_address = serializers.SerializerMethodField()

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "apartment",
            "apartment_address",
            "sender",
            "receiver",
            "type",
            "message",
            "created_at",
            "status",
            "image",
        ]

    def get_apartment_address(self, obj):
        return obj.apartment.address


class InquiryReplySerializer(serializers.ModelSerializer):
    sender = SimpleUserSerializer(read_only=True)
    apartment = ApartmentSerializer(read_only=True)
    room = RoomSerializer(read_only=True)

    class Meta:
        model = InquiryReply
        fields = ["id", "message", "sender", "apartment", "room", "created_at"]
