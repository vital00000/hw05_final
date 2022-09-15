from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        labels = {'group': 'Группа', 'text': 'Сообщение'}
        fields = ["group", "text", "image"]
        help_texts = {'group': 'название групп', 'text': 'Содержимое статьи'}


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
