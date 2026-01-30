from django.contrib import admin

# Register your models here.
from django.contrib.auth import get_user_model
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Role

# -----------------------------
# Role Admin
# -----------------------------
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    filter_horizontal = ["permissions"]  # ManyToMany permissions

# -----------------------------
# User Admin
# -----------------------------

User = get_user_model()

# Unregister if already registered to avoid AlreadyRegistered error
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "number", "first_name", "last_name", "is_staff", "is_active", "date_joined"]
    list_filter = ["is_staff", "is_active"]
    search_fields = ["email", "first_name", "last_name", "number"]
    ordering = ["email"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "number")}),
        (_("Permissions"), {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "number", "first_name", "last_name", "password1", "password2", "is_staff", "is_active"),
        }),
    )
