from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class UserDashboardTestCase(TestCase):
    def setUp(self):
        """Set up test user."""
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123"
        )

    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication."""
        url = reverse("user_dashboard:index", kwargs={"user_id": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_dashboard_shows_for_authenticated_user(self):
        """Test that authenticated user can access their dashboard."""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("user_dashboard:index", kwargs={"user_id": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_dashboard_includes_account_settings_links(self):
        """Test that dashboard includes account settings links."""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("user_dashboard:index", kwargs={"user_id": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Check for account settings section
        self.assertContains(response, "Account Settings")
        
        # Check for specific links
        self.assertContains(response, 'href="{% url \'account_email\' %}"')
        self.assertContains(response, 'href="{% url \'account_change_password\' %}"')
        self.assertContains(response, 'href="{% url \'usersessions_list\' %}"')
        
        # Check for link text
        self.assertContains(response, "Manage Email")
        self.assertContains(response, "Change Password")
        self.assertContains(response, "Manage Sessions")

    def test_dashboard_prevents_access_to_other_users(self):
        """Test that users cannot access other users' dashboards."""
        User = get_user_model()
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        
        self.client.login(username="testuser", password="testpass123")
        url = reverse("user_dashboard:index", kwargs={"user_id": other_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Forbidden


class SubscriptionManagementTestCase(TestCase):
    def setUp(self):
        """Set up test user."""
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123"
        )

    def test_subscription_management_requires_login(self):
        """Test that subscription management requires authentication."""
        url = reverse("user_dashboard:subscription_management", kwargs={"user_id": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_subscription_management_shows_for_authenticated_user(self):
        """Test that authenticated user can access their subscription management page."""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("user_dashboard:subscription_management", kwargs={"user_id": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Subscription Management")

    def test_subscription_management_shows_no_subscription_message(self):
        """Test that page shows appropriate message when user has no subscription."""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("user_dashboard:subscription_management", kwargs={"user_id": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Active Subscription")

    def test_subscription_management_prevents_access_to_other_users(self):
        """Test that users cannot access other users' subscription management."""
        User = get_user_model()
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        
        self.client.login(username="testuser", password="testpass123")
        url = reverse("user_dashboard:subscription_management", kwargs={"user_id": other_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_cancel_subscription_requires_login(self):
        """Test that cancel subscription requires authentication."""
        url = reverse("user_dashboard:cancel_subscription", kwargs={"user_id": self.user.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_cancel_subscription_without_active_subscription(self):
        """Test that canceling without active subscription shows error."""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("user_dashboard:cancel_subscription", kwargs={"user_id": self.user.id})
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        # Check that error message is displayed
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn("don't have an active subscription", str(messages[0]))

    def test_reactivate_subscription_requires_login(self):
        """Test that reactivate subscription requires authentication."""
        url = reverse("user_dashboard:reactivate_subscription", kwargs={"user_id": self.user.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_dashboard_includes_subscription_menu_link(self):
        """Test that dashboard includes subscription menu link."""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("user_dashboard:index", kwargs={"user_id": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Check for subscription link
        subscription_url = reverse("user_dashboard:subscription_management", kwargs={"user_id": self.user.id})
        self.assertContains(response, subscription_url)
        self.assertContains(response, "Subscription")
