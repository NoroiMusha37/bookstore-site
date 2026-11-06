import logging

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

    def get(self, request):
        serializer = UserSerializer(request.user)
        logger.info(f"User {request.user.username} fetched their profile")
        return Response(serializer.data)

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
            f"their name: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
