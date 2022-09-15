from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class GroupViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.user_author = User.objects.create_user(username='NoNameAuthor')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author = Client()
        self.authorized_client.force_login(self.user)
        self.author.force_login(self.user_author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={
                    'username': self.user_author.username})
            ),
            'posts/create_post.html': (
                reverse('posts:post_edit', kwargs={'post_id': self.post.id})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            ),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': 'test-slug'})
            ),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.author.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_cant_edit_post(self):
        """Проверяет что гостевой юзер не может редактировать пост"""
        reverse_url = reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}
        )
        response = self.client.get(reverse_url)
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse_url}'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
