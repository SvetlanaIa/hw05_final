from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponse
from .forms import PostForm, CommentForm
from .models import Post, Group, User, Comment, Follow
from django.http import HttpResponseRedirect, request
from django.contrib.auth.decorators import login_required
from django.db.models.aggregates import Count


def index(request):
    post_list = (
        Post.objects.select_related("author")
        .select_related("group")
        .order_by("-pub_date")
        .annotate(comment_count=Count("post_comment"))
    )

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(request, "index.html", {"page": page, "paginator": paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
  #  post_list = Post.objects.filter(group=group).order_by("-pub_date").all()

    post_list = (
        Post.objects.select_related("author")
        .select_related("group")
        .filter(group=group)
        .order_by("-pub_date")
        .annotate(comment_count=Count("post_comment"))
    )

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(request, "group.html", {"group": group, "page": page, "paginator": paginator})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {
        "title": "Редактировать запись",
        "button": "Сохранить",
        "form": form,
    }
    if request.method == "POST":
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("index")
    return render(request, "new_post.html", context)


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=profile).order_by("-pub_date").all()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    user_followers = Follow.objects.filter(author=profile).count()
    user_follow = Follow.objects.filter(user=profile).count()

    context = {
        "page": page,
        "paginator": paginator,
        "posts": posts,
        "author": profile,
        "user_follow": user_follow,
        "user_followers": user_followers
    }

    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=profile).first()
        context["following"] = following

    return render(request, "profile.html", context)


def post_view(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=profile).all()
    post = Post.objects.get(id=post_id)
    posts_count = Post.objects.filter(author=profile).count()
    user_followers = Follow.objects.filter(author=profile).count()
    user_follow = Follow.objects.filter(user=profile).count()
    form = CommentForm()

    context = {
        "posts": posts,
        "post": post,
        "post_count": posts_count,
        "author": profile,
        "user_follow": user_follow,
        "user_followers": user_followers,
        "form": form
    }

    if request.user.is_authenticated:
        items = Comment.objects.filter(post=post).order_by("-created").all()
        context["items"] = items

    return render(request, "post.html", context)


def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = get_object_or_404(User, username=username)

    if request.user != user:
        return redirect("post", username=user.username, post_id=post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    context = {
        "title": "Редактировать запись",
        "button": "Сохранить",
        "post": post,
        "form": form,
    }
    if request.method == "POST":
        if form.is_valid():
            post.save()
            return redirect("post", username=user.username, post_id=post_id)
    return render(request, "new_post.html", context)


def post_remove(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect("post", username=post.author, post_id=post.id)
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return redirect("index")


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = get_object_or_404(User, username=username)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect("post", username=user.username, post_id=post_id)
    form = CommentForm()
    return redirect("post", username=user.username, post_id=post_id)


@login_required
def follow_index(request):
    follows = Follow.objects.select_related(
        "author", "user").filter(user=request.user)
    authors = [follow.author for follow in follows]
    posts = Post.objects.filter(author__in=authors).order_by("-pub_date").all()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(request, "follow.html", {"page": page, "paginator": paginator, "posts": posts})


@login_required
def profile_follow(request, username):
    profile = get_object_or_404(User, username=username)
    if request.user==profile:
        return redirect("profile", username=profile)
    if Follow.objects.filter(author=profile).all():
        return redirect("profile", username=profile)
    else:
        Follow.objects.create(user=request.user, author=profile)
        return redirect("profile", username=profile)


@login_required
def profile_unfollow(request, username):
    profile = get_object_or_404(User, username=username)
    follows = Follow.objects.filter(author=profile, user=request.user).all()
    follows.delete()
    return redirect("profile", username=profile)
