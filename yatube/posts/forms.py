from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'Текст твой потребен, мы в ожидании, '
            'не тяни с этим 😏'
        )
        self.fields['group'].empty_label = (
            'Группа сама себя не выберет, действуй! 😎'
        )

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Пиши в поле выше.',
            'group': 'Нажми на текст выше и появится '
                     'список доступных групп.',
            'image': 'Загрузи картинку и будет счастье.'
        }


class CommentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'Комментируй изо всех сил!'
        )

    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {'text': 'Текст комментария'}
