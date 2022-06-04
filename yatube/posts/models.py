from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    """Модель для создания таблицы Group."""

    title = models.CharField(verbose_name='Название поста',
                             max_length=200)
    slug = models.SlugField(verbose_name='url адрес',
                            max_length=200, unique=True)
    description = models.TextField(verbose_name="Описание группы")

    class Meta:
        verbose_name = 'группа'
        verbose_name_plural = 'группы'

    def __str__(self):
        return self.title


class Post(CreatedModel):
    """Модель для создания таблицы Post."""

    text = models.TextField(verbose_name="Содержание поста")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="Автор поста",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name="Название группы",
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self):
        return self.text[:settings.CHAR_NUMBER_FOR_ADMIN]


class Comment(CreatedModel):
    """Модель для создания комментариев к постам."""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Откоменнтированный пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария'
    )
    text = models.TextField(
        verbose_name='Комментарий'
    )

    def __str__(self):
        return self.text

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'


class Follow(models.Model):
    """Модель для подписок на авторов."""

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name="follower",
                             verbose_name='Подписчик')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="following",
                               verbose_name='Автор, на которого подписались')

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
