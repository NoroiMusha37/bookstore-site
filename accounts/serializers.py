from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name",
            "last_name", "phone", "is_staff"
        ]
        read_only_fields = ["id", "username", "is_staff"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    password_check = serializers.CharField(write_only=True, max_length=128)
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="A user with this email already exists."
            )
        ]
    )
    phone = serializers.CharField(
        min_length=7, max_length=20, required=False, allow_blank=True
    )

    class Meta:
        model = User
        fields = [
            "username", "email", "first_name", "last_name",
            "password", "password_check", "phone"
        ]

    def validate(self, data):
        password = data.get("password")
        password_check = data.pop("password_check")

        if password and password_check and password != password_check:
            raise serializers.ValidationError(
                {"password_check": "Passwords do not match."}
            )

        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                raise serializers.ValidationError({"password": list(e.messages)})

        return data

    def validate_phone(self, value):
        if value:
            stripped = value.strip()
            if not stripped or not any(char.isdigit() for char in stripped):
                raise serializers.ValidationError(
                    "Phone number must contain actual digits."
                )
            if not all(char.isdigit() or char in "+-() " for char in value):
                raise serializers.ValidationError(
                    "Please enter a valid phone number."
                )
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, min_length=8, max_length=128, required=False
    )
    email = serializers.EmailField(
        required=False,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="A user with this email already exists."
            )
        ]
    )
    phone = serializers.CharField(
        min_length=7, max_length=20, required=False, allow_blank=True
    )

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "phone"]

    def validate_phone(self, value):
        if value:
            stripped = value.strip()
            if not stripped or not any(char.isdigit() for char in stripped):
                raise serializers.ValidationError(
                    "Phone number must contain actual digits."
                )
            if not all(char.isdigit() or char in "+-() " for char in value):
                raise serializers.ValidationError(
                    "Please enter a valid phone number."
                )
        return value

    def validate_password(self, value):
        if value:
            try:
                validate_password(value, user=self.instance)
            except ValidationError as e:
                raise serializers.ValidationError(list(e.messages))
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
