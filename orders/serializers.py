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

    class Meta:
        model = CartItem
        fields = "__all__"


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
    class Meta:
        model = Coupon
        fields = "__all__"


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
