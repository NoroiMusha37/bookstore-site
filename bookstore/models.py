import uuid
from decimal import Decimal

from django.db import models
from django.db.models import DecimalField, F, Sum
from django.core.validators import MinValueValidator

from config import settings


class Author(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    name = models.CharField(max_length=255, unique=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Publisher(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    publisher = models.ForeignKey(Publisher, on_delete=models.PROTECT)
    genre = models.CharField(max_length=100)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))]
    )
    popularity_score = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    publication_year = models.PositiveIntegerField()
    pages = models.PositiveIntegerField()
    in_stock = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.publication_year})"


class Cart(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="cart",
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_price(self):
        result = self.items.aggregate(
            total=Sum(
                F("quantity") * F("book__price"),
                output_field=DecimalField(),
            )
        )
        return result["total"] or Decimal("0.00")


class CartItem(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    cart = models.ForeignKey(
        Cart,
        related_name="items",
        on_delete=models.CASCADE
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "book")

    @property
    def item_total(self):
        return self.quantity * self.book.price


class Order(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=50, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class OrderItem(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE
    )
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    item_total = models.DecimalField(max_digits=10, decimal_places=2)
