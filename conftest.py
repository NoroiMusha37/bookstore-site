import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from bookstore.models import Author, Publisher, Book, Cart, CartItem

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="TestPassword123!",
        phone="+1234567890"
    )
    return user


@pytest.fixture
def admin_user(db):
    admin = User.objects.create_superuser(
        username="adminuser",
        email="admin@example.com",
        password="AdminPassword123!"
    )
    return admin


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def author(db):
    return Author.objects.create(
        name="John Doe",
        bio="A great writer."
    )


@pytest.fixture
def publisher(db):
    return Publisher.objects.create(
        name="Penguin Books",
        description="A great publisher."
    )


@pytest.fixture
def book(db, author, publisher):
    return Book.objects.create(
        title="The Great Novel",
        author=author,
        publisher=publisher,
        genre="Fiction",
        price="19.99",
        popularity_score=4.5,
        description="A masterpiece.",
        publication_year=2023,
        pages=350,
        in_stock=True
    )


@pytest.fixture
def out_of_stock_book(db, author, publisher):
    return Book.objects.create(
        title="Out of Stock Novel",
        author=author,
        publisher=publisher,
        genre="Sci-Fi",
        price="29.99",
        popularity_score=4.8,
        description="Another masterpiece, but sold out.",
        publication_year=2024,
        pages=400,
        in_stock=False
    )


@pytest.fixture
def user_cart(db, user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart


@pytest.fixture
def cart_item(db, user_cart, book):
    return CartItem.objects.create(
        cart=user_cart,
        book=book,
        quantity=2
    )
