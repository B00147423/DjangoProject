from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .forms import ChangeEmailForm
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from unittest.mock import patch
User = get_user_model()

class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(username='adminuser', email='admin@example.com', password='adminpass123')
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)

class ChangeEmailFormTests(TestCase):
    def test_change_email_form_valid(self):
        form = ChangeEmailForm(data={'email': 'newemail@example.com'})
        self.assertTrue(form.is_valid())

    def test_change_email_form_invalid(self):
        form = ChangeEmailForm(data={'email': 'invalidemail'})
        self.assertFalse(form.is_valid())

class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_profile_view(self):
        response = self.client.get(reverse('user:profile_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Update Profile")

class PasswordChangeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='oldpass123')
        self.client.login(username='testuser', password='oldpass123')

    def test_password_change(self):
        response = self.client.post(reverse('user:change_password'), {
            'old_password': 'oldpass123',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123'
        })
        self.assertRedirects(response, reverse('user:settings'))

    def test_password_change_invalid(self):
        response = self.client.post(reverse('user:change_password'), {
            'old_password': 'wrongpass',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123'
        })
        self.assertContains(response, "Your old password was entered incorrectly.")

class EmailVerificationTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

    def test_email_verification(self):
        # Patch token validation to always return True during the test
        with patch("django.contrib.auth.tokens.default_token_generator.check_token", return_value=True):
            response = self.client.get(reverse("user:verify_email", args=[self.uid, self.token]))
            self.assertRedirects(response, reverse("user:dashboard"))

    def test_email_verification_invalid_token(self):
        # Test invalid token case
        response = self.client.get(reverse("user:verify_email", args=[self.uid, "invalid-token"]))
        self.assertRedirects(response, reverse("user:auth_page"), fetch_redirect_response=False)
