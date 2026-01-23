import pytest
from unittest.mock import patch
from django.urls import reverse


@pytest.mark.django_db
class TestIndexView:
    """Tests for the user_dashboard index view."""

    def test_requires_login(self, client):
        """Anonymous users should be redirected to login page."""
        url = reverse("user_dashboard:index")
        response = client.get(url)

        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_returns_200_for_authenticated_user(self, client, user):
        """Authenticated users should receive a 200 response."""
        client.force_login(user)
        url = reverse("user_dashboard:index")
        response = client.get(url)

        assert response.status_code == 200

    def test_uses_correct_template(self, client, user):
        """View should render the correct template."""
        client.force_login(user)
        url = reverse("user_dashboard:index")
        response = client.get(url)

        template_names = [t.name for t in response.templates]
        assert "user_dashboard/index.html" in template_names


@pytest.mark.django_db
class TestStoreUserSidebarStateView:
    """Tests for the store_user_sidebar_state view."""

    def test_requires_login(self, client):
        """Anonymous users should be redirected to login page."""
        url = reverse("user_dashboard:store_user_sidebar_state")
        response = client.post(url)

        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_requires_post(self, client, user):
        """View should only accept POST requests."""
        client.force_login(user)
        url = reverse("user_dashboard:store_user_sidebar_state")
        response = client.get(url)

        assert response.status_code == 405

    @patch("apps.user_dashboard.views.read_signals")
    def test_stores_signals_in_session(self, mock_read_signals, client, user):
        """View should store signals from request in session."""
        mock_signals = {"details_account": True}
        mock_read_signals.return_value = mock_signals

        client.force_login(user)
        url = reverse("user_dashboard:store_user_sidebar_state")
        response = client.post(url)

        # Verify read_signals was called with the request
        assert mock_read_signals.called

        # Verify the signals were stored in the session
        assert "user_sidebar_state" in client.session
        assert client.session["user_sidebar_state"] == mock_signals

    @patch("apps.user_dashboard.views.read_signals")
    def test_returns_204(self, mock_read_signals, client, user):
        """View should return 204 No Content on success."""
        mock_read_signals.return_value = {"details_account": True}

        client.force_login(user)
        url = reverse("user_dashboard:store_user_sidebar_state")
        response = client.post(url)

        assert response.status_code == 204
