
from functools import wraps
from django.http import HttpResponseForbidden
from rest_framework.permissions import BasePermission



def user_has_role(user, *role_codes):
    sp = getattr(user, "staffprofile", None)
    if not sp: return False
    have = set(getattr(r, "code", "") for r in sp.roles.all())
    return any(rc in have for rc in role_codes)
def role_required(*role_codes):
    def decorator(fn):
        @wraps(fn)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(next=request.get_full_path())
            if not user_has_role(request.user, *role_codes):
                return HttpResponseForbidden("Insufficient role")
            return fn(request, *args, **kwargs)
        return wrapper
    return decorator

class IsAuditor(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        role = getattr(user, "role", "").upper()
        return bool(user.is_authenticated and (role == "AUDITOR" or user.is_superuser))