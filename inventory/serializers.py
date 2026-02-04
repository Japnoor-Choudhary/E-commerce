from rest_framework import serializers
from .models import Inventory


class InventoryReportSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    variation_value = serializers.CharField(source="variation.value", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)

    class Meta:
        model = Inventory
        fields = [
            "id",
            "store",
            "store_name",
            "product",
            "product_name",
            "variation",
            "variation_value",
            "quantity",
            "updated_at"
        ]
        read_only_fields = [
            "id",
            "store_name",
            "product_name",
            "variation_value",
            "updated_at"
        ]
