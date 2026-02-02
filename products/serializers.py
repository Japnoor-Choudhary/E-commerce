from rest_framework import serializers
from .models import (
    Product,
    ProductCategory,
    ProductSpecification,
    ProductVariation,
    Attachment,
    ProductDetailType,
)


class ProductCategoryCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = ProductCategory
        fields = "__all__"

    def create(self, validated_data):
        attachments = validated_data.pop("attachments", [])
        category = ProductCategory.objects.create(**validated_data)

        for file in attachments:
            Attachment.objects.create(
                entity_type="category",
                entity_id=category.id,
                store=category.store,   # ✅ REQUIRED
                file=file,
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
                entity_id=obj.id
            ),
            many=True
        ).data


class ProductCategoryUpdateSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = ProductCategory
        fields = "__all__"

    def update(self, instance, validated_data):
        attachments = validated_data.pop("attachments", [])
        instance = super().update(instance, validated_data)

        for file in attachments:
            Attachment.objects.create(
                entity_type="category",
                entity_id=instance.id,
                store=instance.store,   # ✅ REQUIRED
                file=file,
            )

        return instance



class ProductSerializer(serializers.ModelSerializer):
    categories = ProductCategoryResponseSerializer(
        source="primary_category",
        read_only=True
    )

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("slug", "created_at", "updated_at")


class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = "__all__"

    def update(self, instance, validated_data):
        new_key = validated_data.get("key", instance.key)
        new_value = validated_data.get("value", instance.value)

        # CASE 1: Key and value are the same → normal update (other fields)
        if new_key == instance.key and new_value == instance.value:
            return super().update(instance, validated_data)

        # CASE 2: Key exists and value is different → create variation
        if new_key == instance.key and new_value != instance.value:
            ProductVariation.objects.create(
                product=instance.product,
                detail_type=instance.detail_type,
                key=new_key,
                value=new_value,
            )
            # update other fields in specification if any (like detail_type)
            for field in validated_data:
                if field not in ["key", "value"]:
                    setattr(instance, field, validated_data[field])
            instance.save(update_fields=[f for f in validated_data if f not in ["key", "value"]])
            return instance

        # CASE 3: Key changed → update specification normally
        return super().update(instance, validated_data)


class ProductVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariation
        fields = "__all__"

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = "__all__"
        read_only_fields = ("file_type", "slug", "created_at", "updated_at")


class AttachmentBulkUploadSerializer(serializers.Serializer):
    entity_type = serializers.ChoiceField(choices=Attachment.ENTITY_TYPE_CHOICES)
    entity_id = serializers.UUIDField()
    store = serializers.UUIDField()   # ✅ REQUIRED
    files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True
    )

    def create(self, validated_data):
        files = validated_data.pop("files")
        store_id = validated_data.pop("store")

        attachments = []
        for file in files:
            attachment = Attachment.objects.create(
                store_id=store_id,
                file=file,
                **validated_data
            )
            attachments.append(attachment)

        return attachments


class ProductDetailTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDetailType
        fields = "__all__"
        
        