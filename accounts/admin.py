from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission

from .models import User, Role, Address


# =====================================================
# Role Admin
# =====================================================
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "store")
    list_filter = ("store",)
    search_fields = ("name", "store__name")
    filter_horizontal = ("permissions",)


# =====================================================
# User Admin
# =====================================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = (
        "email",
        "first_name",
        "last_name",
        "number",
        "store",
        "is_staff",
        "is_customer",
        "is_guest",
        "is_active",
        "date_joined",
    )

    list_filter = (
        "is_staff",
        "is_active",
        "is_customer",
        "is_guest",
        "store",
    )

    search_fields = ("email", "first_name", "last_name", "number")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),

        (_("Personal Info"), {
            "fields": ("first_name", "last_name", "number", "store")
        }),

        (_("Role Flags"), {
            "fields": (
                "is_staff",
                "is_active",
                "is_superuser",
                "is_customer",
                "is_guest",
            )
        }),

        (_("Permissions"), {
            "fields": (
                "groups",
                "user_permissions",
            )
        }),

        (_("Important Dates"), {
            "fields": ("last_login", "date_joined")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "first_name",
                "last_name",
                "number",
                "store",
                "password1",
                "password2",
                "is_staff",
                "is_active",
                "is_customer",
                "is_guest",
            ),
        }),
    )


# =====================================================
# Address Admin
# =====================================================
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "type",
        "city",
        "state",
        "country",
        "postal_code",
        "is_primary",
        "created_at",
    )

    list_filter = (
        "type",
        "is_primary",
        "country",
        "state",
    )

    search_fields = (
        "user__email",
        "line1",
        "city",
        "state",
        "country",
        "postal_code",
    )

    ordering = ("user", "-is_primary", "-created_at")