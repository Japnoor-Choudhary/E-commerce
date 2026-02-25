from rest_framework import serializers
from .models import *
from django.db.models import Sum
from django.db import transaction    
# -----------------------------
# Attachment
# -----------------------------
class AttachmentSerializer(serializers.ModelSerializer):
    """
    Serializes Attachment model.
    Used to read attachment data (images/files) in API responses.
    """

    class Meta:
        model = Attachment
        fields = "__all__"

        # These fields are set automatically by backend logic
        read_only_fields = ("store", "file_type", "slug", "created_at", "updated_at")

        
# -----------------------------
# Attachment Bulk Upload
# -----------------------------
class AttachmentBulkUploadSerializer(serializers.Serializer):
    """
    Serializer used to upload multiple files
    and attach them to a single entity (product, brand, category, etc.)
    """

    # Defines what type of object the attachment belongs to
    entity_type = serializers.ChoiceField(choices=Attachment.ENTITY_TYPE_CHOICES)

    # UUID of the entity (product_id, brand_id, etc.)
    entity_id = serializers.UUIDField()

    # List of files to be uploaded
    files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True
    )
        

# =====================================================
# Brands
# =====================================================

class BrandSerializer(serializers.ModelSerializer):
    """
    Serializer for Brand CRUD.
    Allows optional logo upload while creating brand.
    """

    # Logo is not a direct model field
    logo = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Brand
        fields = "__all__"

        # Store & slug handled internally
        read_only_fields = ("store", "slug", "created_at")

    def create(self, validated_data):
        logo = validated_data.pop("logo", None)

        validated_data["store"] = self.context["request"].user.store
        brand = Brand.objects.create(**validated_data)

        if logo:
            Attachment.objects.create(
                entity_type="brand",
                entity_id=brand.id,
                store=brand.store,
                file=logo
            )
        return brand

class BrandNestedSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer used inside Product responses.
    """

    logo = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ("id", "name", "slug", "logo")

    def get_logo(self, obj):
        """
        Fetches the brand logo from Attachment table.
        """

        attachment = Attachment.objects.filter(
            entity_type="brand",
            entity_id=obj.id
        ).first()

        return attachment.file.url if attachment else None

# -----------------------------
# Product Category
# -----------------------------
class ProductCategoryCreateSerializer(serializers.ModelSerializer):
    parent_id = serializers.UUIDField(required=False, allow_null=True)

    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = ProductCategory
        fields = "__all__"
        read_only_fields = ("store", "slug")

    def create(self, validated_data):
        request = self.context.get("request")
        store = request.user.store

        parent_id = validated_data.pop("parent_id", None)
        attachments = validated_data.pop("attachments", [])

        if parent_id:
            parent = ProductCategory.objects.get(
                id=parent_id,
                store=store
            )
            validated_data["parent"] = parent

        with transaction.atomic():

            category = ProductCategory.objects.create(
                store=store,
                **validated_data
            )

            for file in attachments:
                Attachment.objects.create(
                    entity_type="category",
                    entity_id=category.id,
                    store=store,
                    file=file
                )

        return category

class ProductCategoryResponseSerializer(serializers.ModelSerializer):
    parent_id = serializers.UUIDField(source="parent.id", read_only=True)
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = [
            "id",
            "name",
            "slug",
            "parent_id",
            "store",
            "attachments",
            "created_at",
            "updated_at",
        ]

    def get_attachments(self, obj):
        return AttachmentSerializer(
            Attachment.objects.filter(
                entity_type="category",
                entity_id=obj.id,
                store=obj.store
            ),
            many=True
        ).data


class ProductCategoryUpdateSerializer(serializers.ModelSerializer):

    attachments = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    parent_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = ProductCategory
        exclude = ("store", "slug", "created_at", "updated_at")

    def update(self, instance, validated_data):
        attachments = validated_data.pop("attachments", [])
        parent_id = validated_data.pop("parent_id", serializers.empty)

        if parent_id is None:
            instance.parent = None
        elif parent_id is not serializers.empty:
            instance.parent = ProductCategory.objects.get(
                id=parent_id,
                store=self.context["request"].user.store
            )

        instance = super().update(instance, validated_data)

        for file in attachments:
            Attachment.objects.create(
                entity_type="category",
                entity_id=instance.id,
                store=instance.store,
                file=file
            )

        return instance


class ProductCategoryNestedSerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ("id", "name", "slug", "subcategories")

    def get_subcategories(self, obj):
        children = obj.get_children()
        return ProductCategoryNestedSerializer(children, many=True).data


# -----------------------------
# Product Variant & Options
# -----------------------------
class VariantOptionSerializer(serializers.Serializer):
    """
    Represents a single variant option key-value pair.
    """
    key = serializers.CharField()
    value = serializers.CharField()

    
class ProductVariantOptionSerializer(serializers.ModelSerializer):
    """
    Serializer for ProductVariantOption model.
    """

    class Meta:
        model = ProductVariantOption
        fields = "__all__"

class ProductVariantItemSerializer(serializers.Serializer):
    """
    Represents one variant entry during bulk creation.
    """
    mrp = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)  # optional
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField()

    # Options like size, color
    options = serializers.DictField(
        child=serializers.CharField()
    )

    # Variant images
    attachments = serializers.ListField(
        child=serializers.ImageField(),
        required=False
    )
    
class ProductNestedInVariantSerializer(serializers.ModelSerializer):
    categories = ProductCategoryNestedSerializer(many=True, read_only=True)
    brand = BrandNestedSerializer(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "short_description",
            "is_active",
            "is_adult",
            "avg_rating",
            "review_count",
            "categories",
            "brand",
        )


class ProductVariantPublicSerializer(serializers.ModelSerializer):
    """
    Public serializer:
    - Shows real price
    - ALWAYS shows full options
    - Explains filter matching via match_info
    """

    options = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    match_info = serializers.SerializerMethodField()
    product = ProductNestedInVariantSerializer(read_only=True)

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "product",
            "price",
            "options",
            "attachments",
            "mrp",
            "match_info",
        )

    # ✅ ALWAYS return full options (NO FILTERING HERE)
    def get_options(self, obj):
        return ProductVariantOptionSerializer(
            obj.options.all(),
            many=True
        ).data

    def get_attachments(self, obj):
        return AttachmentSerializer(
            Attachment.objects.filter(
                entity_type="variation",
                entity_id=obj.id,
                store=obj.product.store
            ),
            many=True
        ).data

    def get_match_info(self, obj):
        request = self.context.get("request")

        # ✅ Only show match_info for filter API
        if not request or not request.path.endswith("/variations/filter/"):
            return None

        requested_colors = {
            c.lower()
            for c in request.query_params.get("color", "").split(",")
            if c
        }

        requested_sizes = {
            s.lower()
            for s in request.query_params.get("size", "").split(",")
            if s
        }


        # No filters → still useful for filter API
        if not requested_colors and not requested_sizes:
            return {
                "matched": True,
                "color_matched": True,
                "size_matched": True,
                "summary": "🎯 No filters – showing all variants",
            }

        variant_colors = {
            opt.value.lower()
            for opt in obj.options.all()
            if opt.key == "color"
        }

        variant_sizes = {
            opt.value.lower()
            for opt in obj.options.all()
            if opt.key == "size"
        }

        color_matched = bool(variant_colors & requested_colors) if requested_colors else False
        size_matched = bool(variant_sizes & requested_sizes) if requested_sizes else False

        matched = (
            (not requested_colors or color_matched)
            and
            (not requested_sizes or size_matched)
        )

        if color_matched and not size_matched:
            summary = "⚠️ Color matched but size not available"
        elif size_matched and not color_matched:
            summary = "⚠️ Size matched but color not available"
        elif color_matched and size_matched:
            summary = "🎯 Perfect match"
        else:
            summary = "❌ No match"

        return {
            "matched": matched,
            "color_matched": color_matched,
            "size_matched": size_matched,
            "summary": summary,
        }

class ProductVariantPrivateSerializer(serializers.ModelSerializer):
    """
    Private serializer:
    - Shows inventory
    - Shows ALL options
    - Includes match_info for debugging
    """

    options = ProductVariantOptionSerializer(many=True, read_only=True)
    attachments = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    match_info = serializers.SerializerMethodField()
    product = ProductNestedInVariantSerializer(read_only=True)

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "product",
            "price",
            "quantity",
            "is_low_stock",
            "options",
            "attachments",
            "mrp",
            "match_info",
        )

    # -------------------------
    # LOW STOCK
    # -------------------------
    def get_is_low_stock(self, obj):
        return obj.quantity <= 20

    # -------------------------
    # ATTACHMENTS
    # -------------------------
    def get_attachments(self, obj):
        return AttachmentSerializer(
            Attachment.objects.filter(
                entity_type="variation",
                entity_id=obj.id,
                store=obj.product.store
            ),
            many=True
        ).data

    # -------------------------
    # MATCH INFO (FULL DEBUG)
    # -------------------------
    def get_match_info(self, obj):
        request = self.context.get("request")

        # ✅ Only show match_info for filter API
        if not request or not request.path.endswith("/variations/filter/"):
            return None

        requested_colors = {
            c.lower()
            for c in request.query_params.get("color", "").split(",")
            if c
        }

        requested_sizes = {
            s.lower()
            for s in request.query_params.get("size", "").split(",")
            if s
        }


        # No filters → still useful for filter API
        if not requested_colors and not requested_sizes:
            return {
                "matched": True,
                "color_matched": True,
                "size_matched": True,
                "summary": "🎯 No filters – showing all variants",
            }

        variant_colors = {
            opt.value.lower()
            for opt in obj.options.all()
            if opt.key == "color"
        }

        variant_sizes = {
            opt.value.lower()
            for opt in obj.options.all()
            if opt.key == "size"
        }


        color_matched = bool(variant_colors & requested_colors) if requested_colors else False
        size_matched = bool(variant_sizes & requested_sizes) if requested_sizes else False

        matched = (
            (not requested_colors or color_matched)
            and
            (not requested_sizes or size_matched)
        )


        if color_matched and not size_matched:
            summary = "⚠️ Color matched but size not available"
        elif size_matched and not color_matched:
            summary = "⚠️ Size matched but color not available"
        elif color_matched and size_matched:
            summary = "🎯 Perfect match"
        else:
            summary = "❌ No match"

        return {
            "matched": matched,
            "color_matched": color_matched,
            "size_matched": size_matched,
            "summary": summary,
        }

class ProductVariantSerializer(serializers.ModelSerializer):
    options = ProductVariantOptionSerializer(many=True, read_only=True)
    is_low_stock = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    product = ProductNestedInVariantSerializer(read_only=True) 

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "quantity",
            "mrp",
            "price",
            "is_low_stock",
            "options",
            "attachments",
        )


    def get_is_low_stock(self, obj):
        return obj.quantity <= 20



    def get_attachments(self, obj):
        """
        Returns attachments related to this variant.
        """

        return AttachmentSerializer(
            Attachment.objects.filter(
                entity_type="variation",
                entity_id=obj.id,
                store=obj.product.store
            ),
            many=True
        ).data

class ProductVariantCreateSerializer(serializers.Serializer):
    """
    Handles bulk creation of product variants
    in a single API request.
    """

    product_id = serializers.UUIDField()
    variants = ProductVariantItemSerializer(many=True)

    def create(self, validated_data):
        """
        Creates:
        - variants
        - variant options
        - inventory records
        - attachments
        """

        request = self.context["request"]

        product = Product.objects.get(
            id=validated_data["product_id"],
            store=request.user.store
        )

        created_variants = []

        for variant_data in validated_data["variants"]:
            options = variant_data.pop("options", {})
            attachments = variant_data.pop("attachments", [])
            quantity = variant_data.pop("quantity",0)
            mrp = variant_data.pop("mrp", None)


            # Create variant
            variant = ProductVariant.objects.create(
                product=product,
                price=variant_data["price"],
                mrp=mrp,
                quantity=quantity   # 👈 STORE HERE
            )


            # Create variant options
            for key, value in options.items():
                ProductVariantOption.objects.create(
                    variant=variant,
                    key=key,
                    value=value
                )

            # Save variant attachments
            for index, file in enumerate(attachments):
                Attachment.objects.create(
                    store=product.store,
                    entity_type="variation",
                    entity_id=variant.id,
                    file=file,
                    is_primary=(index == 0)
                )

            created_variants.append(variant)

        return created_variants


# -----------------------------
# Product
# -----------------------------

class ProductSerializer(serializers.ModelSerializer):
    category = ProductCategoryNestedSerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True, required=False)

    brand = BrandNestedSerializer(read_only=True)
    brand_id = serializers.UUIDField(write_only=True, required=False)

    variants = ProductVariantItemSerializer(
        many=True,
        write_only=True,
        required=False
    )

    total_quantity = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    low_stock_variants = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "description", "short_description",
            "is_active", "is_adult", "avg_rating", "review_count",
            "created_at", "updated_at", "store",
            "brand", "brand_id",
            "category", "category_id",
            "variants",
            "total_quantity", "is_low_stock", "low_stock_variants"
        )
        read_only_fields = ("store", "slug", "created_at", "updated_at")


    def create(self, validated_data):
        request = self.context["request"]

        variants_data = validated_data.pop("variants", [])
        category_id = validated_data.pop("category_id")
        brand_id = validated_data.pop("brand_id", None)

        validated_data["store"] = request.user.store

        # Attach category
        validated_data["category"] = ProductCategory.objects.get(
            id=category_id,
            store=request.user.store
        )

        # Brand
        if brand_id:
            validated_data["brand"] = Brand.objects.get(
                id=brand_id,
                store=request.user.store
            )

        product = Product.objects.create(**validated_data)

        # Variants
        for variant_data in variants_data:
            options = variant_data.pop("options", {})
            attachments = variant_data.pop("attachments", [])

            variant = ProductVariant.objects.create(
                product=product,
                **variant_data
            )

            for k, v in options.items():
                ProductVariantOption.objects.create(
                    variant=variant,
                    key=k,
                    value=v
                )

            for idx, file in enumerate(attachments):
                Attachment.objects.create(
                    store=product.store,
                    entity_type="variation",
                    entity_id=variant.id,
                    file=file,
                    is_primary=(idx == 0)
                )

        return product

    def get_total_quantity(self, obj):
        # Sum all quantities of all variants of this product
        total = obj.variants.aggregate(total=Sum('quantity'))['total']
        return total or 0

        # -------------------------
    # Is low stock?
    # -------------------------
    def get_is_low_stock(self, obj):
        total_qty = self.get_total_quantity(obj)
        return total_qty <= 20  # or whatever threshold you prefer

    # -------------------------
    # Low stock variants
    # -------------------------
    def get_low_stock_variants(self, obj):
        low_variants = obj.variants.filter(quantity__lte=20)
        return ProductVariantPrivateSerializer(
            low_variants,
            many=True,
            context=self.context
        ).data

# -----------------------------
# Product Detail Type
# -----------------------------
class ProductDetailTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for product detail types
    (e.g. material, warranty, brand info).
    """

    class Meta:
        model = ProductDetailType
        fields = "__all__"

