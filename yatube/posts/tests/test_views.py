import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..models import Post, Group
from ..views import POSTS_PER_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TOTAL_POSTS_COUNT = 13
        cls.POSTS_PER_PAGE = POSTS_PER_PAGE

        cls.user = User.objects.create_user(username="test user")

        cls.group = Group.objects.create(
            title="title",
            slug="slug",
            description="description",
        )

        test_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )

        cls.posts = dict()
        for i in range(cls.TOTAL_POSTS_COUNT):
            uploaded = SimpleUploadedFile(
                name="test.jpg",
                content=test_gif,
                content_type="image/gif",
            )
            post = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f"text_{i}",
                image=uploaded,
            )
            cls.posts[post.id] = post

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(PostViewTests.user)

    def tearDown(self):
        cache.clear()

    def test_pages_uses_correct_template(self):
        post = list(PostViewTests.posts.values())[0]

        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": post.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": post.author.username}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": post.id}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": post.id}
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
            reverse("posts:follow_index"): "posts/follow.html",
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        response = self.auth_client.get(reverse("posts:index"))

        self._check_post_list(response.context["page_obj"])

    def test_home_first_page_posts_count(self):
        response = self.client.get(reverse("posts:index"))

        self.assertEqual(
            len(response.context["page_obj"]),
            PostViewTests.POSTS_PER_PAGE,
        )

    def test_home_second_page_posts_count(self):
        response = self.client.get(reverse("posts:index") + "?page=2")

        self.assertEqual(
            len(response.context["page_obj"]),
            PostViewTests.TOTAL_POSTS_COUNT - PostViewTests.POSTS_PER_PAGE,
        )

    def test_home_page_uses_cache(self):
        user = PostViewTests.user

        response = self.auth_client.get(reverse("posts:index"))
        content = response.content

        Post.objects.create(text="Новый пост", author=user)

        response = self.auth_client.get(reverse("posts:index"))
        self.assertEqual(response.content, content)

        cache.clear()
        response = self.auth_client.get(reverse("posts:index"))
        self.assertNotEqual(response.content, content)

    def test_group_list_page_show_correct_context(self):
        group = PostViewTests.group
        response = self.auth_client.get(
            reverse("posts:group_list", kwargs={"slug": group.slug})
        )

        self._check_post_list(response.context["page_obj"])
        self._assert_equal_groups(response.context["group"], group)

    def test_group_list_empty_post_list_for_new_group(self):
        new_group = Group.objects.create(
            title="new title",
            slug="new_slug",
            description="new description",
        )

        response = self.auth_client.get(
            reverse("posts:group_list", kwargs={"slug": new_group.slug})
        )

        self.assertEqual(len(response.context["page_obj"]), 0)
        self._assert_equal_groups(response.context["group"], new_group)

    def test_group_list_first_page_posts_count(self):
        group = PostViewTests.group
        response = self.auth_client.get(
            reverse("posts:group_list", kwargs={"slug": group.slug})
        )

        self.assertEqual(
            len(response.context["page_obj"]),
            PostViewTests.POSTS_PER_PAGE,
        )

    def test_group_list_second_page_posts_count(self):
        group = PostViewTests.group
        response = self.auth_client.get(
            reverse(
                "posts:group_list",
                kwargs={"slug": group.slug},
            )
            + "?page=2",
        )

        self.assertEqual(
            len(response.context["page_obj"]),
            PostViewTests.TOTAL_POSTS_COUNT - PostViewTests.POSTS_PER_PAGE,
        )

    def test_profile_page_show_correct_context(self):
        user = PostViewTests.user
        response = self.auth_client.get(
            reverse("posts:profile", kwargs={"username": user.username})
        )

        self._check_post_list(response.context["page_obj"])
        self._assert_equal_users(response.context["author"], user)
        self.assertEqual(
            response.context["post_count"],
            PostViewTests.TOTAL_POSTS_COUNT,
        )

    def test_profile_page_first_page_posts_count(self):
        user = PostViewTests.user
        response = self.auth_client.get(
            reverse("posts:profile", kwargs={"username": user.username})
        )

        self.assertEqual(
            len(response.context["page_obj"]),
            PostViewTests.POSTS_PER_PAGE,
        )

    def test_profile_page_second_page_posts_count(self):
        user = PostViewTests.user
        response = self.auth_client.get(
            reverse(
                "posts:profile",
                kwargs={"username": user.username},
            )
            + "?page=2"
        )

        self.assertEqual(
            len(response.context["page_obj"]),
            PostViewTests.TOTAL_POSTS_COUNT - PostViewTests.POSTS_PER_PAGE,
        )

    def test_post_detail_page_show_correct_context(self):
        post = list(PostViewTests.posts.values())[0]

        form_fields = {
            "text": forms.fields.CharField,
        }

        response = self.auth_client.get(
            reverse("posts:post_detail", kwargs={"post_id": post.id})
        )

        self._assert_equal_posts(response.context["post"], post)
        self.assertEqual(
            response.context["post_count"], PostViewTests.TOTAL_POSTS_COUNT
        )

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        post = list(PostViewTests.posts.values())[0]
        response = self.auth_client.get(
            reverse("posts:post_edit", kwargs={"post_id": post.id})
        )

        self.assertTrue(response.context["is_edit"])

        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_show_correct_context(self):
        response = self.auth_client.get(reverse("posts:post_create"))

        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_created_post_appears_on_pages(self):
        user = PostViewTests.user
        group = PostViewTests.group

        form_data = {
            "text": "some text",
            "group": group.id,
        }
        response = self.auth_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={"username": user.username}),
        )

        paths = [
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": group.slug}),
            reverse("posts:profile", kwargs={"username": user.username}),
        ]
        for path in paths:
            response = self.auth_client.get(path)
            post = response.context["page_obj"][0]
            self.assertEqual(post.text, form_data["text"])
            self.assertEqual(post.group.id, form_data["group"])

    def test_add_comment_appears_on_post_profile_page(self):
        post = list(PostViewTests.posts.values())[0]

        form_data = {
            "text": "some comment",
        }
        response = self.auth_client.post(
            reverse("posts:add_comment", kwargs={"post_id": post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": post.id}),
        )

        comments = response.context["comments"]
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].text, form_data["text"])
        self.assertEqual(comments[0].post.id, post.id)

    def test_created_post_not_appears_on_another_group_page(self):
        new_group = Group.objects.create(
            title="another title",
            slug="another_slug",
            description="another description",
        )

        form_data = {
            "text": "some new text",
            "group": new_group.id,
        }
        response = self.auth_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:profile",
                kwargs={"username": PostViewTests.user.username},
            ),
        )

        path = reverse(
            "posts:group_list",
            kwargs={"slug": PostViewTests.group.slug},
        )
        for page in range(1, 3):
            response = self.auth_client.get(path + f"?page={page}")
            for post in response.context["page_obj"]:
                self.assertNotEqual(post.group.id, new_group.id)

    def _check_post_list(self, posts):
        for post in posts:
            self._assert_equal_posts(post, PostViewTests.posts[post.id])

    def _assert_equal_posts(self, post_first, post_second):
        self._assert_equal_users(post_first.author, post_second.author)
        self._assert_equal_groups(post_first.group, post_second.group)
        self.assertEqual(post_first.text, post_second.text)
        self._assert_equal_image(post_first.image, post_second.image)

    def _assert_equal_groups(self, group_first, group_second):
        self.assertEqual(group_first.title, group_second.title)
        self.assertEqual(group_first.slug, group_second.slug)
        self.assertEqual(group_first.description, group_second.description)

    def _assert_equal_users(self, user_first, user_second):
        self.assertEqual(user_first.username, user_second.username)

    def _assert_equal_image(self, image_first, image_second):
        if image_first and image_second:
            self.assertEqual(image_first, image_second)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CreateFollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username="author")
        cls.follower = User.objects.create(username="follower")
        cls.not_follower = User.objects.create(username="not_follower")

    def setUp(self):
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

        self.not_follower_client = Client()
        self.not_follower_client.force_login(self.not_follower)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_auth_user_can_follow_unfollow_author(self):
        author = CreateFollowTest.author
        follower = CreateFollowTest.follower

        self.assertEqual(follower.follower.count(), 0)
        self.assertEqual(author.following.count(), 0)

        self.follower_client.get(
            reverse("posts:profile_follow",
                    kwargs={"username": author.username}))

        self.assertEqual(follower.follower.count(), 1)
        self.assertEqual(author.following.count(), 1)

        self.follower_client.get(
            reverse("posts:profile_unfollow",
                    kwargs={"username": author.username}))

        self.assertEqual(follower.follower.count(), 0)
        self.assertEqual(author.following.count(), 0)

    def test_created_post_not_appears_on_not_follower_page(self):
        author = CreateFollowTest.author

        self.follower_client.get(
            reverse("posts:profile_follow",
                    kwargs={"username": author.username}))

        Post.objects.create(author=author, text="test")

        response = self.follower_client.get(reverse("posts:follow_index"))
        posts = response.context["page_obj"]
        self.assertEqual(len(posts), 1)
        for post in posts:
            self.assertEqual(author.username, post.author.username)

        response = self.not_follower_client.get(reverse("posts:follow_index"))
        posts = response.context["page_obj"]
        self.assertEqual(len(posts), 0)