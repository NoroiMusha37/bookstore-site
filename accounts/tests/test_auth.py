import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestAuthAndProfile:
    def test_user_registration(self, api_client):
        url = reverse("accounts:register")
        data = {
            "username": "newuser",
            "password": "StrongPassword123!",
            "password_check": "StrongPassword123!",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "phone": "+1234567890"
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username="newuser").exists()


    def test_get_profile(self, auth_client, user):
        url = reverse("user-profile")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == user.username
        assert response.data["email"] == user.email

    def test_update_profile(self, auth_client, user):
        url = reverse("user-profile")
        data = {
            "first_name": "Updated",
            "phone": "+999999999"
        }
        response = auth_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        user.refresh_from_db()
        assert user.first_name == "Updated"
        assert user.phone == "+999999999"

    def test_get_profile_unauthenticated(self, api_client):
        url = reverse("user-profile")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
