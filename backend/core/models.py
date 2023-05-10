from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from uuid import uuid4
from .validators import validate_file_size
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext as _
from phonenumber_field.modelfields import PhoneNumberField


class CustomUser(AbstractUser):
    OWNER = "owner"
    RENTER = "renter"
    SEARCHER = "searcher"
    USER_TYPE_CHOICES = ((OWNER, "Owner"), (RENTER, "Renter"), (SEARCHER, "Searcher"))
    user_type = models.CharField(choices=USER_TYPE_CHOICES, max_length=10)
    custom_groups = models.ManyToManyField(
        Group, related_name="custom_users", blank=True
    )
    custom_user_permissions = models.ManyToManyField(
        Permission, related_name="custom_users", blank=True
    )

    is_superuser = models.BooleanField(default=False)
    first_name = models.CharField(max_length=30, blank=True, default="")
    last_name = models.CharField(max_length=30, blank=True, default="")
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    phone = PhoneNumberField(blank=True, null=True)

    age = models.PositiveIntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, default="")
    bio = models.TextField(blank=True, default="")

    preferred_location = models.CharField(max_length=100, blank=True, default="")
    preferred_roommates = models.CharField(max_length=100, blank=True, default="")
    preferred_rent = models.PositiveIntegerField(blank=True, null=True)


class Apartment(models.Model):
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="apartments_owned",
        default=None,
        help_text=_("The user that owns the apartment."),
    )
    city = models.CharField(
        max_length=100,
        help_text=_("The city where the apartment is located."),
        null=True,
    )
    street = models.CharField(
        max_length=100,
        help_text=_("The street where the apartment is located."),
        null=True,
    )
    building_number = models.CharField(
        max_length=10,
        help_text=_("The building number of the apartment."),
        null=True,
    )
    apartment_number = models.CharField(
        max_length=10,
        help_text=_("The apartment number."),
        null=True,
    )
    floor = models.IntegerField(
        help_text=_("The floor of the apartment."),
        null=True,
    )
    description = models.TextField(
        blank=True, null=True, help_text=_("A description of the apartment.")
    )
    size = models.CharField(max_length=50, help_text=_("The size of the apartment."))
    balcony = models.BooleanField(
        default=False, help_text=_("Whether the apartment has a balcony.")
    )
    bbq_allowed = models.BooleanField(
        default=False, help_text=_("Whether BBQs are allowed on the apartment.")
    )
    smoking_allowed = models.BooleanField(
        default=False, help_text=_("Whether smoking is allowed in the apartment.")
    )
    allowed_pets = models.BooleanField(
        default=False, help_text=_("Whether pets are allowed in the apartment.")
    )
    ac = models.BooleanField(
        default=False, help_text=_("Whether the apartment has air conditioning.")
    )

    @property
    def address(self):
        return f"{self.street} {self.building_number}, Apt {self.apartment_number}, Floor {self.floor}, {self.city}"

    def __str__(self) -> str:
        return f"{self.street} {self.building_number}, Apt {self.apartment_number}, {self.city}"

    class Meta:
        ordering = ["city", "street", "building_number", "apartment_number"]


class ApartmentImage(models.Model):
    image = models.ImageField(
        upload_to="apartment_images/",
        validators=[validate_file_size],
        help_text=_("The image of the apartment."),
        null=True,
        blank=True,
    )
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name="images",
        blank=True,
        null=True,
    )


class Contract(models.Model):
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="contracts_owned",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    rent_amount = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(1)]
    )
    deposit_amount = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(1)]
    )
    terms_and_conditions = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to="contracts/", blank=True, null=True)


class Room(models.Model):
    apartment = models.ForeignKey(
        Apartment, on_delete=models.PROTECT, related_name="rooms"
    )
    renter = models.OneToOneField(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name="rooms_rented",
        null=True,
        blank=True,
    )
    description = models.TextField(null=True, blank=True)
    contract = models.OneToOneField(
        Contract, on_delete=models.SET_NULL, related_name="room", null=True, blank=True
    )

    price_per_month = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(1)]
    )
    size = models.CharField(max_length=50)
    window = models.BooleanField(default=False, blank=True)
    ac = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.apartment.address}, Room {self.id}"

    def can_user_edit(self, user):
        if user.is_authenticated and user == self.apartment.owner:
            return True
        return False

    class Meta:
        ordering = ["price_per_month"]


class RoomImage(models.Model):
    image = models.ImageField(
        upload_to="room_images/",
        validators=[validate_file_size],
        help_text=_("The image of the room."),
        null=True,
        blank=True,
    )
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="images", blank=True, null=True
    )


class Bill(models.Model):
    ELECTRICITY = "electricity"
    GAS = "gas"
    WATER = "water"
    RENT = "rent"
    OTHER = "other"

    BILL_TYPES = [
        (ELECTRICITY, "Electricity"),
        (GAS, "Gas"),
        (WATER, "Water"),
        (RENT, "Rent"),
        (OTHER, "Other"),
    ]

    apartment = models.ForeignKey(
        Apartment, on_delete=models.CASCADE, related_name="bills"
    )
    bill_type = models.CharField(max_length=20, choices=BILL_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    paid = models.BooleanField(
        default=False, help_text=_("Whether the bill payed or not.")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bills_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file = models.FileField(upload_to="bill_files/", null=True, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return (
            f"{self.get_bill_type_display()} bill for {self.apartment} on {self.date}"
        )


class Inquiry(models.Model):
    class InquiryStatus(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    status = models.CharField(
        max_length=10,
        choices=InquiryStatus.choices,
        default=InquiryStatus.OPEN,
    )
    INQUIRY_TYPE_CHOICES = [
        ("defects", "Defects"),
        ("questions", "Questions"),
        ("payment", "Payment"),
        ("problem", "Problem"),
        ("other", "Other"),
    ]
    apartment = models.ForeignKey(
        Apartment, on_delete=models.CASCADE, related_name="inquiries"
    )
    sender = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="sent_inquiries", null=True
    )
    receiver = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="received_inquiries",
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=20, choices=INQUIRY_TYPE_CHOICES)
    message = models.TextField()
    image = models.ImageField(upload_to="inquiry/", blank=True, null=True)

    def __str__(self):
        return f"Inquiry #{self.id} about {self.apartment.address}"

    class Meta:
        ordering = ["-created_at"]


class InquiryReply(models.Model):
    inquiry = models.ForeignKey(
        Inquiry, on_delete=models.CASCADE, related_name="replies"
    )
    sender = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="sent_replies"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField()

    def __str__(self):
        return f"Reply #{self.id} to Inquiry #{self.inquiry.id}"

    class Meta:
        ordering = ["-created_at"]


class Review(models.Model):
    product = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="reviews")
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)
