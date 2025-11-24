from django.test import TestCase
from apps.accounts.models import CustomUser as User


class UserTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username="testuser",
            email="testuser@email.com",
        )
        cls.user.set_password("Testpass123")
        cls.user.save()

    def test_user_creation(self):
        """Test that user was created successfully"""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "testuser@email.com")

    def test_user_password(self):
        """Test that user password is set correctly"""
        self.assertTrue(self.user.check_password("Testpass123"))
