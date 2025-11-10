from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings
from django.utils import timezone  # <-- needed for published_at

User = get_user_model()


class Timestamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:60]
        super().save(*args, **kwargs)


class Tag(Timestamped):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:60]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # your urls should use app_name = "blogs"
        return reverse("blogs:tag", args=[self.slug])


class PostQuerySet(models.QuerySet):
    def published(self):
        # use the status constant to avoid typos
        return self.filter(status=Post.PUBLISHED)


class Post(models.Model):
    DRAFT = "draft"
    PUBLISHED = "published"
    STATUS_CHOICES = [(DRAFT, "Draft"), (PUBLISHED, "Published")]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts"
    )

    cover = models.ImageField(upload_to="covers/", blank=True, null=True)
    body = models.TextField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    published_at = models.DateTimeField(blank=True, null=True)

    # simple CSV tags field (kept alongside Tag model for now)
    tags = models.CharField(max_length=250, blank=True)

    # keep a numeric counter if you want lightweight summaries
    view_count = models.PositiveIntegerField(default=0)

    # ManyToMany through PostLike for constraints and analytics
    likes = models.ManyToManyField(
        User, blank=True, through="PostLike", related_name="liked_posts"
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-created"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # ensure a unique slug
        if not self.slug:
            base = slugify(self.title)[:60]
            slug = base
            i = 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug

        # set published_at the first time we become published
        if self.status == self.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blogs:post_detail", args=[self.slug])

    def read_time_minutes(self):
        import math, re
        words = len(re.findall(r"\w+", self.body or ""))
        return max(1, math.ceil(words / 200))


class PostView(Timestamped):
    """
    Each unique view event.
    """
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="view_events"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["post", "created_at"]),
        ]

    def __str__(self):
        return f"View {self.post_id} @ {self.created_at}"


class PostLike(Timestamped):
    """
    A user's like on a post (one like per user per post).
    """
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="like_events"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_like_events"
    )

    class Meta:
        unique_together = ("post", "user")
        indexes = [
            models.Index(fields=["post", "user"]),
        ]

    def __str__(self):
        return f"Like {self.user_id} -> {self.post_id}"


class Comment(Timestamped):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField(max_length=80)
    body = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.name} on {self.post}"
