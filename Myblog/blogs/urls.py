from django.urls import path
from . import views

app_name = "blogs"

urlpatterns = [
    path("", views.post_list, name="post_list"),

    # static pages you already had
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),

    # categories
    path("categories/", views.categories, name="categories"),
    path("category/<slug:slug>/", views.post_list, name="category"),
    path("tag/<slug:slug>/", views.post_list, name="tag"),

    # author flow
    path("dashboard/", views.author_dashboard, name="author_dashboard"),
    path("author/apply/", views.author_apply, name="author_apply"),

    # auth (signup you added earlier)
    path("accounts/signup/", views.signup, name="signup"),

    # compose & ownership-safe CRUD
    path("create/", views.post_create, name="post_create"),
    path("<slug:slug>/edit/", views.post_update, name="post_update"),
    path("<slug:slug>/delete/", views.post_delete, name="post_delete"),
    path("<slug:slug>/comment/", views.comment_create, name="comment_create"),
    path("<slug:slug>/", views.post_detail, name="post_detail"),  # keep last

    path("<slug:slug>/like/", views.post_like_toggle, name="post_like_toggle"),
    # keep post_detail last:
    path("<slug:slug>/", views.post_detail, name="post_detail"),

    # blogs/urls.py
    path("accounts/signup/", views.signup, name="signup"),



]
