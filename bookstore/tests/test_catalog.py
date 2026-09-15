import pytest
from django.urls import reverse
from rest_framework import status

from bookstore.models import Book, Author


@pytest.mark.django_db
class TestCatalog:
    def test_get_books_public(self, api_client, book):
        url = reverse("bookstore:book-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["title"] == book.title

    def test_create_book_admin_only(
            self, api_client, auth_client, admin_client, author, publisher
    ):
        url = reverse("bookstore:book-list")
        data = {
            "title": "New Book",
            "author": str(author.id),
            "publisher": str(publisher.id),
            "genre": "Drama",
            "price": "15.00",
            "publication_year": 2024,
            "pages": 100,
            "in_stock": True
        }

        # should fail
        resp1 = api_client.post(url, data, format="json")
        assert resp1.status_code == status.HTTP_401_UNAUTHORIZED

        # should fail
        resp2 = auth_client.post(url, data, format="json")
        assert resp2.status_code == status.HTTP_403_FORBIDDEN

        # should succeed
        resp3 = admin_client.post(url, data, format="json")
        assert resp3.status_code == status.HTTP_201_CREATED
        assert Book.objects.filter(title="New Book").exists()

    def test_delete_author_with_books_fails(self, admin_client, author, book):
        url = reverse("bookstore:author-detail", kwargs={"pk": author.pk})
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "Cannot delete" in response.data.get("error", "")

    def test_delete_author_without_books_succeeds(self, admin_client):
        author = Author.objects.create(name="Empty Author")
        url = reverse("bookstore:author-detail", kwargs={"pk": author.pk})
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Author.objects.filter(pk=author.pk).exists()

    def test_get_publisher_detail(self, api_client, publisher):
        url = reverse("bookstore:publisher-detail", kwargs={"pk": publisher.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == publisher.name
