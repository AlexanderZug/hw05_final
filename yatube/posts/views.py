from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from .utils import paginator


def index(request):
    """
    Функция для вывода главной страницы
    и первых 10-ти постов из БД постранично.
    """
    post_list = Post.objects.select_related().all()
    page_obj = paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """
    Функция для вывода страниц сообщества и
    первых 10-ти постов из БД постранично.
    """
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related().all()
    page_obj = paginator(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Функция для вывода всех постов пользователя."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related().all()
    page_obj = paginator(request, post_list)
    following = (request.user != author
                 and request.user.is_authenticated
                 and Follow.objects.filter(user=request.user,
                                           author=author).exists())
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """
    Функция для вывода информации об отдельном посте пользователя.
    """
    post = get_object_or_404(Post.objects.select_related(),
                             pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {'post': post,
               'comments': comments,
               'form': form,
               }
    return render(request,
                  'posts/post_detail.html',
                  context)


@login_required
def post_create(request):
    """
    Функция для создания нового поста,
    если пользователь зарегистрирован.
    """
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        new_post_create = form.save(commit=False)
        new_post_create.author = request.user
        form.save()
        return redirect('posts:profile',
                        username=request.user)
    context = {
        'form': form
    }
    return render(request,
                  'posts/create_post.html',
                  context)


@login_required
def post_edit(request, post_id):
    """
    Функция для редактирования поста новым пользователем.
    """
    post = get_object_or_404(Post.objects.select_related(),
                             pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail',
                        post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail',
                        post_id=post.id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request,
                  'posts/create_post.html',
                  context)


@login_required
def add_comment(request, post_id):
    """Функция, дающая возможность оставлять комментарии."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    """Отображение подписок."""
    post = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(request, post)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора."""
    if username != request.user.username:
        author = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписаться от автора."""
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=request.user, author=author)
    if follower.exists():
        follower.delete()
    return redirect('posts:profile', username)
