from django.contrib import admin
from .models import (
    Attachment,
    ProductCategory,
    Brand,
    Product,
    ProductDetailType,
    ProductVariant,
    ProductVariantOption,
    Review,
    ReviewHelpfulVote,
)


# =====================================================
# Attachment Admin
# =====================================================
@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'entity_type', 'entity_id', 'file_type', 'slug', 'is_primary', 'store', 'created_at')
    list_filter = ('entity_type', 'store', 'file_type', 'is_primary', 'created_at')
    search_fields = ('slug', 'entity_id')
    readonly_fields = ('file_type', 'slug', 'created_at', 'updated_at')
    ordering = ('-created_at',)

# =====================================================
# Product Category Admin
# =====================================================
@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'slug', 'store', 'created_at')
    list_filter = ('store',)
    search_fields = ('name', 'slug')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    ordering = ('name',)

# =====================================================
# Product Admin
# =====================================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'slug', 'store',  'is_active', 'is_adult', 'created_at')
    list_filter = ('store', 'is_active', 'is_adult', )
    search_fields = ('name', 'slug')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    ordering = ('-created_at',)

# =====================================================
# Product Detail Type Admin
# =====================================================
@admin.register(ProductDetailType)
class ProductDetailTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('name',)

# =====================================================
# Product Variant Admin
# =====================================================
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'price', 'mrp','quantity', 'created_at')
    list_filter = ('product__store',)
    search_fields = ('product__name',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

# =====================================================
# Product Variant Option Admin
# =====================================================
@admin.register(ProductVariantOption)
class ProductVariantOptionAdmin(admin.ModelAdmin):
    list_display = ('id','variant', 'key', 'value')
    list_filter = ('variant__product__store', 'key')
    search_fields = ('key', 'value', 'variant__product__name')
    ordering = ('variant', 'key')

# =====================================================
# Brand Admin
# =====================================================
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'store', 'is_active', 'created_at')
    list_filter = ('store', 'is_active')
    search_fields = ('name', 'slug')
    readonly_fields = ('slug', 'created_at')
    ordering = ('name',)

# =====================================================
# Review Admin
# =====================================================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'product',
        'user',
        'rating',
        'is_deleted',
        'is_hidden',
        'created_at',
    )
    list_filter = ('rating', 'is_deleted', 'is_hidden', 'created_at')
    search_fields = ('user__email', 'title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
# =====================================================
# Review Helpful Vote Admin
# =====================================================
@admin.register(ReviewHelpfulVote)
class ReviewHelpfulVoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'review', 'user')
    list_filter = ()
    search_fields = ('review__product__name', 'user__email')
