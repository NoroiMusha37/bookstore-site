import pytest
from django.urls import reverse
from rest_framework import status

from bookstore.models import CartItem


@pytest.mark.django_db
class TestCart:
    def test_add_item_to_cart(self, auth_client, book):
        url = reverse("cart-item-add")
        data = {"book": str(book.id), "quantity": 1}
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["quantity"] == 1
        assert CartItem.objects.filter(book=book).exists()

    def test_add_out_of_stock_item(self, auth_client, out_of_stock_book):
        url = reverse("cart-item-add")
        data = {"book": str(out_of_stock_book.id), "quantity": 1}
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not CartItem.objects.filter(book=out_of_stock_book).exists()

    def test_get_cart(self, auth_client, cart_item):
        url = reverse("cart-detail")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["items"]) == 1
        assert str(response.data["items"][0]["book"]) == str(cart_item.book.id)

    def test_update_cart_item(self, auth_client, cart_item):
        url = reverse("cart-item-detail", kwargs={"book_id": cart_item.book.id})
        data = {"quantity": 5}
        response = auth_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        cart_item.refresh_from_db()
        assert cart_item.quantity == 5

    def test_remove_cart_item(self, auth_client, cart_item):
        url = reverse("cart-item-detail", kwargs={"book_id": cart_item.book.id})
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CartItem.objects.filter(id=cart_item.id).exists()

    def test_clear_cart(self, auth_client, cart_item):
        url = reverse("cart-detail")
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CartItem.objects.exists()
