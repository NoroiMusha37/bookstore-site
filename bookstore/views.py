import logging

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bookstore.models import Book, Author, Publisher, Cart, CartItem, Order, OrderItem
from bookstore.permissions import IsAdminUserOrReadOnly
from bookstore.serializers import (
    PublisherListSerializer, PublisherDetailSerializer,
    AuthorListSerializer, AuthorDetailSerializer,
    BookListSerializer, BookDetailSerializer,
    CartSerializer, CartItemWriteSerializer, CartItemUpdateSerializer,
    CartItemReadSerializer, OrderListSerializer, OrderDetailSerializer,
)

logger = logging.getLogger(__name__)


class PublisherListAPIView(APIView):
    permission_classes = [IsAdminUserOrReadOnly]

    def get(self, request):
        publishers = Publisher.objects.all()
        serializer = PublisherListSerializer(publishers, many=True)

        logger.info(f"Fetched publishers")
        return Response(serializer.data)

    def post(self, request):
        serializer = PublisherDetailSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            logger.info(f"Created publisher {serializer.validated_data["name"]}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        logger.warning(
            f"Failed to create publisher "
            f"{request.data.get("name", "Unknown")}: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublisherDetailAPIView(APIView):
    permission_classes = [IsAdminUserOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(Publisher, pk=pk)

    def get(self, request, pk):
        try:
            publisher = Publisher.objects.prefetch_related("book_set").get(pk=pk)
        except Publisher.DoesNotExist:
            logger.warning(f"Publisher {pk} not found")
            raise NotFound("Publisher not found.")

        serializer = PublisherDetailSerializer(publisher)

        logger.info(f"Fetched publisher {publisher.name}")
        return Response(serializer.data)

    def patch(self, request, pk):
        publisher = self.get_object(pk)
        serializer = PublisherDetailSerializer(
            publisher, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()

            logger.info(f"Updated publisher {publisher.name}")
            return Response(serializer.data)

        logger.warning(
            f"Failed to update publisher {publisher.name}: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        publisher = self.get_object(pk)
        if publisher.book_set.exists():
            logger.warning(
                f"Failed to delete publisher {publisher.name}: "
                f"they have associated books"
            )
            return Response(
                {"error": "Cannot delete publisher with associated books."},
                status=status.HTTP_409_CONFLICT
            )
        publisher.delete()

        logger.info(f"Deleted publisher {publisher.name}")
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuthorListAPIView(APIView):
    permission_classes = [IsAdminUserOrReadOnly]

    def get(self, request):
        authors = Author.objects.all()
        serializer = AuthorListSerializer(authors, many=True)

        logger.info(f"Fetched authors")
        return Response(serializer.data)

    def post(self, request):
        serializer = AuthorDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            logger.info(f"Created author {serializer.validated_data["name"]}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        logger.warning(
            f"Failed to create author "
            f"{request.data.get("name", "Unknown")}: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthorDetailAPIView(APIView):
    permission_classes = [IsAdminUserOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(Author, pk=pk)

    def get(self, request, pk):
        try:
            author = Author.objects.prefetch_related("book_set").get(pk=pk)
        except Author.DoesNotExist:
            logger.warning(f"Author {pk} not found")
            raise NotFound("Author not found.")

        serializer = AuthorDetailSerializer(author)

        logger.info(f"Fetched author {author.name}")
        return Response(serializer.data)

    def patch(self, request, pk):
        author = self.get_object(pk)
        serializer = AuthorDetailSerializer(
            author, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()

            logger.info(f"Updated author {author.name}")
            return Response(serializer.data)

        logger.warning(
            f"Failed to update author {author.name}: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        author = self.get_object(pk)
        if author.book_set.exists():
            logger.warning(
                f"Failed to delete author {author.name}: "
                f"they have associated books"
            )
            return Response(
                {"error": "Cannot delete author with associated books."},
                status=status.HTTP_409_CONFLICT
            )
        author.delete()

        logger.info(f"Deleted author {author.name}")
        return Response(status=status.HTTP_204_NO_CONTENT)


class BookListAPIView(APIView):
    permission_classes = [IsAdminUserOrReadOnly]

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

        logger.info(f"Fetched books with params: {request.query_params}")
        return Response(serializer.data)

    def post(self, request):
        serializer = BookDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            logger.info(f"Created book {serializer.validated_data["title"]}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        logger.warning(
            f"Failed to create book "
            f"{request.data.get("title", "Unknown")}: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDetailAPIView(APIView):
    permission_classes = [IsAdminUserOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(Book, pk=pk)

    def get(self, request, pk):
        book = self.get_object(pk)
        serializer = BookDetailSerializer(book)

        logger.info(f"Fetched book {book.title}")
        return Response(serializer.data)

    def patch(self, request, pk):
        book = self.get_object(pk)
        serializer = BookDetailSerializer(
            book, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()

            logger.info(f"Updated book {book.title}")
            return Response(serializer.data)

        logger.warning(
            f"Failed to update book {book.title}: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        book = self.get_object(pk)
        if CartItem.objects.filter(book=book).exists() or OrderItem.objects.filter(book=book).exists():
            logger.warning(
                f"Failed to delete book {book.title}: "
                f"in active cart or order history"
            )
            return Response(
                {"error": "Cannot delete a book that is in an active cart or order history."},
                status=status.HTTP_409_CONFLICT
            )
        book.delete()

        logger.info(f"Deleted book {book.title}")
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        serializer = OrderListSerializer(orders, many=True)

        logger.info(f"User {request.user.username} fetched their orders")
        return Response(serializer.data)

    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = cart.items.select_related("book").all()

        if not cart_items.exists():
            logger.warning(f"User {request.user.username} attempted to checkout an empty cart")
            return Response(
                {"error": "Cannot create an order from an empty cart."},
                status=status.HTTP_400_BAD_REQUEST
            )

        for item in cart_items:
            if not item.book.in_stock:
                logger.warning(
                    f"User {request.user.username} tried to checkout with "
                    f"out of stock book {item.book.title}"
                )
                return Response(
                    {"error": f"Book '{item.book.title}' is currently out of stock."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                status=Order.Status.PENDING,
                total_price=cart.total_price
            )

            order_items = []
            for item in cart_items:
                order_items.append(
                    OrderItem(
                        order=order,
                        book=item.book,
                        quantity=item.quantity,
                        unit_price=item.book.price,
                        item_total=item.item_total
                    )
                )

            OrderItem.objects.bulk_create(order_items)
            cart.items.all().delete()

        serializer = OrderDetailSerializer(order)
        logger.info(f"User {request.user.username} successfully checked out")

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        serializer = OrderDetailSerializer(order)

        logger.info(f"User {request.user.username} fetched details for order {pk}")
        return Response(serializer.data)


class CartDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        if created:
            logger.info(f"Created new cart for user {request.user.username}")
        serializer = CartSerializer(cart)

        logger.info(f"User {request.user.username} fetched their cart")
        return Response(serializer.data)

    def delete(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()

        logger.info(f"User {request.user.username} cleared their cart")
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemAddAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemWriteSerializer(data=request.data)

        if serializer.is_valid():
            book = serializer.validated_data["book"]

            if CartItem.objects.filter(cart=cart, book=book).exists():
                logger.warning(
                    f"User {request.user.username} tried to add book {book.title} "
                    f"which is already in the cart"
                )
                return Response(
                    {"error": "This book is already in your cart. Use PATCH to update quantity."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item = serializer.save(cart=cart)

            logger.info(f"User {request.user.username} added book {book.title} to cart")

            read_serializer = CartItemReadSerializer(cart_item)
            return Response(read_serializer.data, status=status.HTTP_201_CREATED)

        logger.warning(f"User {request.user.username} failed to add to cart: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartItemDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, book_id):
        cart = get_object_or_404(Cart, user=request.user)
        return get_object_or_404(CartItem, cart=cart, book_id=book_id)

    def patch(self, request, book_id):
        cart_item = self.get_object(request, book_id)
        serializer = CartItemUpdateSerializer(
            cart_item, data=request.data, partial=True
        )
        if serializer.is_valid():
            cart_item = serializer.save()

            logger.info(
                f"User {request.user.username} updated quantity of "
                f"{cart_item.book.title} to {cart_item.quantity}"
            )

            read_serializer = CartItemReadSerializer(cart_item)
            return Response(read_serializer.data)

        logger.warning(
            f"User {request.user.username} failed to update cart item: "
            f"{serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, book_id):
        cart_item = self.get_object(request, book_id)
        book_title = cart_item.book.title
        cart_item.delete()

        logger.info(f"User {request.user.username} removed {book_title} from cart")
        return Response(status=status.HTTP_204_NO_CONTENT)
