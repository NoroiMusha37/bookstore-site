from django.urls import path
from bookstore.views import (
    PublisherListAPIView, PublisherDetailAPIView,
    AuthorListAPIView, AuthorDetailAPIView,
    BookListAPIView, BookDetailAPIView
)

app_name = "bookstore"

urlpatterns = [
    path("publishers/", PublisherListAPIView.as_view(), name="publisher-list"),
    path("publishers/<uuid:pk>/", PublisherDetailAPIView.as_view(), name="publisher-detail"),

    path("authors/", AuthorListAPIView.as_view(), name="author-list"),
    path("authors/<uuid:pk>/", AuthorDetailAPIView.as_view(), name="author-detail"),

    path("books/", BookListAPIView.as_view(), name="book-list"),
    path("books/<uuid:pk>/", BookDetailAPIView.as_view(), name="book-detail"),
]