from django.contrib import admin
from .models import (
    Attachment,
    ProductCategory,
    Product,
    ProductDetailType,
    ProductSpecification,
    ProductVariation
)

# =====================================================
# Attachment Admin
# =====================================================
@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'entity_type', 'entity_id', 'file_type', 'slug', 'is_primary', 'created_at')
    list_filter = ('entity_type', 'file_type', 'is_primary')
    search_fields = ('slug',)
    readonly_fields = ('file_type', 'slug', 'created_at', 'updated_at')

# =====================================================
# Product Category Admin
# =====================================================
@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at', 'updated_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}  # auto-slug in admin

# =====================================================
# Product Specification Inline
# =====================================================
class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1
    readonly_fields = ('id',)
    fields = ('key', 'value', 'detail_type')

# =====================================================
# Product Variation Inline
# =====================================================
class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1
    readonly_fields = ('id',)
    fields = ('key', 'value', 'detail_type')

# =====================================================
# Product Admin
# =====================================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'primary_category', 'created_at')
    list_filter = ('is_active', 'primary_category')
    search_fields = ('name', 'slug', 'description', 'short_description')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    inlines = [ProductSpecificationInline, ProductVariationInline]
    prepopulated_fields = {'slug': ('name',)}  # optional, admin auto-slug

# =====================================================
# Product Detail Type Admin
# =====================================================
@admin.register(ProductDetailType)
class ProductDetailTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_active',)

# =====================================================
# Product Specification Admin
# =====================================================
@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ('product', 'key', 'value', 'detail_type')
    list_filter = ('detail_type', 'product')
    search_fields = ('key', 'value', 'product__name')

# =====================================================
# Product Variation Admin
# =====================================================
@admin.register(ProductVariation)
class ProductVariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'key', 'value', 'detail_type')
    list_filter = ('detail_type', 'product')
    search_fields = ('key', 'value', 'product__name')
