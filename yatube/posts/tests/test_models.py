from django.conf import settings
from django.test import TestCase

from ..models import Comment, Follow, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Moses')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='auth'),
            text='Текст' * settings.CHAR_NUMBER_FOR_ADMIN,
        )
        cls.commit = Comment.objects.create(
            author=cls.user,
            post_id=cls.post.pk,
            text='Коммит',
        )
        cls.fellow = Follow.objects.create(user=cls.user,
                                           author=User.objects.create_user(
                                               username='NotMoses'))

    def test_models_have_correct_object_names_group(self):
        """
        Проверка, что у моделей post и group корректно работает __str__.
        """
        fields = {
            f'{PostModelTest.post}':
                f'{PostModelTest.post.text[:settings.CHAR_NUMBER_FOR_ADMIN]}',
            f'{PostModelTest.group}': f'{PostModelTest.group.title}',
        }
        for field, expected_value in fields.items():
            with self.subTest(field=field):
                self.assertEqual(
                    expected_value, str(field))

    def test_verbose_name_post(self):
        """verbose_name в полях модели post совпадает с ожидаемым."""
        post_verbose_name = PostModelTest.post
        field_verbose = {
            'text': 'Содержание поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор поста',
            'group': 'Название группы',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post_verbose_name._meta.get_field(field).verbose_name,
                    expected_value)

    def test_verbose_name_group(self):
        """verbose_name в полях модели group совпадает с ожидаемым."""
        group_verbose_name = PostModelTest.group
        field_verbose = {
            'title': 'Название поста',
            'slug': 'url адрес',
            'description': 'Описание группы',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group_verbose_name._meta.get_field(field).verbose_name,
                    expected_value)

    def test_verbose_name_commit(self):
        """verbose_name в полях модели comment совпадает с ожидаемым."""
        comment_verbose_name = PostModelTest.commit
        field_verbose = {
            'post': 'Откоменнтированный пост',
            'author': 'Автор комментария',
            'text': 'Комментарий',
            'pub_date': 'Дата публикации',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment_verbose_name._meta.get_field(field).verbose_name,
                    expected_value)

    def test_verbose_name_fellow(self):
        """verbose_name в полях модели comment совпадает с ожидаемым."""
        comment_verbose_name = PostModelTest.fellow
        field_verbose = {
            'user': 'Подписчик',
            'author': 'Автор, на которого подписались',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment_verbose_name._meta.get_field(field).verbose_name,
                    expected_value)
