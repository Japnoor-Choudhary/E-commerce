from django.contrib import admin
from .models import (
    CartItem,
    Wishlist,
    WishlistItem,
    Coupon,
    CouponUsage,
    Order,
    OrderItem,
    OrderTracking,
    CartCoupon
)

# ============================
# Cart
# ============================
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "variation", "quantity", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "product__name")
    ordering = ("-created_at",)

@admin.register(CartCoupon)
class CartCouponAdmin(admin.ModelAdmin):
    list_display = ("user", "coupon", "applied_at")
    search_fields = ("user__email", "coupon__code")
    list_filter = ("coupon", "applied_at")
    ordering = ("-applied_at",)
    autocomplete_fields = ("user", "coupon")


# ============================
# Wishlist
# ============================
@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("id", "wishlist", "product", "added_at")
    search_fields = ("wishlist__name", "product__name", "wishlist__user__email")
    list_filter = ("added_at",)
    ordering = ("-added_at",)
    autocomplete_fields = ("wishlist", "product")


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name", "created_at")
    search_fields = ("user__email", "name")
    ordering = ("created_at",)


# ============================
# Coupons
# ============================



@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_type",
        "discount_value",
        "max_discount_amount",
        "min_order_amount",
        "active",
    )

    list_filter = ("active", "discount_type")
    search_fields = ("code",)
    ordering = ("-id",)



@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ("coupon", "user", "times_used")
    search_fields = ("coupon__code", "user__email")
    list_filter = ("coupon",)


# ============================
# Orders
# ============================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ("product", "variation")
    readonly_fields = ("price",)


class OrderTrackingInline(admin.TabularInline):
    model = OrderTracking
    extra = 0
    readonly_fields = ("updated_at",)
    ordering = ("-updated_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "subtotal",
        "discount_amount",
        "total_amount",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__email")
    ordering = ("-created_at",)
    autocomplete_fields = ("user", "coupon", "shipping_address", "reordered_from")
    readonly_fields = ("subtotal", "discount_amount", "total_amount", "created_at", "updated_at")
    inlines = [OrderItemInline, OrderTrackingInline]


# ============================
# Order Items (optional standalone view)
# ============================
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "variation", "quantity", "price")
    search_fields = ("order__id", "product__name")
    autocomplete_fields = ("order", "product", "variation")


# ============================
# Order Tracking (optional standalone view)
# ============================
@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "updated_at")
    list_filter = ("status",)
    ordering = ("-updated_at",)
