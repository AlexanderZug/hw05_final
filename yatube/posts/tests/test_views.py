import tempfile
from shutil import rmtree
from typing import NamedTuple

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PageContent(NamedTuple):
    """Хранит name и шаблоны/url-путь к 2-й странице."""

    name: str
    value: str


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Moses')
        cls.group = Group.objects.create(
            slug='test-slug',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            image=cls.uploaded,
        )
        cls.names = {
            'index': PageContent(
                name=reverse('posts:index'),
                value='posts/index.html',
            ),
            'group': PageContent(
                name=reverse('posts:group_list', kwargs={
                    'slug': cls.group.slug}),
                value='posts/group_list.html',
            ),
            'post_detail': PageContent(
                name=reverse('posts:post_detail', kwargs={
                    'post_id': cls.post.pk}),
                value='posts/post_detail.html',
            ),
            'profile': PageContent(
                name=reverse('posts:profile', kwargs={
                    'username': cls.post.author.username}),
                value='posts/profile.html'
            ),
            'create': PageContent(
                name=reverse('posts:post_create'),
                value='posts/create_post.html',
            ),
            'post_edit': PageContent(
                name=reverse('posts:post_edit', kwargs={
                    'post_id': cls.post.pk}),
                value='posts/create_post.html'
            ),
        }
        cls.form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

    @classmethod
    def tearDownClass(cls):
        rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(
            PostsViewTests.user)
        cache.clear()

    def test_views_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for names_and_template in self.names.values():
            with self.subTest(template=names_and_template.name):
                response = self.authorized_client.get(names_and_template.name)
                self.assertTemplateUsed(response, names_and_template.value)

    def test_index_show_correct_context(self):
        """
        Шаблоны index, post_detail
        сформирован с правильным контекстом.
        """
        posts = 'post'
        context = {
            self.names['index'].name: PostsViewTests.post,
            self.names['post_detail'].name: PostsViewTests.post,
        }
        self.content_test(context, posts)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        group = 'group'
        context = {
            self.names['group'].name: PostsViewTests.group,
        }
        self.content_test(context, group)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        author = 'author'
        context = {
            self.names['profile'].name: PostsViewTests.post.author,
        }
        self.content_test(context, author)

    def content_test(self, context: dict, value: str):
        """
        Метод для обработки и верификации контента в шаблоне.
        """
        for reverse_page, object in context.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                page_object = response.context[f'{value}']
                content = {page_object: object}
                for response, expected in content.items():
                    self.assertEqual(response, expected)

    def test_post_create_show_correct_instance(self):
        """
        Проверка ожидаемых полей формы post_create.
        """
        for field, expected in self.form_fields.items():
            with self.subTest(field=field):
                response = self.authorized_client.get(
                    self.names['create'].name)
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_instance(self):
        """
        Проверка ожидаемых полей формы post_edit.
        """
        for field, expected in self.form_fields.items():
            with self.subTest(field=field):
                response = self.authorized_client.get(
                    self.names['post_edit'].name)
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)
        is_edit_true = response.context.get('is_edit')
        self.assertTrue(is_edit_true)


class PostsPaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_posts_paginator = 13
        cls.user = User.objects.create_user(username='Moses')
        cls.group = Group.objects.create(
            slug='test-slug',
        )
        cls.post = [Post.objects.create(
            text=f'Numbers: {str(i)}',
            author=cls.user,
            group=cls.group
        ) for i in range(cls.test_posts_paginator)]
        cls.paginator = {
            'index': PageContent(
                name=reverse('posts:index'),
                value='?page=2',
            ),
            'group': PageContent(
                name=reverse('posts:group_list', kwargs={
                    'slug': cls.group.slug}),
                value='?page=2',
            ),
            'profile': PageContent(
                name=reverse('posts:profile', kwargs={
                    'username': cls.user.username}),
                value='?page=2',
            ),
            'follow': PageContent(
                name=reverse('posts:follow_index'),
                value='?page=2',
            ),
        }

    def setUp(self):
        self.user_follower = User.objects.create(
            username='follower'
        )
        self.follower_client = Client()
        self.follower_client.force_login(self.user_follower)
        self.follower_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username})
        )

    def test_paginator_first_page(self):
        """
        Тестирование Paginator для index,
        profile, group_list, follow_index.
        Выводит 10 постов.
        """
        for url in self.paginator.values():
            response = self.follower_client.get(url.name)
            self.assertEqual(
                len(response.context.get('page_obj').object_list),
                settings.POSTS_PER_PAGE)

    def test_paginator_next_page(self):
        """
        Тестирование Paginator. Вывод постов на следующую страницу.
        """
        posts_number_on_next_page = (PostsPaginatorTest.test_posts_paginator
                                     - settings.POSTS_PER_PAGE)
        for url in self.paginator.values():
            response = self.follower_client.get(url.name + url.value)
            self.assertEqual(
                len(response.context.get('page_obj').object_list),
                posts_number_on_next_page)


class PostsNewPostTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Moses')
        cls.group = Group.objects.create(
            slug='test-slug',
        )
        cls.group_two = Group.objects.create(
            slug='test-slug-two',
        )
        cls.post = Post.objects.create(
            text='Пробный текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsNewPostTest.user)
        cache.clear()

    def test_new_post_index(self):
        """Новый пост появляется на главной странице."""
        response = self.authorized_client.get('/')
        self.assertContains(response, PostsNewPostTest.post.text)

    def test_new_post_list_group(self):
        """Новый пост появляется на странице группы."""
        response = self.authorized_client.get(
            f'/group/{PostsNewPostTest.post.group.slug}/')
        self.assertContains(response, PostsNewPostTest.post.text)

    def test_new_post_list_not_on_group_page(self):
        """Новый пост не содержится на странице другой группы."""
        response = self.authorized_client.get(
            f'/group/{PostsNewPostTest.group_two.slug}/')
        self.assertNotContains(response, PostsNewPostTest.post.text)

    def test_new_post_profile(self):
        """Новый пост появляется на странице автора."""
        response = self.authorized_client.get(
            f'/profile/{PostsNewPostTest.post.author.username}/')
        self.assertContains(response, PostsNewPostTest.post.text)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Moses')
        cls.post = Post.objects.create(
            text='Пробный текст',
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()

    def test_cache_index_pages(self):
        """Тест кэша на главной странице."""
        first_response = self.client.get(reverse('posts:index'))
        Post.objects.create(
            text='Другой текст',
            author=CacheTest.user,
        )
        second_response = self.client.get(reverse('posts:index'))
        self.assertEqual(
            first_response.content,
            second_response.content
        )
        cache.clear()
        response_after_cache_clear = self.client.get(reverse('posts:index'))
        self.assertNotEqual(
            first_response.content,
            response_after_cache_clear.content
        )
        cache.clear()


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='follower')
        cls.user_following = User.objects.create_user(username='following')
        cls.post = Post.objects.create(
            text='Пробный текст',
            author=cls.user_following,
        )
        cls.follow = Follow.objects.create(user=cls.user_follower,
                                           author=cls.user_following)

    def setUp(self):
        self.authorized_client_follower = Client()
        self.authorized_client_following = Client()
        self.authorized_client_follower.force_login(
            FollowTest.user_follower)
        self.authorized_client_following.force_login(
            FollowTest.user_following)

    def test_follow(self):
        """Пользователь может подписаться на автора."""
        self.authorized_client_follower.get(
            reverse('posts:profile_follow',
                    args=(self.user_following.username,)))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """Пользователь может отписаться на автора."""
        self.authorized_client_follower.get(
            reverse('posts:profile_follow', kwargs={
                'username': self.user_following.username
            }))
        self.authorized_client_follower.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': self.user_following.username
            }))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_authors_posts_appear_on_subscribers_page(self):
        """Пост автора появляется на странице подписчиков."""
        response = self.authorized_client_follower.get(
            reverse('posts:follow_index'))
        post_text = response.context["page_obj"][0].text
        self.assertEqual(post_text, FollowTest.post.text)
