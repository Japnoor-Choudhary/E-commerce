from rest_framework import serializers
from .models import (
    CartItem,
    Wishlist,
    WishlistItem,
    Order,
    OrderItem,
    OrderTracking,
    Coupon,
    CouponUsage
)
from products.models import Product, ProductVariant


# ---------------------------
# Cart
# ---------------------------
class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    variation_name = serializers.CharField(source="variation.name", read_only=True)
    unit_price = serializers.SerializerMethodField()
    payable_amount = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        exclude = ("user",)

    def get_unit_price(self, obj):
        if obj.variation:
            return obj.variation.price
        return obj.product.price

    def get_payable_amount(self, obj):
        return self.get_unit_price(obj) * obj.quantity
    
class CartSummarySerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    # delivery_fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    
class CartApplyCouponSerializer(serializers.Serializer):
    coupon_code = serializers.CharField(max_length=50)


# ---------------------------
# Wishlist
# ---------------------------

class WishlistItemCreateSerializer(serializers.Serializer):
    product = serializers.UUIDField()
    
class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = "__all__"
        read_only_fields = ("user", "is_system")

class WishlistItemBulkCreateSerializer(serializers.Serializer):
    products = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    wishlist = serializers.UUIDField(required=False)

    def validate_products(self, value):
        if not Product.objects.filter(id__in=value).count() == len(set(value)):
            raise serializers.ValidationError("One or more products are invalid")
        return value

    def validate_wishlist(self, value):
        user = self.context["request"].user
        if not Wishlist.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Invalid wishlist")
        return value


class WishlistItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    wishlist_name = serializers.CharField(source="wishlist.name", read_only=True)

    class Meta:
        model = WishlistItem
        fields = "__all__"


# ---------------------------
# Coupon
# ---------------------------
class CouponSerializer(serializers.ModelSerializer):
    total_users_used = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Coupon
        fields = "__all__"
        read_only_fields = ("id", "created_at")

    def get_total_users_used(self, obj):
        return obj.usages.count()

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")

        if start and end and start >= end:
            raise serializers.ValidationError(
                "End date must be greater than start date"
            )

        return attrs



# ---------------------------
# Orders
# ---------------------------
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    variation_name = serializers.CharField(source="variation.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTracking
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    tracking = OrderTrackingSerializer(many=True, read_only=True)
    coupon = CouponSerializer(read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
