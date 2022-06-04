from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Comment, Group, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Moses')
        cls.group = Group.objects.create(
            slug='test-slug',
        )
        cls.new_group = Group.objects.create(
            slug='test-slug-new',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.form = PostForm()
        cls.commit_form = CommentForm()
        cls.form_data = {'text': 'Тестовый текст',
                         'group': cls.group.id}

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        """Валидация формы создания записи и редиректа на profile."""
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': PostCreateFormTests.post.author.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostCreateFormTests.group.id).first()
        )

    def test_post_edit(self):
        """Валидация редактирования записи и редиректа на post_detail."""
        posts_count = Post.objects.count()
        form_data_edit = {
            "text": "Новый текст",
            'group': PostCreateFormTests.new_group.id,
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit",
                    kwargs={
                        "post_id": PostCreateFormTests.post.pk}),
            data=form_data_edit)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, reverse("posts:post_detail", kwargs={
            "post_id": PostCreateFormTests.post.pk}))
        self.assertTrue(Post.objects.filter(
            text="Новый текст",
            group=PostCreateFormTests.new_group.id,
        ).first())

    def test_guest_client_create_post(self):
        """
        Проверка невозможности создать
        пост для незарегистрированного пользователя.
        """
        posts_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True,
        )
        redirect = '/auth/login/' + '?next=' + reverse('posts:post_create')
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_authorized_client_csn_create_comment(self):
        """
        Комментарий появляется в БД от авторизированного пользователя.
        """
        comments_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': PostCreateFormTests.post.pk}),
            data=self.form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostCreateFormTests.post.pk}
        ))
        self.assertEqual(Comment.objects.count(), comments_count + 1)

    def test_guest_client_cant_create_comment(self):
        """
        Комментарий не появляется в БД, если его пытается сделать гость.
        """
        comments_count = Comment.objects.count()
        self.guest_client.post(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostCreateFormTests.post.pk}
            ),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)

    def test_forms_help_text_post(self):
        """Тестирование help_text из класса Meta model Post."""
        help_text_forms = PostCreateFormTests.form
        field_help_text = {
            'text': 'Пиши в поле выше.',
            'group': 'Нажми на текст выше и появится '
                     'список доступных групп.',
            'image': 'Загрузи картинку и будет счастье.',
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    help_text_forms[field].help_text, expected_value)

    def test_forms_help_text_commit(self):
        """Тестирование help_text из класса Meta model Commit."""
        help_text_forms = PostCreateFormTests.commit_form
        self.assertEqual(help_text_forms['text'].help_text,
                         'Текст комментария')

    def test_forms_empty_label(self):
        """Тестирование empty_label и placeholder из класса Meta."""
        group_label = PostCreateFormTests.form.fields['group'].empty_label
        placeholder = PostCreateFormTests.form.fields['text'].widget.attrs[
            'placeholder']
        placeholder_commit = PostCreateFormTests.commit_form.fields[
            'text'].widget.attrs['placeholder']
        fields = {
            f'{group_label}': 'Группа сама себя не выберет, '
                              'действуй! 😎',
            f'{placeholder}': 'Текст твой потребен, мы в ожидании, '
                              'не тяни с этим 😏',
            f'{placeholder_commit}': 'Комментируй изо всех сил!',
        }
        for field, expected_value in fields.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected_value)

    def test_photo_upload(self):
        """При загрузке фото появляется запись в БД."""
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
            'text': 'Пост с картинкой',
            'group': PostCreateFormTests.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
