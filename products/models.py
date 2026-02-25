import os
import uuid
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from organization.models import Store
from django.utils import timezone
from accounts.models import User
from mptt.models import MPTTModel, TreeForeignKey
from mptt.managers import TreeManager

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

    ENTITY_FOLDER_MAP = {
        "category": "categories",
        "brand": "brands",
        "product": "products",
        "variation": "variations",
        "review": "products/reviews",
    }

    base_folder = ENTITY_FOLDER_MAP.get(
        instance.entity_type,
        "others"
    )

    return (
        f"stores/{instance.store.id}/"
        f"{base_folder}/"
        f"{instance.entity_id}/"
        f"{filename}"
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
# Attachment
# =====================================================

class Attachment(models.Model):
    ENTITY_TYPE_CHOICES = (
        ("product", "Product"),
        ("category", "Category"),
        ("brand", "Brand"),
        ("variation", "Variation"),
        ("review", "Review"),
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

        return f"media/{self.entity_type}/{self.entity_id}/{file_slug}{os.path.splitext(filename)[1]}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_type = detect_file_type(self.file.name)
            self.slug = self.generate_slug()
        super().save(*args, **kwargs)

# =====================================================
# Product Category
# =====================================================

class ProductCategory(MPTTModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="categories"
    )

    parent = TreeForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TreeManager()

    class MPTTMeta:
        order_insertion_by = ["name"]

    class Meta:
        unique_together = ("slug", "store")

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)
        if not self.slug or not self.slug.startswith(base_slug):
            slug = base_slug
            i = 1
            while ProductCategory.objects.filter(
                slug=slug,
                store=self.store
            ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            self.slug = slug

        super().save(*args, **kwargs)

# =====================================================
# Brands
# =====================================================

class Brand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE,related_name="brands")
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    def generate_unique_slug(self):
        base_slug = slugify(self.name)
        slug = base_slug
        i = 1
        while Brand.objects.filter(
            slug=slug,
            store=self.store
        ).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{i}"
            i += 1
        return slug

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)
        if not self.slug or not self.slug.startswith(base_slug):
            self.slug = self.generate_unique_slug()
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
    category = models.ForeignKey(ProductCategory,on_delete=models.PROTECT,related_name="products")
    is_adult = models.BooleanField(default=False)
    brand = models.ForeignKey(Brand,on_delete=models.PROTECT,related_name="products",null=True,blank=True)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)
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
# Product Variant & Options
# =====================================================

class ProductVariant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # new field
    quantity = models.PositiveIntegerField(default=0)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ProductVariantOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="options")
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ("variant", "key", "value")

# =====================================================
# Reviews
# =====================================================

class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    product = models.ForeignKey(Product,on_delete=models.SET_NULL,null=True,blank=True,related_name="reviews")
    rating = models.PositiveSmallIntegerField()  # 1–5
    title = models.CharField(max_length=150)
    review_text = models.TextField()
    is_deleted = models.BooleanField(default=False)      # user soft delete
    is_hidden = models.BooleanField(default=False)       # admin control
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_edit(self):
        return timezone.now() <= self.created_at + timezone.timedelta(hours=1)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.product:
            reviews = self.product.reviews.filter(
                is_deleted=False,
                is_hidden=False
            )
            avg = reviews.aggregate(models.Avg("rating"))["rating__avg"] or 0
            count = reviews.count()

            self.product.avg_rating = round(avg, 2)
            self.product.review_count = count
            self.product.save(update_fields=["avg_rating", "review_count"])
class ReviewHelpfulVote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="helpful_votes")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("review", "user")

