import os
import uuid
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from organization.models import Store

# =====================================================
# Helpers
# =====================================================

def detect_file_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        return "image"
    if ext in [".mp4", ".mov", ".avi", ".mkv"]:
        return "video"
    if ext == ".pdf":
        return "pdf"
    return "other"

def attachment_upload_path(instance, filename):
    name, ext = os.path.splitext(filename)
    safe_name = slugify(name)[:50]
    filename = f"{safe_name}_{uuid.uuid4().hex}{ext}"
    return os.path.join(
        f"stores/{instance.store.id}/categorys/{instance.entity_id}",
        filename
    ).replace("\\", "/")

def get_entity_slug(entity_type, entity_id):
    from products.models import Product, ProductCategory
    model_map = {
        "product": Product,
        "category": ProductCategory,
    }
    model = model_map.get(entity_type)
    if not model:
        return "unknown"
    try:
        obj = model.objects.get(id=entity_id)
        return obj.slug
    except model.DoesNotExist:
        return "unknown"

# =====================================================
# Attachment
# =====================================================

class Attachment(models.Model):
    ENTITY_TYPE_CHOICES = (
        ("product", "Product"),
        ("category", "Category"),
        ("variation", "Variation"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPE_CHOICES)
    entity_id = models.UUIDField()
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=attachment_upload_path, max_length=500)
    file_type = models.CharField(max_length=20, blank=True)
    slug = models.SlugField(max_length=500, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_slug(self):
        filename = os.path.basename(self.file.name)
        name_without_ext = os.path.splitext(filename)[0]
        file_slug = slugify(name_without_ext)
        entity_slug = get_entity_slug(self.entity_type, self.entity_id)
        return f"media/{self.entity_type}/{entity_slug}/{file_slug}"

    def save(self, *args, **kwargs):
        if self.file:
            self.file_type = detect_file_type(self.file.name)
            self.slug = self.generate_slug()
        super().save(*args, **kwargs)

# =====================================================
# Product Category
# =====================================================

class ProductCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="categories")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)
        if not self.slug or (self.slug.split('-')[0] != base_slug):
            slug = base_slug
            i = 1
            while ProductCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

# =====================================================
# Product
# =====================================================

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    description = models.TextField()
    short_description = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    primary_category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )
    is_adult = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_unique_slug(self):
        base = slugify(self.name)
        slug = base
        i = 1
        while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{i}"
            i += 1
        return slug

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)
        if not self.slug or not self.slug.startswith(base_slug):
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

# =====================================================
# Product Detail Type
# =====================================================

class ProductDetailType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# =====================================================
# Product Specification
# =====================================================

class ProductSpecification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specifications")
    detail_type = models.ForeignKey(ProductDetailType, on_delete=models.SET_NULL, null=True, blank=True)
    key = models.CharField(max_length=100, db_index=True)
    value = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# =====================================================
# Product Variant & Options
# =====================================================

class ProductVariant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ProductVariantOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="options")
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ("variant", "key", "value")
