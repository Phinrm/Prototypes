from django.contrib import admin
from django.db.models import Count
from .models import Post, Category, Tag, Comment

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "status",
        "published_at",
        "admin_view_count",
        "admin_like_count",
    )
    # Only filter on supported field types
    list_filter = ("status", "category")
    search_fields = ("title", "body", "tags")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [CommentInline]
    autocomplete_fields = ("category",)  # tags is CharField, so omit
    date_hierarchy = "published_at"
    ordering = ("-published_at",)

    def get_queryset(self, request):
        qs = (
            super()
            .get_queryset(request)
            # NOTE: use new related names from models.py
            .annotate(
                _vcount=Count("view_events", distinct=True),
                _lcount=Count("like_events", distinct=True),
            )
        )
        # Limit non-superusers to their own posts
        if request.user.is_superuser:
            return qs
        return qs.filter(author=request.user)

    # Use method names that DON'T collide with Post.view_count field
    def admin_view_count(self, obj):
        return getattr(obj, "_vcount", 0)
    admin_view_count.short_description = "Views"

    def admin_like_count(self, obj):
        return getattr(obj, "_lcount", 0)
    admin_like_count.short_description = "Likes"

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser and obj:
            ro.append("author")
        return ro

    def has_change_permission(self, request, obj=None):
        has = super().has_change_permission(request, obj)
        if not has:
            return False
        if obj is None or request.user.is_superuser:
            return True
        return obj.author_id == request.user.id

    def has_view_permission(self, request, obj=None):
        has = super().has_view_permission(request, obj)
        if not has:
            return False
        if obj is None or request.user.is_superuser:
            return True
        return obj.author_id == request.user.id

    def has_delete_permission(self, request, obj=None):
        has = super().has_delete_permission(request, obj)
        if not has:
            return False
        if obj is None or request.user.is_superuser:
            return True
        return obj.author_id == request.user.id

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "body")
