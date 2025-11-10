from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Count, Q, F
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Post, Category, Tag, PostView, PostLike


# -------- helpers --------
def _paginate(request, queryset, per_page=6):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)


def is_approved_author(user):
    # “Approved author” = has permission to add posts
    return user.is_authenticated and user.has_perm("blogs.add_post")


# -------- public views --------
def post_list(request, slug=None):
    qs = (
        Post.objects.published()  # requires Post.objects = PostQuerySet.as_manager()
        .select_related("author", "category")
    )
    page_title = "Latest Posts"

    # category/tag archives reuse this view
    rm = request.resolver_match
    if rm and rm.url_name == "category":
        category = get_object_or_404(Category, slug=slug)
        qs = qs.filter(category=category)
        page_title = f"Category: {category.name}"
    elif rm and rm.url_name == "tag":
        # tags is a CSV/text field on Post; match by Tag.name substring (case-insensitive)
        tag = get_object_or_404(Tag, slug=slug)
        qs = qs.filter(tags__icontains=tag.name)
        page_title = f"Tag: {tag.name}"

    # simple search
    q = request.GET.get("q")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(body__icontains=q))

    page_obj = _paginate(request, qs, per_page=6)

    popular_posts = (
        Post.objects.published()
        .annotate(num_comments=Count("comments"))
        .order_by("-num_comments", "-published_at")[:6]
    )
    categories = Category.objects.all().order_by("name")[:20]

    return render(
        request,
        "blog/post_list.html",
        {
            "page_obj": page_obj,
            "page_title": page_title,
            "popular_posts": popular_posts,
            "categories": categories,
        },
    )


def _get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.published()
        .select_related("author", "category")
        .prefetch_related("comments", "like_events", "view_events"),
        slug=slug,
    )

    # Unique view per session+post
    viewed = set(request.session.get("viewed_posts", []))
    key = f"post:{post.pk}"
    if key not in viewed:
        PostView.objects.create(
            post=post,
            user=request.user if request.user.is_authenticated else None,
            ip_address=_get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        # If you DO NOT have a Post.view_count integer field, don't touch it.
        # If you DO have it, uncomment the next line.
        # Post.objects.filter(pk=post.pk).update(view_count=F("view_count") + 1)
        viewed.add(key)
        request.session["viewed_posts"] = list(viewed)

    liked = False
    if request.user.is_authenticated:
        liked = PostLike.objects.filter(post=post, user=request.user).exists()

    context = {
        "post": post,
        "comment_form": CommentForm(),
        "liked": liked,
        "like_count": post.like_events.count(),   # count via PostLike reverse
        "view_count": post.view_events.count(),   # count via PostView reverse
    }
    return render(request, "blog/post_detail.html", context)


# -------- author dashboard & access flow --------
@login_required
def author_dashboard(request):
    if not is_approved_author(request.user):
        messages.info(request, "You need author approval to access the dashboard.")
        return redirect("blogs:author_apply")

    base_qs = (
        Post.objects.filter(author=request.user)
        .select_related("category")
        # Use non-conflicting annotation names
        .annotate(
            v_count=Count("view_events", distinct=True),
            l_count=Count("like_events", distinct=True),
            c_count=Count("comments", distinct=True),
        )
        .order_by("-updated", "-created")
    )

    # filters
    qs = base_qs
    status = request.GET.get("status")
    if status in {"draft", "published"}:
        qs = qs.filter(status=status)
    q = request.GET.get("q")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(body__icontains=q))

    page_obj = _paginate(request, qs, per_page=10)

    # totals panel for the author
    totals = base_qs.aggregate(
        total_posts=Count("id", distinct=True),
        total_views=Count("view_events", distinct=True),
        total_likes=Count("like_events", distinct=True),
        total_comments=Count("comments", distinct=True),
    )

    # trending (top by views then likes)
    trending = base_qs.order_by("-v_count", "-l_count")[:5]

    return render(
        request,
        "blog/author_dashboard.html",
        {"page_obj": page_obj, "totals": totals, "trending": trending},
    )


@login_required
def author_apply(request):
    """
    Informational page for logged-in users who want author rights.
    You (admin) grant 'blogs.add_post' (and optionally change/delete) in Admin.
    """
    return render(request, "blog/author_apply.html")


# -------- create/update/delete with strict ownership --------
@login_required
def post_create(request):
    if not is_approved_author(request.user):
        return redirect(f"{redirect('blogs:author_apply').url}?next=/create/")
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            # publish immediately so it appears on the home page
            post.status = Post.PUBLISHED
            # (if your Post.save() auto-sets published_at when status == published, great)
            post.save()
            messages.success(request, "Post published.")
            return redirect("blogs:post_list")  # home page shows it immediately
    else:
        form = PostForm()
    return render(request, "blog/post_form.html", {"form": form, "title": "Create Post"})


