from django.test import TestCase, Client
from http import HTTPStatus


class AboutUrlTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        for path in ["/about/author/", "/about/tech/"]:
            with self.subTest(path=path):
                response = self.guest_client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_template(self):
        paths = ["/about/author/", "/about/tech/"]
        templates = ["about/author.html", "about/tech.html"]
        for path, template in zip(paths, templates):
            with self.subTest(path=path):
                response = self.guest_client.get(path)
                self.assertTemplateUsed(response, template)
