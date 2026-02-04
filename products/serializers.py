from rest_framework import serializers
from .models import *

# -----------------------------
# Attachment
# -----------------------------
class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = "__all__"
        read_only_fields = ("store", "file_type", "slug", "created_at", "updated_at")

# -----------------------------
# Product Category
# -----------------------------
class ProductCategoryCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )

    class Meta:
        model = ProductCategory
        fields = "__all__"
        read_only_fields = ("store",)

    def create(self, validated_data):
        attachments = validated_data.pop("attachments", [])
        category = super().create(validated_data)
        for file in attachments:
            Attachment.objects.create(
                entity_type="category",
                entity_id=category.id,
                store=category.store,
                file=file
            )
        return category

class ProductCategoryResponseSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = "__all__"

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
        child=serializers.FileField(), write_only=True, required=False
    )

    class Meta:
        model = ProductCategory
        exclude = ("store", "slug", "created_at", "updated_at")

    def update(self, instance, validated_data):
        attachments = validated_data.pop("attachments", [])
        instance = super().update(instance, validated_data)
        for file in attachments:
            Attachment.objects.create(
                entity_type="category",
                entity_id=instance.id,
                store=instance.store,
                file=file
            )
        return instance

# -----------------------------
# Product
# -----------------------------
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("store", "slug", "created_at", "updated_at")

# -----------------------------
# Product Specification
# -----------------------------
class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = "__all__"

# -----------------------------
# Product Variant & Options
# -----------------------------

class VariantOptionSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.CharField()
    
class ProductVariantOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantOption
        fields = "__all__"

class ProductVariantSerializer(serializers.ModelSerializer):
    options = ProductVariantOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "product",
            "price",
            "quantity",
            "options",
        ]

    def create(self, validated_data):
        options = validated_data.pop("options")

        variant = ProductVariant.objects.create(**validated_data)

        for opt in options:
            ProductVariantOption.objects.create(
                variant=variant,
                key=opt["key"],
                value=opt["value"]
            )

        return variant

class ProductVariantCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    variants = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )

    def create(self, validated_data):
        product = Product.objects.get(id=validated_data["product_id"])
        created_variants = []

        for variant_data in validated_data["variants"]:
            options = variant_data.pop("options", {})

            variant = ProductVariant.objects.create(
                product=product,
                price=variant_data.get("price", 0),
                quantity=variant_data.get("quantity", 0)
            )

            for key, value in options.items():
                ProductVariantOption.objects.create(
                    variant=variant,
                    key=key,
                    value=value
                )

            created_variants.append(variant)

        return created_variants

# -----------------------------
# Product Detail Type
# -----------------------------
class ProductDetailTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDetailType
        fields = "__all__"

# -----------------------------
# Attachment Bulk Upload
# -----------------------------
class AttachmentBulkUploadSerializer(serializers.Serializer):
    entity_type = serializers.ChoiceField(choices=Attachment.ENTITY_TYPE_CHOICES)
    entity_id = serializers.UUIDField()
    files = serializers.ListField(
        child=serializers.FileField(), write_only=True
    )

