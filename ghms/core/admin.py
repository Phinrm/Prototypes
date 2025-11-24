from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import ServiceItem

from .models import Department, Role, StaffProfile, Hospital


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "location")
    search_fields = ("name", "code")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "hospital")
    list_filter = ("hospital",)
    search_fields = ("name", "code")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "hospital", "department", "is_active_flag")
    list_filter = ("hospital", "department", "roles")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    filter_horizontal = ("roles",)

    def is_active_flag(self, obj):
        return obj.user.is_active

    is_active_flag.short_description = "Active"
    is_active_flag.boolean = True


# --- Inline StaffProfile on the User admin --- #

class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    can_delete = False
    fk_name = "user"
    filter_horizontal = ("roles",)


class UserAdmin(DjangoUserAdmin):
    inlines = [StaffProfileInline]


# Re-register User with inline StaffProfile
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "department", "base_price", "is_active")
    list_filter = ("department", "is_active")
    search_fields = ("code", "name")

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser