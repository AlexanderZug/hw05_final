import random
import string
from http import HTTPStatus
from typing import NamedTuple

from django.conf.urls import handler500
from django.http import request
from django.test import Client, TestCase

from ..models import Comment, Group, Post, User
from ...yatube import settings


class Url(NamedTuple):
    """Хранит связку урл и шаблона."""

    url: str
    template: str


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Moses')
        cls.user_not_author = User.objects.create_user(username='Not_Moses')
        cls.group = Group.objects.create(
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
        )
        cls.commit = Comment.objects.create(
            author=cls.user,
            post_id=cls.post.pk,
            text='Коммит',
        )
        cls.public_urls = {
            'index': Url(
                url='/',
                template='posts/index.html'
            ),
            'group': Url(
                url=f'/group/{cls.group.slug}/',
                template='posts/group_list.html'),
            'post_detail': Url(
                url=f'/posts/{cls.post.pk}/',
                template='posts/post_detail.html'),
            'profile': Url(
                url=f'/profile/{cls.post.author}/',
                template='posts/profile.html'),
        }
        cls.private_urls = {
            'create': Url(
                url='/create/',
                template='posts/create_post.html'
            ),
            'post_edit': Url(
                url=f'/posts/{cls.post.pk}/edit/',
                template='posts/create_post.html'),
        }
        cls.errors = {
            'error_404': Url(
                url='/some_url/',
                template='core/404.html',
            )
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_not_author = Client()
        self.authorized_client.force_login(PostsURLTests.user)
        self.authorized_client_not_author.force_login(
            PostsURLTests.user_not_author)

    def test_urls_exist_at_desired_location_for_authorized_client(self):
        """
        Проверка доступности url для авторизированного пользователя.
        """
        all_url = {**self.public_urls, **self.private_urls}
        for url in all_url.values():
            with self.subTest(url=url.url):
                status_code = self.authorized_client.get(url.url).status_code
                self.assertEqual(status_code, HTTPStatus.OK)

    def test_urls_exist_at_desired_location_guest_client(self):
        """
        Проверка недоступности create_post и post_edit
        url для неавторизованного пользователя.
        """
        for url in self.private_urls.values():
            with self.subTest(url=url.url):
                status_code = self.guest_client.get(url.url).status_code
                self.assertEqual(status_code, HTTPStatus.FOUND)

    def test_urls_exist_at_desired_location_not_author(self):
        """
        Проверка недоступности редактирования поста
        для пользователя, не являющегося автором.
        """
        status_code = self.authorized_client_not_author.get(
            self.private_urls['post_edit'].url).status_code
        self.assertEqual(status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        all_templates = {**self.private_urls, **self.public_urls}
        for page in all_templates.values():
            with self.subTest(page=page.url):
                response = self.authorized_client.get(page.url)
                self.assertTemplateUsed(response, page.template)

    def test_unexisting_page(self):
        """Несуществующая страница вернет ошибку пользователю."""
        letters = string.ascii_lowercase
        response = self.guest_client.get(
            f'/{"/".join(random.choice(letters) for _ in range(10))}/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, self.errors['error_404'].template)
