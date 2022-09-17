import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User=get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDiA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user_test')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовое сообщение',
            group=cls.group,
            image=None,
        )


    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        
    def test_post_create(self):
        """Проверка на создание записи и валидность формы."""
        reverse_url = reverse('posts:post_create')
        posts_befor_postn = Post.objects.count()
        form_data = {
            'text': 'Простое сообщение',
            'group': self.group.id,
            'image': self.uploaded
        }
        self.authorized_client.post(
            reverse_url,
            data=form_data,
            follow=True
        )
        self.assertEqual(posts_befor_postn + 1, Post.objects.count())
        post_ddt = Post.objects.latest(
            'pub_date'
        )
        self.assertEqual(post_ddt.text, form_data['text'])
        self.assertEqual(post_ddt.group.id, form_data['group'])
        self.assertEqual(
            list(post_ddt.image.chunks()), list(form_data['image'].chunks())
        )


    def test_post_edit(self):
        """Редактирование поста доступно авторизованному пользователю"""
        reverse_url = reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Измененённое сообщение',
            'group': self.new_group.id,
            'image': self.uploaded,
        }
        self.authorized_client.post(
            reverse_url,
            data=form_data,
            follow=True
        )
        self.assertEqual(posts_count, Post.objects.count())
        post_now = Post.objects.get(
            id=self.post.id
        )
        self.assertEqual(post_now.text, form_data['text'])
        self.assertEqual(post_now.group.id, form_data['group'])
        self.assertEqual(
            list(post_now.image.chunks()), list(form_data['image'].chunks())
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