# =====================================================
# Reviews 
# =====================================================
class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for reading product reviews.
    """

    helpful_count = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ("user", "is_deleted", "is_hidden", "created_at")

    def get_helpful_count(self, obj):
        """
        Returns total helpful votes.
        """

        return obj.helpful_votes.count()

    def get_attachments(self, obj):
        """
        Returns attachments for the review.
        """

        return Attachment.objects.filter(
            entity_type="review",
            entity_id=obj.id
        ).values("id", "file", "file_type")


class ReviewCreateSerializer(serializers.Serializer):
    """
    Used for creating a review with optional attachments.
    """
    product_id = serializers.UUIDField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(max_length=150)
    review_text = serializers.CharField()
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        max_length=5
    )

    def create(self, validated_data):
        request = self.context["request"]
        attachments = validated_data.pop("attachments", [])

        review = Review.objects.create(
            user=request.user,
            product_id=validated_data["product_id"],
            rating=validated_data["rating"],
            title=validated_data["title"],
            review_text=validated_data["review_text"]
        )

        for file in attachments:
            Attachment.objects.create(
                store=request.user.store,
                entity_type="review",
                entity_id=review.id,
                file=file
            )

        return review

# =====================================================
# Product Import Serializer
# =====================================================

class ProductImportSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_active = serializers.BooleanField(default=True)
    categories = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    brand = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        request = self.context["request"]
        store = request.user.store

        category_names = validated_data.pop("categories", [])
        brand_name = validated_data.pop("brand", None)

        product = Product.objects.create(
            store=store,
            **validated_data
        )

        if brand_name:
            product.brand = Brand.objects.filter(
                name=brand_name,
                store=store
            ).first()
            product.save()

        if category_names:
            categories = ProductCategory.objects.filter(
                name__in=category_names,
                store=store
            )
            if categories.exists():
                product.category = categories.first()
                product.save()

        return product


