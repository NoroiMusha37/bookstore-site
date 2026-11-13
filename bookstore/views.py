import logging

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
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

# Shared OpenAPI response descriptions
ERROR_RESPONSE = inline_serializer("ErrorResponse", {"error": serializers.CharField()})
RESPONSE_400 = OpenApiResponse(description="Invalid data: field errors are returned per field.")
RESPONSE_401 = OpenApiResponse(description="Missing or invalid JWT access token.")
RESPONSE_403 = OpenApiResponse(description="Authenticated user is not an admin (is_staff=False).")
RESPONSE_404 = OpenApiResponse(description="Object not found.")

BOOK_EXAMPLE = OpenApiExample(
    "Book",
    value={
        "title": "The Hobbit",
        "author": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "publisher": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "genre": "fantasy",
        "price": "15.99",
        "popularity_score": 85,
        "description": "A fantasy novel.",
        "publication_year": 1937,
        "pages": 310,
        "in_stock": True,
    },
    request_only=True,
)


class PublisherListAPIView(APIView):
    permission_classes = [IsAdminUserOrReadOnly]

    @extend_schema(tags=["Publishers"], summary="List publishers", responses={200: PublisherListSerializer(many=True)})
    def get(self, request):
        publishers = Publisher.objects.all()
        serializer = PublisherListSerializer(publishers, many=True)

        logger.debug(f"Fetched publishers")
        return Response(serializer.data)

    @extend_schema(
        tags=["Publishers"], summary="Create a publisher", description="Admin only.",
        request=PublisherDetailSerializer,
        responses={201: PublisherDetailSerializer, 400: RESPONSE_400, 401: RESPONSE_401, 403: RESPONSE_403},
    )
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

    @extend_schema(
        tags=["Publishers"], summary="Get a publisher with their books",
        responses={200: PublisherDetailSerializer, 404: RESPONSE_404},
    )
    def get(self, request, pk):
        try:
            publisher = Publisher.objects.prefetch_related("book_set").get(pk=pk)
        except Publisher.DoesNotExist:
            logger.warning(f"Publisher {pk} not found")
            raise NotFound("Publisher not found.")

        serializer = PublisherDetailSerializer(publisher)

        logger.debug(f"Fetched publisher {publisher.name}")
        return Response(serializer.data)

    @extend_schema(
        tags=["Publishers"], summary="Update a publisher", description="Admin only.",
        request=PublisherDetailSerializer,
        responses={200: PublisherDetailSerializer, 400: RESPONSE_400, 401: RESPONSE_401, 403: RESPONSE_403, 404: RESPONSE_404},
    )
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

    @extend_schema(
        tags=["Publishers"], summary="Delete a publisher", description="Admin only.",
        responses={
            204: OpenApiResponse(description="Publisher deleted."),
            401: RESPONSE_401, 403: RESPONSE_403, 404: RESPONSE_404,
            409: OpenApiResponse(ERROR_RESPONSE, description="Publisher has associated books."),
        },
    )
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

    @extend_schema(tags=["Authors"], summary="List authors", responses={200: AuthorListSerializer(many=True)})
    def get(self, request):
        authors = Author.objects.all()
        serializer = AuthorListSerializer(authors, many=True)

        logger.debug(f"Fetched authors")
        return Response(serializer.data)

    @extend_schema(
        tags=["Authors"], summary="Create a author", description="Admin only.",
        request=AuthorDetailSerializer,
        responses={201: AuthorDetailSerializer, 400: RESPONSE_400, 401: RESPONSE_401, 403: RESPONSE_403},
    )
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

    @extend_schema(
        tags=["Authors"], summary="Get a author with their books",
        responses={200: AuthorDetailSerializer, 404: RESPONSE_404},
    )
    def get(self, request, pk):
        try:
            author = Author.objects.prefetch_related("book_set").get(pk=pk)
        except Author.DoesNotExist:
            logger.warning(f"Author {pk} not found")
            raise NotFound("Author not found.")

        serializer = AuthorDetailSerializer(author)

        logger.debug(f"Fetched author {author.name}")
        return Response(serializer.data)

    @extend_schema(
        tags=["Authors"], summary="Update a author", description="Admin only.",
        request=AuthorDetailSerializer,
        responses={200: AuthorDetailSerializer, 400: RESPONSE_400, 401: RESPONSE_401, 403: RESPONSE_403, 404: RESPONSE_404},
    )
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

    @extend_schema(
        tags=["Authors"], summary="Delete a author", description="Admin only.",
        responses={
            204: OpenApiResponse(description="Author deleted."),
            401: RESPONSE_401, 403: RESPONSE_403, 404: RESPONSE_404,
            409: OpenApiResponse(ERROR_RESPONSE, description="Author has associated books."),
        },
    )
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

    VALID_ORDERINGS = [
        "popularity_score",
        "-popularity_score",
        "price",
        "-price",
        "genre",
        "-genre"
    ]

    @extend_schema(
        tags=["Books"],
        summary="List books",
        description="Public endpoint, no authentication required. "
                    "Supports search, filtering and ordering.",
        parameters=[
            OpenApiParameter("search", OpenApiTypes.STR, description="Search in book title or author name (case-insensitive)."),
            OpenApiParameter("publisher", OpenApiTypes.STR, description="Comma-separated publisher names, e.g. `Penguin,Vintage`."),
            OpenApiParameter("genre", OpenApiTypes.STR, description="Comma-separated genres, e.g. `fantasy,drama`."),
            OpenApiParameter(
                "ordering", OpenApiTypes.STR,
                enum=VALID_ORDERINGS,
                description="Sort field; prefix with `-` for descending. Default: `-popularity_score`.",
            ),
        ],
        responses={200: BookListSerializer(many=True)},
    )
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

        logger.debug(f"Fetched books with params: {request.query_params}")
        return Response(serializer.data)

    @extend_schema(
        tags=["Books"],
        summary="Create a book",
        description="Admin only (`is_staff=True`). Requires a JWT access token.",
        request=BookDetailSerializer,
        responses={
            201: BookDetailSerializer,
            400: RESPONSE_400,
            401: RESPONSE_401,
            403: RESPONSE_403,
        },
        examples=[BOOK_EXAMPLE],
    )
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

    @extend_schema(
        tags=["Books"],
        summary="Get a book",
        description="Public endpoint, no authentication required.",
        responses={200: BookDetailSerializer, 404: RESPONSE_404},
    )
    def get(self, request, pk):
        book = self.get_object(pk)
        serializer = BookDetailSerializer(book)

        logger.debug(f"Fetched book {book.title}")
        return Response(serializer.data)

    @extend_schema(
        tags=["Books"],
        summary="Update a book",
        description="Admin only. Partial update: send only the fields to change.",
        request=BookDetailSerializer,
        responses={
            200: BookDetailSerializer,
            400: RESPONSE_400,
            401: RESPONSE_401,
            403: RESPONSE_403,
            404: RESPONSE_404,
        },
        examples=[OpenApiExample("Change price", value={"price": "12.50"}, request_only=True)],
    )
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

    @extend_schema(
        tags=["Books"],
        summary="Delete a book",
        description="Admin only. A book that is in any cart or order cannot be deleted.",
        responses={
            204: OpenApiResponse(description="Book deleted."),
            401: RESPONSE_401,
            403: RESPONSE_403,
            404: RESPONSE_404,
            409: OpenApiResponse(
                ERROR_RESPONSE,
                description="Book is in an active cart or order history.",
                examples=[OpenApiExample(
                    "Conflict",
                    value={"error": "Cannot delete a book that is in an active cart or order history."},
                )],
            ),
        },
    )
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

    @extend_schema(tags=["Orders"], summary="List my orders", responses={200: OrderListSerializer(many=True), 401: RESPONSE_401})
    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        serializer = OrderListSerializer(orders, many=True)

        logger.debug(f"User {request.user.username} fetched their orders")
        return Response(serializer.data)

    @extend_schema(
        tags=["Orders"], summary="Checkout cart",
        description="Creates an order from all items in the cart and empties the cart. No request body.",
        request=None,
        responses={
            201: OrderDetailSerializer,
            400: OpenApiResponse(ERROR_RESPONSE, description="Cart is empty or a book is out of stock."),
            401: RESPONSE_401,
            404: OpenApiResponse(description="User has no cart yet."),
        },
    )
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

    @extend_schema(tags=["Orders"], summary="Get my order", responses={200: OrderDetailSerializer, 401: RESPONSE_401, 404: RESPONSE_404})
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        serializer = OrderDetailSerializer(order)

        logger.debug(f"User {request.user.username} fetched details for order {pk}")
        return Response(serializer.data)


class CartDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Cart"],
        summary="Get current cart",
        description="Returns the authenticated user's cart. The cart is created on first access.",
        responses={200: CartSerializer, 401: RESPONSE_401},
    )
    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        if created:
            logger.info(f"Created new cart for user {request.user.username}")
        serializer = CartSerializer(cart)

        logger.debug(f"User {request.user.username} fetched their cart")
        return Response(serializer.data)

    @extend_schema(
        tags=["Cart"],
        summary="Clear cart",
        description="Removes all items from the authenticated user's cart.",
        responses={
            204: OpenApiResponse(description="Cart cleared."),
            401: RESPONSE_401,
            404: OpenApiResponse(description="User has no cart yet."),
        },
    )
    def delete(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()

        logger.info(f"User {request.user.username} cleared their cart")
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemAddAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Cart"],
        summary="Add item to cart",
        description="Adds a book to the cart. The book must be in stock and not already in the cart "
                    "(use PATCH on the item to change quantity).",
        request=CartItemWriteSerializer,
        responses={
            201: CartItemReadSerializer,
            400: OpenApiResponse(description="Invalid data, book out of stock, unknown book id, or book already in cart."),
            401: RESPONSE_401,
        },
        examples=[OpenApiExample(
            "Add book",
            value={"book": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "quantity": 2},
            request_only=True,
        )],
    )
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

    @extend_schema(
        tags=["Cart"],
        summary="Update item quantity",
        request=CartItemUpdateSerializer,
        responses={
            200: CartItemReadSerializer,
            400: RESPONSE_400,
            401: RESPONSE_401,
            404: OpenApiResponse(description="Cart or item with this book_id not found."),
        },
        examples=[OpenApiExample("Set quantity", value={"quantity": 5}, request_only=True)],
    )
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

    @extend_schema(
        tags=["Cart"],
        summary="Remove item from cart",
        responses={
            204: OpenApiResponse(description="Item removed."),
            401: RESPONSE_401,
            404: OpenApiResponse(description="Cart or item with this book_id not found."),
        },
    )
    def delete(self, request, book_id):
        cart_item = self.get_object(request, book_id)
        book_title = cart_item.book.title
        cart_item.delete()

        logger.info(f"User {request.user.username} removed {book_title} from cart")
        return Response(status=status.HTTP_204_NO_CONTENT)
