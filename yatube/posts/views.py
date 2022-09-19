from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .constanta import NAME_CONSTANTA
from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .paginator import paginator_posts


@cache_page(NAME_CONSTANTA, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related('group', 'author')
    page_obj = paginator_posts(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    title = 'Группы'
    text = 'Посты группы'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator_posts(request, posts)
    context = {
        'title': title,
        'text': text,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_list(request, slug):
    text = 'Информация о группах проекта Yatube'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator_posts(request, posts)
    context = {
        'group': group,
        'text': text,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    posts_author = get_object_or_404(User, username=username)
    post_list = posts_author.posts.all()
    page_obj = paginator_posts(request, post_list)
    context = {
        'author': posts_author,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'form': form,
        'comments': comments,
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """информация о текущем пользователе"""
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator_posts(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Функция-обработчик, позволяющая подписаться на автора."""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    """ Дизлайк, отписка"""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
