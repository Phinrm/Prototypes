
from django.shortcuts import redirect
from django.urls import reverse

EXEMPT_PATHS = {"/login/", "/admin/login/", "/admin/logout/"}

class EnforceDepartmentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If not logged in, do nothing special
        if not request.user.is_authenticated:
            return self.get_response(request)

        path = request.path

        # Allow admin & static & login/logout without interference
        if path.startswith("/admin/") or path.startswith("/static/"):
            return self.get_response(request)

        # Resolve once (safe even if urls change)
        try:
            my_profile_url = reverse("my_profile")
        except Exception:
            my_profile_url = "/my-profile/"

        try:
            login_url = reverse("login")
        except Exception:
            login_url = "/login/"

        try:
            logout_url = reverse("logout")
        except Exception:
            logout_url = "/logout/"

        # Don't enforce on these views to avoid redirect loops
        if path in {my_profile_url, login_url, logout_url}:
            return self.get_response(request)

        # Check staff profile / department
        sp = getattr(request.user, "staffprofile", None)
        if not sp or not sp.department:
            # Send them to profile page to show "No staff profile linked"
            return redirect("my_profile")

        return self.get_response(request)