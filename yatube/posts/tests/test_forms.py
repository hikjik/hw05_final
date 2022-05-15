import os
import shutil
import tempfile

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(username="user")
        cls.group = Group.objects.create(
            title="title",
            slug="slug",
            description="description",
        )
        cls.post = Post.objects.create(
            author=cls.post_author,
            group=cls.group,
            text="text",
        )
        cls.test_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

        self.user = User.objects.create_user(username="auth user")
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

        self.post_author_client = Client()
        self.post_author_client.force_login(PostFormTests.post_author)

    def test_create_post_authorized_client(self):
        posts_count = Post.objects.count()
        group = PostFormTests.group
        uploaded = SimpleUploadedFile(
            name="test.gif",
            content=PostFormTests.test_gif,
            content_type="image/gif",
        )

        form_data = {
            "text": "Тестовый текст",
            "group": group.id,
            "image": uploaded,
        }

        response = self.auth_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={"username": self.user.username}),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=group,
                text=form_data["text"],
                image=os.path.join("posts", uploaded.name),
            ).exists()
        )

    def test_create_post_redirect_anonymous(self):
        form_data = {
            "text": "Тестовый текст",
            "group": PostFormTests.group.id,
        }
        path = reverse("posts:post_create")
        response = self.guest_client.post(path, data=form_data, follow=True)

        self.assertRedirects(
            response,
            reverse("users:login") + "?next=" + path,
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

    def test_edit_post_author_client(self):
        posts_count = Post.objects.count()
        post = PostFormTests.post
        uploaded = SimpleUploadedFile(
            name="new_test.gif",
            content=PostFormTests.test_gif,
            content_type="image/gif",
        )

        form_data = {
            "text": "Новый тестовый текст",
            "group": post.group.id,
            "image": uploaded,
        }
        response = self.post_author_client.post(
            reverse("posts:post_edit", kwargs={"post_id": post.id}),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": post.id}),
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                group=post.group,
                text=form_data["text"],
                image=os.path.join("posts", uploaded.name),
            ).exists()
        )

    def test_add_comment_anonymous(self):
        post = PostFormTests.post
        form_data = {
            "text": "Новый комментарий",
        }
        path = reverse("posts:add_comment", kwargs={"post_id": post.id})
        response = self.guest_client.post(path, data=form_data, follow=True)

        self.assertRedirects(
            response,
            reverse("users:login") + "?next=" + path,
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

    def test_add_comment_authorized(self):
        post = PostFormTests.post
        form_data = {
            "text": "Новый комментарий",
        }
        path = reverse("posts:add_comment", kwargs={"post_id": post.id})
        response = self.auth_client.post(path, data=form_data, follow=True)

        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": post.id}),
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

    def test_edit_post_redirect_anonymous(self):
        post = PostFormTests.post
        form_data = {
            "text": "Новый тестовый текст",
            "group": post.group.id,
        }
        path = reverse("posts:post_edit", kwargs={"post_id": post.id})
        response = self.guest_client.post(path, data=form_data, follow=True)

        self.assertRedirects(
            response,
            reverse("users:login") + "?next=" + path,
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

    def test_edit_post_redirect_authorized_not_author(self):
        post = PostFormTests.post
        form_data = {
            "text": "Новый тестовый текст",
            "group": post.group.id,
        }

        path = reverse("posts:post_edit", kwargs={"post_id": post.id})
        response = self.auth_client.post(path, data=form_data, follow=True)

        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": post.id}),
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )
