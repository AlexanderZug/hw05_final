from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import User


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Moses',
                                            email='todo@yandex.ru')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(UsersURLTests.user)

    def test_about_urls_exist_at_desired_location(self):
        """Проверка доступности url для /auth/..."""
        field_response_urls_code = {
            '/auth/password_reset/': HTTPStatus.OK,
            '/auth/password_reset/done/': HTTPStatus.OK,
            '/auth/password_change/': HTTPStatus.OK,
            '/auth/password_change/done/': HTTPStatus.OK,
            f'/auth/reset/{UsersURLTests.user.email}/<token>/': HTTPStatus.OK,
            '/auth/reset/done/': HTTPStatus.OK,
            '/auth/logout/': HTTPStatus.OK,
            '/auth/login/': HTTPStatus.OK,
        }
        for url, response_code in field_response_urls_code.items():
            with self.subTest(url=url):
                status_code = self.authorized_client.get(url).status_code
                self.assertEqual(status_code, response_code)
