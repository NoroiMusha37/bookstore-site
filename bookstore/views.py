from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from bookstore.models import Book, Author, Publisher, CartItem, OrderItem
from bookstore.serializers import (
    PublisherListSerializer, PublisherDetailSerializer,
    AuthorListSerializer, AuthorDetailSerializer,
    BookListSerializer, BookDetailSerializer,
)


class PublisherListAPIView(APIView):
    def get(self, request):
        publishers = Publisher.objects.all()
        serializer = PublisherListSerializer(publishers, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PublisherDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublisherDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(Publisher, pk=pk)

    def get(self, request, pk):
        try:
            publisher = Publisher.objects.prefetch_related("book_set").get(pk=pk)
        except Publisher.DoesNotExist:
            raise NotFound("Publisher not found.")
        serializer = PublisherDetailSerializer(publisher)
        return Response(serializer.data)

    def patch(self, request, pk):
        publisher = self.get_object(pk)
        serializer = PublisherDetailSerializer(
            publisher, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        publisher = self.get_object(pk)
        if publisher.book_set.exists():
            return Response(
                {"error": "Cannot delete publisher with associated books."},
                status=status.HTTP_409_CONFLICT
            )
        publisher.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuthorListAPIView(APIView):
    def get(self, request):
        authors = Author.objects.all()
        serializer = AuthorListSerializer(authors, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AuthorDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthorDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(Author, pk=pk)

    def get(self, request, pk):
        try:
            author = Author.objects.prefetch_related("book_set").get(pk=pk)
        except Author.DoesNotExist:
            raise NotFound("Author not found.")
        serializer = AuthorDetailSerializer(author)
        return Response(serializer.data)

    def patch(self, request, pk):
        author = self.get_object(pk)
        serializer = AuthorDetailSerializer(
            author, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        author = self.get_object(pk)
        if author.book_set.exists():
            return Response(
                {"error": "Cannot delete author with associated books."},
                status=status.HTTP_409_CONFLICT
            )
        author.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BookListAPIView(APIView):
    VALID_ORDERINGS = {
        "price", "-price", "popularity_score",
        "-popularity_score", "genre", "-genre"
    }

    def get(self, request):
        books = Book.objects.select_related("author", "publisher")

        search = request.query_params.get("search")
        publishers = request.query_params.get("publisher")
        genres = request.query_params.get("genre")
        ordering = request.query_params.get("ordering")

        if search:
            search = search.strip()
            if search:
                books = books.filter(
                    Q(title__icontains=search) | Q(author__name__icontains=search)
                )

        if publishers:
            publisher_list = [
                clean_p for p in publishers.split(",")
                if (clean_p := p.strip())
            ]
            if publisher_list:
                books = books.filter(publisher__name__in=publisher_list)

        if genres:
            genre_list = [
                clean_g for g in genres.split(",")
                if (clean_g := g.strip())
            ]
            if genre_list:
                books = books.filter(genre__in=genre_list)

        if ordering:
            ordering = ordering.strip()
            if ordering in self.VALID_ORDERINGS:
                books = books.order_by(ordering)
        else:
            books = books.order_by("-popularity_score")

        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BookDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(Book, pk=pk)

    def get(self, request, pk):
        book = self.get_object(pk)
        serializer = BookDetailSerializer(book)
        return Response(serializer.data)

    def patch(self, request, pk):
        book = self.get_object(pk)
        serializer = BookDetailSerializer(
            book, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        book = self.get_object(pk)
        if CartItem.objects.filter(book=book).exists() or OrderItem.objects.filter(book=book).exists():
            return Response(
                {"error": "Cannot delete a book that is in an active cart or order history."},
                status=status.HTTP_409_CONFLICT
            )
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
