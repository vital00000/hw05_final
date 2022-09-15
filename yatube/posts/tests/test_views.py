from django import forms

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
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
            text='Текст поста',
            author=cls.user,
            group=cls.group,
            pub_date='Дата публикации',
            image=cls.uploaded,
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_post = Client()
        self.author_post.force_login(self.user)
        self.authorized_user = User.objects.create_user(username='не автор!')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized_user)
        self.subscribed_user = Client()
        self.subscribed_user.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """1_URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/create_post.html',
            reverse('posts:post_create'):
                'posts/create_post.html'
        }

        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.author_post.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_list(self):
        response = self.authorized_client.get(reverse('posts:index'))
        index = list(response.context['page_obj'])
        self.assertEqual(index[0].image, self.post.image)

    def test_group_list_page_list(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={
                'slug': self.group.slug
            }))
        group_list = list(response.context['page_obj'])
        self.assertEqual(group_list[0].image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id
                    }))
        context = response.context
        post = context['post']
        self.assertEqual(post, self.post)
        self.assertEqual(post.image, self.post.image)

    def test_edit_uses_correct_form(self):
        response = self.author_post.get(reverse(
            'posts:post_edit', kwargs={
                'post_id': self.post.id}
        ))
        form_fields = {
            'text': forms.fields.CharField,
        }
        for field_name, type in form_fields.items():
            with self.subTest(key=field_name):
                form_fields = response.context['form'].fields[field_name]
                self.assertIsInstance(form_fields, type)

    def test_edit_post_uses_is_edit(self):
        response = self.author_post.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        context = response.context
        is_edit = context['is_edit']
        self.assertIs(is_edit, True)

    def test_post_create(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for field_name, field_type in form_fields.items():
            with self.subTest(field_name=field_name):
                form_field = response.context['form'].fields[field_name]
                self.assertIsInstance(form_field, field_type)

    def test_post_not_in_right_places(self):
        response_index = self.authorized_client.get(reverse('posts:index'))
        response_group_list = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug})
        )
        response_profile = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        context_index = response_index.context['page_obj'][0]
        context_group = response_group_list.context['page_obj'][0]
        context_profile = response_profile.context['page_obj'][0]
        self.assertNotEqual(PostViewsTest, context_index)
        self.assertNotEqual(PostViewsTest, context_group)
        self.assertNotEqual(PostViewsTest, context_profile)

    def test_post_in_places_goup_list(self):
        new_post_1 = Post.objects.create(
            group=self.group,
            text='Что-то новое',
            author=self.user,
        )
        response_new_list = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        context_group = response_new_list.context['group']
        self.assertEqual(context_group, new_post_1.group)

    def test_post_in_places(self):
        new_post = Post.objects.create(
            text='Новый Пост',
            author=self.user,
            image=self.uploaded,
        )
        response_new_profile = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user}))
        context_profile = response_new_profile.context['page_obj'][0]
        self.assertEqual(new_post, context_profile)
        self.assertEqual(context_profile.image, new_post.image)


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.new_user = User.objects.create_user(username='vi')
        cls.post_user = Client()
        cls.authorized_client = Client()
        cls.authorized_user = Client()
        cls.post_user.force_login(cls.new_user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.new_user,
            text='Текст',
            group=cls.group
        )

        NUMBER: int = 20
        posts = []
        for i in range(NUMBER):
            posts.append(
                Post(
                    author=cls.new_user,
                    text=f'my test{i}',
                    group=cls.group
                )
            )
            Post.objects.bulk_create(posts)

    def test_first_page_contains_ten_records(self):
        """12 Паджинатор проверяет первую страницу"""
        paginator_pages = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.new_user})
        }
        for address in paginator_pages:
            with self.subTest(address=address):
                response = self.post_user.get((address) + '?page=1')
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """13 Паджинатор проверяет вторую  страницу"""
        paginator_pages = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.new_user})
        }
        for address in paginator_pages:
            with self.subTest(address=address):
                response = self.post_user.get((address) + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_comment_available(self):
        'Leave comment can just authorized_client'
        form_data = {
            'text': 'Тестовый комметарий'
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        response = self.authorized_user.get(
            reverse(
                'posts:post_detail', kwargs={'post_id': 1}
            )
        )
        self.assertTrue(response, 'Тестовый комметарий')


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='Автор постов'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_cache = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.user
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, post_cache)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_post = response_new.content
        self.assertNotEqual(old_posts, new_post)
        cache.clear()


class CoreTestClass(TestCase):
    """Тест на проверку 404 ошибки"""
    def test_page_not_found(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')


class FollowersViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='follower', password='284'
        )
        cls.subscribed_user = Client()
        cls.subscribed_user.force_login(cls.user)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.follower = Client()
        cls.follower.force_login(cls.user)
        cls.user2 = User.objects.create_user(
            username='author', password='482'
        )
        cls.author = Client()
        cls.author.force_login(cls.user2)
        cls.post = Post.objects.create(
            text='Test_text',
            author=cls.user2,
        )

    def test_follower_can_follow(self):
        """
        Авторизованный пользователь может подписываться
        на других пользоваталей.
        """
        self.follower.get(
            reverse('posts:profile_follow', kwargs={
                'username': self.user2.username}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user2).exists()
        )
        self.assertEqual(Follow.objects.count(), 1)

    def test_new_post_appears_for_subscribed_users_only(self):
        """Новая запись появляется в ленте подписчиков."""
        Follow.objects.create(
            user=self.user,
            author=self.user2,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        objects = list(response.context['page_obj'])
        self.assertIn(objects[0].text, self.post.text)

    def test_content_for_follower_and_unfollow(self):
        """Тест: Подписанный пользователь видит посты и может отписаться."""
        self.follower = Follow.objects.create(
            user=self.user, author=self.user2
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)
        self.follower.delete()
        response1 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotEqual(response.content, response1.content)
