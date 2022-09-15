import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user_test')
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test',
            description='тестовое описание',
        )
        cls.new_group = Group.objects.create(
            title='описание групп',
            slug='test_1',
            description='тестовое описание групп',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small_gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовое сообщение',
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Проверка на создание записи и валидность формы."""
        reverse_url = reverse('posts:post_create')
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Простое сообщение',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse_url,
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertFalse(
            Post.objects.filter(
                text='Простое сообщение',
                group=self.group,
                author=self.post.author,
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edit(self):
        """Редактирование поста доступно авторизованному пользователю"""
        reverse_url = reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}
        )
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='big.gif',
            content=small_gif,
            content_type='image/gif'
        )
        from_data = {
            'text': 'Измененённое сообщение',
            'group': self.new_group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse_url,
            data=from_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text='Измененённое сообщение',
                group=self.new_group.id,
                image='posts/big.gif'
            ).exists()
        )

    def test_guest_cant_edit_post(self):
        """Редактирование поста не авторизированным пользователем."""
        reverse_url = reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}
        )
        posts_count = Post.objects.count()
        from_data = {
            'text': 'Измененное сообщение',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse_url,
            data=from_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(text='Измененённое сообщение').exists()
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
