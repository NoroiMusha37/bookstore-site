import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserProfileUpdateSerializer
)

logger = logging.getLogger(__name__)


class RegistrationAPIView(APIView):
    @extend_schema(
        tags=["Accounts"], summary="Register a new user",
        request=UserRegistrationSerializer,
        responses={201: UserSerializer, 400: OpenApiResponse(description="Invalid data.")},
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            logger.info(f"Registered user {user.username} successfully")
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )

        logger.warning(f"Failed to register user: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Accounts"], summary="Get my profile",
        responses={200: UserSerializer, 401: OpenApiResponse(description="Missing or invalid JWT access token.")},
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        logger.debug(f"User {request.user.username} fetched their profile")
        return Response(serializer.data)

    @extend_schema(
        tags=["Accounts"], summary="Update my profile",
        request=UserProfileUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Invalid data."),
            401: OpenApiResponse(description="Missing or invalid JWT access token."),
        },
    )
    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            response_serializer = UserSerializer(request.user)

            logger.info(f"User {request.user.username} updated their profile")
            return Response(response_serializer.data)

        logger.warning(
            f"User {request.user.username} failed to update "
            f"their profile: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
