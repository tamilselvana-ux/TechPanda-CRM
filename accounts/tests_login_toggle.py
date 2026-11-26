from django.test import TestCase, Client
from django.urls import reverse


class LoginPasswordToggleTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_general_login_page_renders_password_toggle(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn('tp-password-field-wrapper', content)
        self.assertIn('tp-password-toggle-btn', content)
        self.assertIn('password_security.js', content)
        self.assertIn('<svg', content)

    def test_manager_login_page_renders_password_toggle(self):
        response = self.client.get(reverse('manager_login'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn('tp-password-field-wrapper', content)
        self.assertIn('tp-password-toggle-btn', content)
        self.assertIn('<svg', content)

    def test_admin_login_page_renders_password_toggle(self):
        response = self.client.get(reverse('admin_login'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn('tp-password-field-wrapper', content)
        self.assertIn('tp-password-toggle-btn', content)
        self.assertIn('<svg', content)

    def test_telecaller_login_page_renders_password_toggle(self):
        response = self.client.get(reverse('telecaller_login'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn('tp-password-field-wrapper', content)
        self.assertIn('tp-password-toggle-btn', content)
        self.assertIn('<svg', content)
