from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponseForbidden, Http404
from django.urls import reverse
from django.db.models import Count
from django.contrib.auth import get_user_model

from .models import Post, Category, Comment
from .forms import UserEditForm, PostForm, CommentForm, UserRegisterForm

User = get_user_model()
PAGE_SIZE = 10


def _published_posts_qs():
    now = timezone.now()
    return Post.objects.select_related('author', 'category').filter(
        is_published=True,
        pub_date__lte=now,
        category__is_published=True
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')


def index(request):
    qs = _published_posts_qs().order_by('-pub_date')
    paginator = Paginator(qs, PAGE_SIZE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    posts = page_obj.object_list
    return render(request, 'blog/index.html', {'page_obj': page_obj, 'posts': posts})


def post_detail(request, id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'category'),
        pk=id
    )

    if not post.is_visible():
        if not (request.user.is_authenticated and request.user == post.author):
            raise Http404("Публикация недоступна")

    comments = post.comments.select_related('author').all()

    context = {
        'post': post,
        'comments': comments,
    }

    if request.user.is_authenticated:
        context['form'] = CommentForm()

    return render(request, 'blog/detail.html', context)

def category_posts(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    if not category.is_published:
        raise Http404("Категория снята с публикации")
    qs = category.posts.select_related('author', 'category').filter(
        is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')
    paginator = Paginator(qs, PAGE_SIZE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    posts = page_obj.object_list
    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj,
        'posts': posts,
    })


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    if request.user.is_authenticated and request.user == profile_user:
        qs = profile_user.posts.select_related('category').all().annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    else:
        qs = _published_posts_qs().filter(author=profile_user)
    paginator = Paginator(qs, PAGE_SIZE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    posts = page_obj.object_list
    return render(request, 'blog/profile.html', {
        'profile': profile_user,
        'page_obj': page_obj,
        'posts': posts,
    })


def user_page(request, username):
    profile_user = get_object_or_404(User, username=username)
    if request.user.is_authenticated and request.user == profile_user:
        qs = profile_user.posts.select_related('category').all().annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    else:
        qs = _published_posts_qs().filter(author=profile_user)
    paginator = Paginator(qs, PAGE_SIZE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    posts = page_obj.object_list
    return render(request, 'blog/user.html', {
        'profile_user': profile_user,
        'page_obj': page_obj,
        'posts': posts,
    })


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Публикация создана')
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm(initial={'pub_date': timezone.now()})
    return render(request, 'blog/create.html', {'form': form, 'is_edit': False})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', id=post.id)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Публикация обновлена')
            return redirect('blog:post_detail', id=post.id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form, 'is_edit': True, 'post': post})


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return HttpResponseForbidden("Нельзя удалять чужие публикации")
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Публикация удалена')
        return redirect('blog:profile', username=request.user.username)
    comments = post.comments.select_related('author').all()
    form = CommentForm()
    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
        'confirm_delete': True
    })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method != 'POST':
        return redirect('blog:post_detail', id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        messages.success(request, 'Комментарий добавлен')
    else:
        messages.error(request, 'Ошибка при добавлении комментария')
    return redirect('blog:post_detail', id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post__pk=post_id)
    if request.user != comment.author:
        return HttpResponseForbidden("Нельзя редактировать чужие комментарии")
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Комментарий обновлён')
            return redirect('blog:post_detail', id=post_id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'blog/comment.html', {
        'form': form,
        'post': comment.post,
        'comment': comment,
        'edit_comment': comment
    }, status=200)

@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post__pk=post_id)
    if request.user != comment.author:
        return HttpResponseForbidden("Нельзя удалять чужие комментарии")
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Комментарий удалён')
        return redirect('blog:post_detail', id=post_id)
    return render(request, 'blog/comment.html', {
        'comment': comment,
        'post': comment.post,
        'confirm_delete': True
    }, status=200)

def signup(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно.')
            return redirect('blog:profile', username=user.username)
    else:
        form = UserRegisterForm()
    return render(request, 'registration/registration_form.html', {'form': form})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён')
            return redirect('blog:profile', username=request.user.username)
    else:
        form = UserEditForm(instance=request.user)
    return render(request, 'registration/registration_form.html', {'form': form})