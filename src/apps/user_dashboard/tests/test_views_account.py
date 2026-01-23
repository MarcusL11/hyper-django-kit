import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from django.urls import reverse
from allauth.account.models import EmailAddress


@pytest.mark.django_db
class TestAccountProfile:
    """Tests for account_profile view."""

    def test_requires_login(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse("user_dashboard:account_profile")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_get_returns_200(self, client, user):
        """Authenticated GET request should return 200."""
        client.force_login(user)
        url = reverse("user_dashboard:account_profile")
        response = client.get(url)
        assert response.status_code == 200

    def test_get_context_has_form(self, client, user):
        """Context should contain profile_form."""
        client.force_login(user)
        url = reverse("user_dashboard:account_profile")
        response = client.get(url)
        assert "profile_form" in response.context

    def test_post_valid_data_redirects(self, client, user):
        """POST with valid data should redirect to account_profile."""
        client.force_login(user)
        url = reverse("user_dashboard:account_profile")
        data = {
            "first_name": "John",
            "last_name": "Doe",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == url

    def test_post_valid_data_saves(self, client, user):
        """POST with valid data should update user fields."""
        client.force_login(user)
        url = reverse("user_dashboard:account_profile")
        data = {
            "first_name": "John",
            "last_name": "Doe",
        }
        client.post(url, data)
        user.refresh_from_db()
        assert user.first_name == "John"
        assert user.last_name == "Doe"

    def test_post_invalid_data_returns_200(self, client, user):
        """POST with invalid data should return 200 with form errors."""
        client.force_login(user)
        url = reverse("user_dashboard:account_profile")
        data = {
            "first_name": "123",  # Invalid: contains digits
            "last_name": "456",
        }
        response = client.post(url, data)
        assert response.status_code == 200
        assert "profile_form" in response.context
        assert response.context["profile_form"].errors

    def test_post_adds_success_message(self, client, user):
        """Valid POST should add success message."""
        client.force_login(user)
        url = reverse("user_dashboard:account_profile")
        data = {
            "first_name": "John",
            "last_name": "Doe",
        }
        response = client.post(url, data, follow=True)
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "success" in messages[0].tags


@pytest.mark.django_db
class TestAccountEmail:
    """Tests for account_email view."""

    def test_requires_login(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse("user_dashboard:account_email")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_get_returns_200(self, client, user):
        """Authenticated GET request should return 200."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email")
        response = client.get(url)
        assert response.status_code == 200

    def test_get_context_has_email_addresses(self, client, user, email_address):
        """Context should contain email_addresses and add_form."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email")
        response = client.get(url)
        assert "email_addresses" in response.context
        assert "add_form" in response.context

    @patch("apps.user_dashboard.views.AddEmailForm")
    def test_post_valid_email(self, mock_form_class, client, user):
        """POST with valid email should re-render page."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email")

        # Mock form instance
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form_class.return_value = mock_form

        data = {"email": "newemail@example.com"}
        response = client.post(url, data)

        assert response.status_code == 200
        mock_form.is_valid.assert_called_once()
        mock_form.save.assert_called_once()

    def test_post_invalid_email(self, client, user):
        """POST with invalid email should show form errors."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email")
        data = {"email": "invalid-email"}
        response = client.post(url, data)
        assert response.status_code == 200
        assert "add_form" in response.context
        assert response.context["add_form"].errors


@pytest.mark.django_db
class TestAccountEmailMakePrimary:
    """Tests for account_email_make_primary view."""

    def test_requires_login(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse("user_dashboard:account_email_make_primary")
        response = client.post(url, {"email_id": 1})
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_requires_post(self, client, user):
        """GET request should return 405."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email_make_primary")
        response = client.get(url)
        assert response.status_code == 405

    def test_makes_email_primary(self, client, user, email_address, secondary_email):
        """POST with email_id should make email primary."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email_make_primary")

        # Ensure secondary email exists and is not primary
        assert not secondary_email.primary

        data = {"email_id": secondary_email.id}
        response = client.post(url, data)

        # Check response is DatastarResponse (StreamingHttpResponse)
        assert response.status_code == 200
        assert hasattr(response, "streaming")

        # Verify email is now primary
        secondary_email.refresh_from_db()
        assert secondary_email.primary

    def test_nonexistent_email_returns_404(self, client, user):
        """POST with non-existent email_id should return 404."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email_make_primary")
        data = {"email_id": 99999}
        response = client.post(url, data)
        assert response.status_code == 404


@pytest.mark.django_db
class TestAccountEmailRemove:
    """Tests for account_email_remove view."""

    def test_requires_login(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse("user_dashboard:account_email_remove")
        response = client.post(url, {"email_id": 1})
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_requires_post(self, client, user):
        """GET request should return 405."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email_remove")
        response = client.get(url)
        assert response.status_code == 405

    def test_removes_non_primary_email(self, client, user, email_address, secondary_email):
        """POST should remove non-primary email."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email_remove")

        secondary_email_id = secondary_email.id
        data = {"email_id": secondary_email_id}
        response = client.post(url, data)

        assert response.status_code == 200
        assert not EmailAddress.objects.filter(id=secondary_email_id).exists()

    def test_cannot_remove_primary_email(self, client, user, email_address):
        """POST to remove primary email should show error and not delete."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email_remove")

        primary_email_id = email_address.id
        data = {"email_id": primary_email_id}
        response = client.post(url, data, follow=True)

        # Email should still exist
        assert EmailAddress.objects.filter(id=primary_email_id).exists()

        # Should have error message
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "error" in messages[0].tags

    def test_nonexistent_email_shows_error(self, client, user):
        """POST with non-existent email_id should show error message."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email_remove")
        data = {"email_id": 99999}
        response = client.post(url, data, follow=True)

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "error" in messages[0].tags


@pytest.mark.django_db
class TestAccountEmailResendVerification:
    """Tests for account_email_resend_verification view."""

    def test_requires_login(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse("user_dashboard:account_email_resend_verification")
        response = client.post(url, {"email_id": 1})
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_requires_post(self, client, user):
        """GET request should return 405."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email_resend_verification")
        response = client.get(url)
        assert response.status_code == 405

    @patch("allauth.account.models.EmailAddress.send_confirmation")
    def test_resends_for_unverified_email(self, mock_send_confirmation, client, user):
        """POST for unverified email should send confirmation."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email_resend_verification")

        # Create unverified email
        unverified_email = EmailAddress.objects.create(
            user=user,
            email="unverified@example.com",
            verified=False,
            primary=False
        )

        data = {"email_id": unverified_email.id}
        response = client.post(url, data, follow=True)

        mock_send_confirmation.assert_called_once()
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "success" in messages[0].tags

    def test_already_verified_shows_info(self, client, user, email_address):
        """POST for already verified email should show info message."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email_resend_verification")

        # email_address fixture is verified by default
        assert email_address.verified

        data = {"email_id": email_address.id}
        response = client.post(url, data, follow=True)

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "info" in messages[0].tags

    def test_nonexistent_email_shows_error(self, client, user):
        """POST with non-existent email_id should show error message."""
        client.force_login(user)
        url = reverse("user_dashboard:account_email_resend_verification")
        data = {"email_id": 99999}
        response = client.post(url, data, follow=True)

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "error" in messages[0].tags


