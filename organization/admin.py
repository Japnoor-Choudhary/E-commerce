from django.contrib import admin
from .models import Company, Store


# =====================================================
# Store Inline (inside Company)
# =====================================================
class StoreInline(admin.TabularInline):
    model = Store
    extra = 1
    readonly_fields = ('id', 'slug', 'created_at', 'updated_at')
    fields = (
        'name',
        'email',
        'phone',
        'address',
        'is_primary',
        'is_active',
    )


# =====================================================
# Company Admin
# =====================================================
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'is_active',
        'created_at',
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'slug', 'address', 'description')
    readonly_fields = ('id', 'slug', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [StoreInline]


# =====================================================
# Store Admin
# =====================================================
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'company',
        'slug',
        'email',
        'phone',
        'is_primary',
        'is_active',
        'created_at',
    )
    list_filter = (
        'company',
        'is_primary',
        'is_active',
    )
    search_fields = (
        'name',
        'slug',
        'email',
        'phone',
        'company__name',
    )
    readonly_fields = ('id', 'slug', 'created_at', 'updated_at')
