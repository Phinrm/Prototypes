from django import forms
from django.utils import timezone
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "category", "cover", "body", "status", "published_at", "tags"]
        widgets = {
            "published_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def save(self, commit=True):
        post = super().save(commit=False)
        # if author chooses published in the form, ensure timestamp
        if post.status == Post.PUBLISHED and not post.published_at:
            post.published_at = timezone.now()
        if commit:
            post.save()
            # no m2m on this model, but keep the pattern
            self.save_m2m()
        return post

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["name", "body"]