@pytest.mark.django_db
class TestAccountPassword:
    """Tests for account_password view."""

    def test_requires_login(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse("user_dashboard:account_password")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_get_returns_200(self, client, user):
        """Authenticated GET request should return 200."""
        client.force_login(user)
        url = reverse("user_dashboard:account_password")
        response = client.get(url)
        assert response.status_code == 200

    def test_get_context_has_form(self, client, user):
        """Context should contain password_form."""
        client.force_login(user)
        url = reverse("user_dashboard:account_password")
        response = client.get(url)
        assert "password_form" in response.context

    @patch("apps.user_dashboard.views.ChangePasswordForm")
    def test_post_valid_password_redirects_to_login(self, mock_form_class, client, user):
        """POST with valid password should redirect to login."""
        client.force_login(user)
        url = reverse("user_dashboard:account_password")

        # Mock form instance
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form_class.return_value = mock_form

        data = {
            "oldpassword": "oldpass123",
            "password1": "newpass123",
            "password2": "newpass123"
        }
        response = client.post(url, data)

        assert response.status_code == 302
        assert response.url == reverse("account_login")
        mock_form.save.assert_called_once()

    @patch("apps.user_dashboard.views.ChangePasswordForm")
    def test_post_invalid_shows_errors(self, mock_form_class, client, user):
        """POST with invalid data should re-render with errors."""
        client.force_login(user)
        url = reverse("user_dashboard:account_password")

        # Mock form instance as invalid
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_errors = MagicMock()
        mock_errors.as_json.return_value = '{"password1": [{"message": "Passwords do not match"}]}'
        mock_form.errors = mock_errors
        mock_form_class.return_value = mock_form

        data = {
            "oldpassword": "oldpass123",
            "password1": "newpass123",
            "password2": "different123"
        }
        response = client.post(url, data)

        assert response.status_code == 200
        assert "password_form" in response.context


@pytest.mark.django_db
class TestAccountSessions:
    """Tests for account_sessions view."""

    def test_requires_login(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse("user_dashboard:account_sessions")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_get_returns_200(self, client, user):
        """Authenticated GET request should return 200."""
        client.force_login(user)
        url = reverse("user_dashboard:account_sessions")
        response = client.get(url)
        assert response.status_code == 200

    @patch("apps.user_dashboard.views.UserSession.objects.purge_and_list")
    def test_get_shows_sessions(self, mock_purge_and_list, client, user):
        """GET should display user sessions."""
        client.force_login(user)
        url = reverse("user_dashboard:account_sessions")

        # Mock sessions
        mock_sessions = [
            MagicMock(session_key="session1"),
            MagicMock(session_key="session2")
        ]
        mock_purge_and_list.return_value = mock_sessions

        response = client.get(url)

        assert response.status_code == 200
        mock_purge_and_list.assert_called_once_with(user)
        assert "sessions" in response.context

    @patch("apps.user_dashboard.views.ManageUserSessionsForm")
    def test_post_valid_signs_out_sessions(self, mock_form_class, client, user):
        """POST with valid data should sign out sessions."""
        client.force_login(user)
        url = reverse("user_dashboard:account_sessions")

        # Mock form instance
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form_class.return_value = mock_form

        data = {"sessions": ["session1", "session2"]}
        response = client.post(url, data, follow=True)

        mock_form.is_valid.assert_called_once()
        mock_form.save.assert_called_once()
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "success" in messages[0].tags

    @patch("apps.user_dashboard.views.ManageUserSessionsForm")
    def test_post_invalid_shows_error(self, mock_form_class, client, user):
        """POST with invalid data should show error."""
        client.force_login(user)
        url = reverse("user_dashboard:account_sessions")

        # Mock form instance as invalid
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_errors = MagicMock()
        mock_errors.as_json.return_value = '{"sessions": [{"message": "Invalid session"}]}'
        mock_form.errors = mock_errors
        mock_form_class.return_value = mock_form

        data = {"sessions": ["invalid_session"]}
        response = client.post(url, data, follow=True)

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "error" in messages[0].tags


@pytest.mark.django_db
class TestAccountProfileDeleteImage:
    """Tests for account_profile_delete_image view."""

    def test_requires_login(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse("user_dashboard:account_profile_delete_image")
        response = client.post(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_requires_post(self, client, user):
        """GET request should return 405."""
        client.force_login(user)
        url = reverse("user_dashboard:account_profile_delete_image")
        response = client.get(url)
        assert response.status_code == 405

    def test_deletes_existing_image(self, client, user):
        """POST should delete existing profile image."""
        client.force_login(user)
        url = reverse("user_dashboard:account_profile_delete_image")

        # Patch the profile_image attribute on the user instance retrieved by the view
        mock_image = MagicMock()
        mock_image.__bool__ = lambda self: True  # Make it truthy

        with patch.object(type(user), "profile_image", new_callable=PropertyMock, return_value=mock_image):
            response = client.post(url, follow=True)

        assert response.status_code == 200
        mock_image.delete.assert_called_once_with(save=True)
        assert response.redirect_chain[0][0] == reverse("user_dashboard:account_profile")

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "success" in messages[0].tags

    def test_no_image_shows_info(self, client, user):
        """POST without profile image should show info message."""
        client.force_login(user)
        url = reverse("user_dashboard:account_profile_delete_image")

        # Ensure user has no profile_image
        user.profile_image = None
        user.save()

        response = client.post(url, follow=True)

        assert response.status_code == 200
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "info" in messages[0].tags
