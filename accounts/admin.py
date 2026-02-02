from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission

from .models import User, Role


# =====================================================
# Role Admin
# =====================================================
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'store')
    list_filter = ('store',)
    search_fields = ('name', 'store__name')
    filter_horizontal = ('permissions',)


# =====================================================
# User Admin
# =====================================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email',
        'first_name',
        'last_name',
        'number',
        'store',
        'is_staff',
        'is_active',
        'date_joined',
    )

    list_filter = ('is_staff', 'is_active', 'store')
    search_fields = ('email', 'first_name', 'last_name', 'number')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'number', 'store')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'first_name',
                'last_name',
                'number',
                'store',
                'password1',
                'password2',
                'is_staff',
                'is_active',
            ),
        }),
    )
