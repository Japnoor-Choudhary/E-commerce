from rest_framework import serializers
from .models import *
from django.db.models import Sum
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
        """
        Creates a brand.
        If logo is provided, it is stored as an Attachment.
        """

        # Remove logo from validated data
        logo = validated_data.pop("logo", None)

        # Create brand instance
        brand = Brand.objects.create(**validated_data)

        # Save logo as attachment if provided
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
    """
    Used to create categories with:
    - optional parent category
    - multiple attachments
    """

    attachments = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    # Used to assign parent category
    parent_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = ProductCategory
        fields = "__all__"
        read_only_fields = ("store",)

    def create(self, validated_data):
        """
        Creates a category, assigns parent (if any),
        and saves attachments.
        """

        attachments = validated_data.pop("attachments", [])
        parent_id = validated_data.pop("parent_id", None)

        # Assign parent category if provided
        if parent_id:
            validated_data["parent"] = ProductCategory.objects.get(id=parent_id)

        # Assign store from logged-in user
        validated_data["store"] = self.context["request"].user.store

        category = super().create(validated_data)

        # Save category attachments
        for file in attachments:
            Attachment.objects.create(
                entity_type="category",
                entity_id=category.id,
                store=category.store,
                file=file
            )

        return category


class ProductCategoryResponseSerializer(serializers.ModelSerializer):
    """
    Used for listing categories with attachments and subcategories.
    """

    attachments = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = "__all__"

    def get_attachments(self, obj):
        """
        Returns all attachments linked to this category.
        """

        return AttachmentSerializer(
            Attachment.objects.filter(
                entity_type="category",
                entity_id=obj.id,
                store=obj.store
            ),
            many=True
        ).data

    def get_subcategories(self, obj):
        """
        Recursively returns child categories.
        """

        return ProductCategoryResponseSerializer(
            obj.subcategories.all(),
            many=True
        ).data


class ProductCategoryUpdateSerializer(serializers.ModelSerializer):
    """
    Used for updating category details and attachments.
    """

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
        """
        Updates category fields, parent,
        and optionally adds new attachments.
        """

        attachments = validated_data.pop("attachments", [])
        parent_id = validated_data.pop("parent_id", None)

        if parent_id:
            validated_data["parent"] = ProductCategory.objects.get(id=parent_id)

        instance = super().update(instance, validated_data)

        # Save new attachments
        for file in attachments:
            Attachment.objects.create(
                entity_type="category",
                entity_id=instance.id,
                store=instance.store,
                file=file
            )

        return instance


class ProductCategoryNestedSerializer(serializers.ModelSerializer):
    """
    Minimal category serializer used inside Product response.
    """

    parent = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ("id", "name", "slug", "parent", "subcategories")

    def get_parent(self, obj):
        """
        Returns parent category details.
        """

        if obj.parent:
            return {
                "id": obj.parent.id,
                "name": obj.parent.name,
                "slug": obj.parent.slug,
            }
        return None

    def get_subcategories(self, obj):
        """
        Returns immediate child categories.
        """

        return [
            {
                "id": sub.id,
                "name": sub.name,
                "slug": sub.slug,
            }
            for sub in obj.subcategories.all()
        ]


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
    primary_category = ProductCategoryNestedSerializer(read_only=True)
    brand = BrandNestedSerializer(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "description", "short_description",
            "is_active", "is_adult", "avg_rating", "review_count",
            "primary_category", "brand"
        )

class ProductVariantPublicSerializer(serializers.ModelSerializer):
    """
    Public serializer:
    - Shows real price
    - Hides inventory & internal flags
    """

    options = ProductVariantOptionSerializer(many=True, read_only=True)
    attachments = serializers.SerializerMethodField()
    product = ProductNestedInVariantSerializer(read_only=True) 

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "product",
            "price",       # ✅ REAL price
            "options",
            "attachments",
            "mrp"
        ]
        def get_options(self, obj):
            request = self.context.get("request")
            color_ids = request.query_params.get("color") if request else None

            qs = obj.options.all()

            if color_ids:
                qs = qs.filter(
                    id__in=color_ids.split(","),
                    key="color"
                )

            return ProductVariantOptionSerializer(qs, many=True).data
    
    def get_attachments(self, obj):
        """
        Public variant images.
        """
        return AttachmentSerializer(
            Attachment.objects.filter(
                entity_type="variation",
                entity_id=obj.id,
                store=obj.product.store
            ),
            many=True
        ).data


class ProductVariantPrivateSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.SerializerMethodField()
    options = ProductVariantOptionSerializer(many=True, read_only=True)
    attachments = serializers.SerializerMethodField()
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
            "mrp"
        )


    def get_is_low_stock(self, obj):
        return obj.quantity <= 20

    def get_attachments(self, obj):
        return AttachmentSerializer(
            Attachment.objects.filter(
                entity_type="variation",
                entity_id=obj.id,
                store=obj.product.store
            ),
            many=True
        ).data




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
from django.db.models import Sum
from rest_framework import serializers

class ProductSerializer(serializers.ModelSerializer):
    total_quantity = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    low_stock_variants = serializers.SerializerMethodField()
    primary_category = ProductCategoryNestedSerializer(read_only=True)
    brand = BrandNestedSerializer(read_only=True)

    # Nested variants for creation
    variants = ProductVariantItemSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "description", "short_description", "is_active",
            "is_adult", "avg_rating", "review_count", "created_at", "updated_at",
            "store", "primary_category", "brand",
            "total_quantity", "is_low_stock", "low_stock_variants",
            "variants",
        )
        read_only_fields = ("store", "slug", "created_at", "updated_at")

    def get_total_quantity(self, obj):
        total = obj.variants.aggregate(total_qty=Sum("quantity"))["total_qty"]
        return total or 0

    def get_is_low_stock(self, obj):
        return obj.variants.filter(quantity__lte=20).exists()

    def get_low_stock_variants(self, obj):
        low_variants = obj.variants.filter(quantity__lte=20)
        return [
            {
                "variant_id": variant.id,
                "quantity": variant.quantity,
                "options": {opt.key: opt.value for opt in variant.options.all()},
            }
            for variant in low_variants
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        variants_data = validated_data.pop("variants", [])

        # Assign store from request.user
        validated_data["store"] = request.user.store
        product = Product.objects.create(**validated_data)

        # Create variants properly
        for variant_data in variants_data:
            options_dict = variant_data.pop("options", {})
            attachments = variant_data.pop("attachments", [])
            quantity = variant_data.pop("quantity", 0)


            variant = ProductVariant.objects.create(
                product=product,
                price=variant_data.get("price", 0),
                quantity=quantity,

            )

            # ✅ Create ProductVariantOption objects
            for key, value in options_dict.items():
                ProductVariantOption.objects.create(
                    variant=variant,
                    key=key,
                    value=value
                )

            # ✅ Save attachments
            for idx, file in enumerate(attachments):
                Attachment.objects.create(
                    store=product.store,
                    entity_type="variation",
                    entity_id=variant.id,
                    file=file,
                    is_primary=(idx == 0)
                )

        return product



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
    variant_id = serializers.UUIDField(required=False)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(max_length=150)
    review_text = serializers.CharField()

    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        max_length=5
    )

    def validate(self, data):
        """
        Ensures user has purchased product before reviewing.
        """

        user = self.context["request"].user

        # Placeholder for purchase validation
        has_purchased = True
        if not has_purchased:
            raise serializers.ValidationError("Only verified buyers can review")

        return data

    def create(self, validated_data):
        """
        Creates review and stores attachments.
        """

        request = self.context["request"]
        attachments = validated_data.pop("attachments", [])

        review = Review.objects.create(
            user=request.user,
            product_id=validated_data["product_id"],
            variant_id=validated_data.get("variant_id"),
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
    """
    Used for importing products via JSON or CSV.
    """

    name = serializers.CharField(max_length=255)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_active = serializers.BooleanField(default=True)
    category = serializers.CharField(required=False, allow_blank=True)
    brand = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        """
        Creates product by mapping category and brand by name.
        """

        request = self.context["request"]
        store = request.user.store

        category_name = validated_data.pop("category", None)
        brand_name = validated_data.pop("brand", None)

        category = None
        if category_name:
            category = ProductCategory.objects.filter(
                name=category_name,
                store=store
            ).first()

        brand = None
        if brand_name:
            brand = Brand.objects.filter(
                name=brand_name,
                store=store
            ).first()

        return Product.objects.create(
            store=store,
            primary_category=category,
            brand=brand,
            **validated_data
        )
