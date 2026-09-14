from rest_framework import serializers

from bookstore.models import (
    Publisher,
    Author,
    Book,
    Cart,
    CartItem,
    Order,
    OrderItem
)


class PublisherListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ["id", "name", "description"]


class PublisherDetailSerializer(serializers.ModelSerializer):
    books = serializers.SerializerMethodField()

    class Meta:
        model = Publisher
        fields = ["id", "name", "description", "books"]

    def get_books(self, obj):
        return [
            {
                "id": book.id, 
                "title": book.title,
                "genre": book.genre,
                "price": book.price,
                "popularity_score": book.popularity_score
            } for book in obj.book_set.all()
        ]


class AuthorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "bio"]


class AuthorDetailSerializer(serializers.ModelSerializer):
    books = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ["id", "name", "bio", "books"]

    def get_books(self, obj):
        return [
            {
                "id": book.id, 
                "title": book.title,
                "genre": book.genre,
                "price": book.price,
                "popularity_score": book.popularity_score
            } for book in obj.book_set.all()
        ]


class BookListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.name", read_only=True)
    publisher_name = serializers.CharField(
        source="publisher.name", read_only=True
    )

    class Meta:
        model = Book
        fields = [
            "id", "title", "author", "author_name",
            "publisher", "publisher_name", "genre", "price",
            "popularity_score", "in_stock"
        ]


class BookDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.name", read_only=True)
    publisher_name = serializers.CharField(
        source="publisher.name", read_only=True
    )

    class Meta:
        model = Book
        fields = [
            "id", "title", "author", "author_name",
            "publisher", "publisher_name", "genre", "price",
            "popularity_score", "description", "publication_year",
            "pages", "in_stock"
        ]


class CartItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["id", "book", "quantity"]

    def validate_book(self, value):
        if not value.in_stock:
            raise serializers.ValidationError("This book is currently out of stock.")
        return value


class CartItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["quantity"]


class CartItemReadSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)
    book_price = serializers.DecimalField(
        source="book.price", max_digits=10, decimal_places=2, read_only=True
    )
    item_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            "id", "book", "book_title",
            "book_price", "quantity", "item_total"
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemReadSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Cart
        fields = [
            "id", "user", "created_at",
            "updated_at", "items", "total_price"
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id", "book", "book_title",
            "quantity", "unit_price", "item_total",
        ]


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "status", "total_price", "created_at"]


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "status", "total_price", "created_at", "items"]
