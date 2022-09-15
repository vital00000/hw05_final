from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(str(self.post), self.post.text[:15])
        self.assertEqual(str(self.group), self.group.title)

    def test_post_model_verbose_name(self):
        """Проверяем verbose_name"""
        expected_value_verbose = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикаций',
            'author': 'Автор поста',
            'group': 'Группа поста',
        }

        for field, expected_value in expected_value_verbose.items():
            with self.subTest(field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value,
                )

    def test_post_model_help_text(self):
        """Проверяем verbose_name"""
        expected_value_help = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }

        for field, expected_value in expected_value_help.items():
            with self.subTest(field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value,
                )
