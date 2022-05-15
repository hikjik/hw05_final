from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment, Follow

User = get_user_model()


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )

    def test_models_have_correct_object_names(self):
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_verbose_name(self):
        group = GroupModelTest.group
        field_verboses = {
            "title": "Название группы",
            "description": "Описание группы",
            "slug": "Слаг группы",
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value
                )


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Тестовый пользователь")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
        )

    def test_models_have_correct_object_names(self):
        post = PostModelTest.post
        expected_object_name = post.text[: Post.STR_REPR_LEN]
        self.assertEqual(expected_object_name, str(post))

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            "text": "Текст поста",
            "pub_date": "Дата публикации",
            "author": "Автор",
            "group": "Группа",
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user(username="Тестовый пользователь")
        post = Post.objects.create(
            author=user,
            text="Тестовый пост",
        )
        cls.comment = Comment.objects.create(
            text="Тестовый текст",
            author=user,
            post=post,
        )

    def test_models_have_correct_object_names(self):
        comment = CommentModelTest.comment
        expected_object_name = comment.text[: Comment.STR_REPR_LEN]
        self.assertEqual(expected_object_name, str(comment))

    def test_verbose_name(self):
        comment = CommentModelTest.comment
        field_verboses = {
            "text": "Текст комментария",
            "created": "Дата комментария",
            "author": "Автор комментария",
            "post": "Комментируемый пост",
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name, expected_value
                )


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        follower = User.objects.create_user(username="Подписчик")
        author = User.objects.create_user(username="Автор")

        cls.follow = Follow.objects.create(
            user=follower,
            author=author,
        )

    def test_models_have_correct_object_names(self):
        follow = FollowModelTest.follow
        expected_object_name = (
            f"Подписчик: {follow.user.username}, "
            f"Автор: {follow.author.username}")
        self.assertEqual(expected_object_name, str(follow))

    def test_verbose_name(self):
        follow = FollowModelTest.follow
        field_verboses = {
            "user": "Подписчик",
            "author": "Автор",
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    follow._meta.get_field(field).verbose_name, expected_value
                )
