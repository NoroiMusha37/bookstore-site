from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from bookstore.models import Order


@pytest.mark.django_db
class TestOrders:
    def test_checkout_cart(self, auth_client, cart_item, user):
        url = reverse("order-list")
        response = auth_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.filter(user=user).exists()

        assert not user.cart.items.exists()

    def test_checkout_empty_cart_fails(self, auth_client, user_cart):
        url = reverse("order-list")
        response = auth_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_orders_list(self, auth_client, user, cart_item):
        checkout_url = reverse("order-list")
        auth_client.post(checkout_url)

        url = reverse("order-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        expected_price = Decimal(cart_item.book.price) * cart_item.quantity
        assert str(response.data[0]["total_price"]) == str(expected_price)

    def test_get_order_detail(self, auth_client, user, cart_item):
        auth_client.post(reverse("order-list"))
        order = Order.objects.get(user=user)

        url = reverse("order-detail", kwargs={"pk": order.pk})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["items"]) == 1
        assert str(response.data["items"][0]["book"]) == str(cart_item.book.id)
