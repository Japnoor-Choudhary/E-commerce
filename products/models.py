import os
import uuid
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
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
    """
    media/
    stores/<store_id>(uuid)/
      products/<entity_id>/<filename>
      categories/<entity_id>/<filename>
      variations/<entity_id>/<filename>
    """
    return os.path.join(
        "stores",
        str(instance.store_id),
        f"{instance.entity_type}s",
        str(instance.entity_id),
        filename
    )

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
# Attachment (Generic Media)
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
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="attachments"
    )
    file = models.FileField(upload_to=attachment_upload_path)
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



class ProductCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="categories"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug or ProductCategory.objects.filter(pk=self.pk).exclude(name=self.name).exists():
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="products"
    )
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
        if not self.slug or Product.objects.filter(pk=self.pk).exclude(name=self.name).exists():
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

class ProductDetailType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)   # add this
    updated_at = models.DateTimeField(auto_now=True) 

class ProductSpecification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="specifications"
    )

    detail_type = models.ForeignKey(
        ProductDetailType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    key = models.CharField(max_length=100, db_index=True)
    value = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)   # add this
    updated_at = models.DateTimeField(auto_now=True) 





class ProductVariation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variations"
    )

    detail_type = models.ForeignKey(
        ProductDetailType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    key = models.CharField(max_length=100, db_index=True)
    value = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)   # add this
    updated_at = models.DateTimeField(auto_now=True) 
    class Meta:
        unique_together = ("product", "key", "value")

    def clean(self):
        if not ProductSpecification.objects.filter(
            product=self.product,
            key=self.key
        ).exists():
            raise ValidationError(
                f"Key '{self.key}' does not exist in product specification"
            )

    

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