@login_required
def post_update(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if not (request.user.is_superuser or post.author_id == request.user.id):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("You cannot edit another author's post.")
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.instance.author = post.author  # keep original author
            form.save()
            messages.success(request, "Post updated.")
            return redirect("blogs:post_detail", slug=post.slug)
    else:
        form = PostForm(instance=post)
    return render(request, "blog/post_form.html", {"form": form, "title": "Edit Post"})


@login_required
def post_delete(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if not (request.user.is_superuser or post.author_id == request.user.id):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("You cannot delete another author's post.")
    if request.method == "POST":
        post.delete()
        messages.success(request, "Post deleted.")
        return redirect("blogs:author_dashboard")
    return render(request, "blog/post_delete_confirm.html", {"post": post})


def signup(request):
    if request.user.is_authenticated:
        return redirect(request.GET.get("next") or "blogs:post_list")
    next_url = request.GET.get("next") or request.POST.get("next") or "/"
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created and you are now signed in.")
            return redirect(next_url)
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form, "next": next_url})


def comment_create(request, slug):
    post = get_object_or_404(Post.objects.published(), slug=slug)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.post = post
            c.save()
            messages.success(request, "Comment added.")
    return redirect(post.get_absolute_url())


def about(request):
    return render(request, "blog/about.html")


def contact(request):
    return render(request, "blog/contact.html")


def categories(request):
    # Fetch categories with counts for published posts
    cats = (
        Category.objects
        .annotate(num_posts=Count("posts", filter=Q(posts__status="published")))
        .order_by("name")
    )

    canonical_meta = {
        "guides-tutorials": {
            "display": "Guides & Tutorials",
            "what": "In-depth, step-by-step how-tos and educational walkthroughs.",
            "why": "Learn a new skill fast with practical, actionable steps.",
            "emoji": "🧭",
        },
        "news-trends": {
            "display": "News & Trends",
            "what": "Timely updates, emerging tech, and expert takes on what’s next.",
            "why": "Stay current and make smarter, up-to-date decisions.",
            "emoji": "🗞️",
        },
        "reviews-comparisons": {
            "display": "Reviews & Comparisons",
            "what": "Honest evaluations and side-by-side comparisons of tools/services.",
            "why": "Choose confidently with unbiased guidance before you buy.",
            "emoji": "🔍",
        },
        "personal-stories-insights": {
            "display": "Personal Stories & Insights",
            "what": "Experiences, failures, wins, and opinionated lessons learned.",
            "why": "Real talk that humanizes the journey and shares takeaways.",
            "emoji": "🧠",
        },
        "tips-quick-wins": {
            "display": "Tips & Quick Wins",
            "what": "Short, scannable advice, shortcuts, and productivity boosts.",
            "why": "Get value in minutes—perfect for busy readers.",
            "emoji": "⚡",
        },
        "resources-tools": {
            "display": "Resources & Tools",
            "what": "Curated links, templates, downloads, and utilities.",
            "why": "One place to find and save the most useful stuff.",
            "emoji": "🧰",
        },
    }

    def normalize_key(cat):
        from django.utils.text import slugify as _slugify
        key = _slugify(cat.name)
        swaps = {
            "guides": "guides-tutorials",
            "tutorials": "guides-tutorials",
            "how-to": "guides-tutorials",
            "how-tos": "guides-tutorials",
            "news": "news-trends",
            "trends": "news-trends",
            "reviews": "reviews-comparisons",
            "comparisons": "reviews-comparisons",
            "stories": "personal-stories-insights",
            "insights": "personal-stories-insights",
            "tips": "tips-quick-wins",
            "quick-wins": "tips-quick-wins",
            "resources": "resources-tools",
            "tools": "resources-tools",
        }
        return swaps.get(key, key)

    enriched = []
    for c in cats:
        key = normalize_key(c)
        meta = canonical_meta.get(key, {
            "display": c.name,
            "what": "Posts curated under this topic.",
            "why": "Explore focused content tailored to this theme.",
            "emoji": "📂",
        })
        enriched.append({
            "obj": c,
            "display": meta["display"],
            "what": meta["what"],
            "why": meta["why"],
            "emoji": meta["emoji"],
        })

    enriched.sort(key=lambda x: (-x["obj"].num_posts, x["display"].lower()))
    return render(request, "blog/categories.html", {"categories": enriched})


@login_required
def post_like_toggle(request, slug):
    post = get_object_or_404(Post.objects.published(), slug=slug)
    like, created = PostLike.objects.get_or_create(post=post, user=request.user)
    if created:
        messages.success(request, "You liked this post.")
    else:
        like.delete()
        messages.info(request, "Like removed.")
    return redirect(post.get_absolute_url())
