from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page

from .models import Post, User, Group, Follow
from .forms import PostForm, CommentForm

POSTS_PER_PAGE: int = 10


def page_obj(post_list, page_number):
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    return paginator.get_page(page_number)


@cache_page(20, key_prefix="index_page")
def index(request):
    post_list = Post.objects.select_related("group", "author").all()

    context = {
        "page_obj": page_obj(post_list, request.GET.get("page")),
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    post_list = Post.objects.select_related("author").filter(group=group).all()

    context = {
        "group": group,
        "page_obj": page_obj(post_list, request.GET.get("page")),
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)

    following = False
    if user.is_authenticated:
        following = Follow.objects.filter(user=user, author=author).exists()

    post_count = Post.objects.filter(author=author).count()

    post_list = (
        Post.objects
        .select_related("author", "group")
        .filter(author=author)
        .all())

    context = {
        "post_count": post_count,
        "author": author,
        "page_obj": page_obj(post_list, request.GET.get("page")),
        "following": following,
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("author", "group"), id=post_id)

    post_count = Post.objects.filter(author=post.author).count()

    context = {
        "comments": post.comments.all(),
        "form": CommentForm(),
        "post": post,
        "post_count": post_count,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        return redirect("posts:profile", username=request.user.username)

    return render(request, "posts/create_post.html", {"form": form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("author", "group"), id=post_id)

    if request.user != post.author:
        return redirect("posts:post_detail", post_id=post_id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post)

    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post_id)

    context = {
        "form": form,
        "is_edit": True,
    }
    return render(request, "posts/create_post.html", context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("author", "group"), id=post_id)

    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = (
        Post.objects
        .filter(author__following__user=request.user)
        .select_related("group", "author")
        .all()
    )

    context = {
        "page_obj": page_obj(posts, request.GET.get("page")),
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    follow = get_object_or_404(
        Follow.objects, user=request.user, author__username=username)
    follow.delete()
    return redirect("posts:profile", username=username)
