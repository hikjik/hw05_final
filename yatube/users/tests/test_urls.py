from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

User = get_user_model()


class AuthURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

        self.user = User.objects.create_user(username="user")
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def test_signup_url_exists_at_desired_location(self):
        response = self.guest_client.get("/auth/signup/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        for path, template in {
            "/auth/signup/": "users/signup.html",
            "/auth/login/": "users/login.html",
            "/auth/password_reset/done/": "users/password_reset_done.html",
            "/auth/password_reset/": "users/password_reset_form.html",
            "/auth/password_change/done/": "users/password_change_done.html",
            "/auth/password_change/": "users/password_change_form.html",
            "/auth/reset/done/": "users/password_reset_complete.html",
            "/auth/reset/uidb64/token/": "users/password_reset_confirm.html",
            "/auth/logout/": "users/logged_out.html",
        }.items():
            with self.subTest(path=path):
                response = self.auth_client.get(path)
                self.assertTemplateUsed(response, template)
