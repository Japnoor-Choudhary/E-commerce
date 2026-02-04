from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from collections import defaultdict
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F
from decimal import Decimal
from django.utils import timezone
from products.models import Product
from inventory.models import Inventory
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
from .serializers import (
    CartItemSerializer,
    WishlistSerializer,
    WishlistItemSerializer,
    OrderSerializer,
    WishlistItemCreateSerializer
)


# ---------------------------
#  Helper Functions
# ---------------------------
def apply_coupon(subtotal, user, coupon_code=None):
    if not coupon_code:
        return Decimal("0.00"), None

    try:
        coupon = Coupon.objects.get(
            code=coupon_code,
            active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )
    except Coupon.DoesNotExist:
        raise ValueError("Invalid or expired coupon")

    if subtotal < coupon.min_order_amount:
        raise ValueError("Order amount too low for this coupon")

    usage, _ = CouponUsage.objects.get_or_create(coupon=coupon, user=user)
    if coupon.usage_limit_per_user and usage.times_used >= coupon.usage_limit_per_user:
        raise ValueError("You have already used this coupon the maximum number of times")

    discount = (subtotal * coupon.discount_percent) / 100
    if coupon.max_discount_amount:
        discount = min(discount, coupon.max_discount_amount)

    return discount, coupon



def get_or_create_system_wishlist(user):
    """
    Always returns the system 'Wishlist'
    """
    wishlist, created = Wishlist.objects.get_or_create(
        user=user,
        is_system=True,
        defaults={
            "name": "Wishlist",
            "is_primary": True,
        }
    )

    if created:
        Wishlist.objects.filter(user=user).exclude(id=wishlist.id).update(is_primary=False)

    return wishlist


def get_primary_wishlist(user):
    """
    Returns primary wishlist or system wishlist
    """
    primary = Wishlist.objects.filter(user=user, is_primary=True).first()
    if primary:
        return primary
    return get_or_create_system_wishlist(user)

# ---------------------------
# Cart APIs
# ---------------------------
class CartListCreateAPI(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartDeleteAPI(generics.DestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)


# ---------------------------
# Wishlist APIs
# ---------------------------
class WishlistAPI(generics.ListCreateAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        # Remove primary from previous wishlists
        Wishlist.objects.filter(user=self.request.user).update(is_primary=False)

        serializer.save(
            user=self.request.user,
            is_primary=True,
            is_system=False
        )



class WishlistDeleteAPI(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)


class WishlistItemAPI(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WishlistItem.objects.filter(
            wishlist__user=self.request.user
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WishlistItemCreateSerializer
        return WishlistItemSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        product_id = serializer.validated_data["product"]
        product = Product.objects.get(id=product_id)

        # 1️⃣ Ensure system wishlist exists
        system_wishlist = get_or_create_system_wishlist(user)

        # 2️⃣ Get primary wishlist
        primary_wishlist = get_primary_wishlist(user)

        # 3️⃣ Always save to SYSTEM wishlist
        WishlistItem.objects.get_or_create(
            wishlist=system_wishlist,
            product=product
        )

        # 4️⃣ Save to PRIMARY wishlist if different
        if primary_wishlist.id != system_wishlist.id:
            WishlistItem.objects.get_or_create(
                wishlist=primary_wishlist,
                product=product
            )


class WishlistItemByFolderAPI(generics.ListAPIView):
    serializer_class = WishlistItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        wishlist_id = self.kwargs["wishlist_id"]

        return WishlistItem.objects.filter(
            wishlist__id=wishlist_id,
            wishlist__user=self.request.user
        ).select_related("product", "wishlist")

class WishlistItemDeleteAPI(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = WishlistItem.objects.all()
    serializer_class = WishlistItemSerializer

    def get_queryset(self):
        # User safety
        return WishlistItem.objects.filter(wishlist__user=self.request.user)

    def perform_destroy(self, instance):
        """
        Business rules:
        1. Delete from system → delete from ALL folders
        2. Delete from last custom folder → delete from system + custom
        3. Otherwise → delete only from selected folder
        """

        product = instance.product
        user = self.request.user

        all_items = WishlistItem.objects.filter(
            product=product,
            wishlist__user=user
        )

        system_item = all_items.filter(wishlist__is_system=True).first()
        custom_items = all_items.filter(wishlist__is_system=False)

        # 🟥 CASE 3: deleting from SYSTEM wishlist
        if instance.wishlist.is_system:
            all_items.delete()
            return

        # 🟨 CASE 2: only ONE custom folder + system
        if custom_items.count() == 1 and system_item:
            all_items.delete()
            return

        # 🟩 CASE 1: multiple custom folders
        instance.delete()
        
class WishlistProductGroupedAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = (
            WishlistItem.objects
            .filter(wishlist__user=request.user)
            .select_related("product", "wishlist")
        )

        product_map = defaultdict(lambda: {
            "product_id": None,
            "product_name": None,
            "folders": []
        })

        for item in items:
            pid = str(item.product.id)

            product_map[pid]["product_id"] = pid
            product_map[pid]["product_name"] = item.product.name

            product_map[pid]["folders"].append({
                "wishlist_id": str(item.wishlist.id),
                "wishlist_name": item.wishlist.name,
                "is_system": item.wishlist.is_system,
                "is_primary": item.wishlist.is_primary,
            })

        return Response(list(product_map.values()))

# ---------------------------
# Place Order API
# ---------------------------
class PlaceOrderAPI(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        cart_items = CartItem.objects.filter(user=user)

        if not cart_items.exists():
            return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Check inventory
        for item in cart_items:
            inventory = Inventory.objects.select_for_update().filter(
                store=item.product.store,
                product=item.product,
                variation=item.variation
            ).first()
            if not inventory or inventory.quantity < item.quantity:
                return Response({"detail": f"Insufficient stock for {item.product.name}"},
                                status=status.HTTP_400_BAD_REQUEST)

        # Calculate subtotal
        subtotal = Decimal("0.00")
        for item in cart_items:
            price = item.variation.price if item.variation else item.product.price
            subtotal += price * item.quantity

        # Apply coupon
        coupon_code = request.data.get("coupon_code")
        try:
            discount, coupon = apply_coupon(subtotal, user, coupon_code)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = subtotal - discount

        # Create order
        order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            discount_amount=discount,
            total_amount=total_amount,
            status="pending",
            coupon=coupon
        )

        # Create order items & reduce inventory
        for item in cart_items:
            price = item.variation.price if item.variation else item.product.price
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variation=item.variation,
                quantity=item.quantity,
                price=price
            )
            Inventory.objects.filter(
                store=item.product.store,
                product=item.product,
                variation=item.variation
            ).update(quantity=F("quantity") - item.quantity)

        # Increment coupon usage
        if coupon:
            CouponUsage.objects.filter(coupon=coupon, user=user).update(times_used=F("times_used") + 1)

        # Create initial tracking
        OrderTracking.objects.create(order=order, status="pending", note="Order placed")

        # Clear cart
        cart_items.delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ---------------------------
# Reorder API
# ---------------------------
class ReOrderAPI(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, order_id):
        old_order = get_object_or_404(Order, id=order_id, user=request.user)
        subtotal = Decimal("0.00")

        # Inventory check
        for item in old_order.items.select_related("product", "variation"):
            inventory = Inventory.objects.select_for_update().filter(
                store=item.product.store,
                product=item.product,
                variation=item.variation
            ).first()
            if not inventory or inventory.quantity < item.quantity:
                return Response({"detail": f"Insufficient stock for {item.product.name}"},
                                status=status.HTTP_400_BAD_REQUEST)
            price = item.variation.price if item.variation else item.product.price
            subtotal += price * item.quantity

        # Create new order
        new_order = Order.objects.create(
            user=request.user,
            shipping_address=old_order.shipping_address,
            subtotal=subtotal,
            discount_amount=Decimal("0.00"),
            total_amount=subtotal,
            status="pending",
            reordered_from=old_order
        )

        # Create items & reduce inventory
        for item in old_order.items.all():
            price = item.variation.price if item.variation else item.product.price
            OrderItem.objects.create(
                order=new_order,
                product=item.product,
                variation=item.variation,
                quantity=item.quantity,
                price=price
            )
            Inventory.objects.filter(
                store=item.product.store,
                product=item.product,
                variation=item.variation
            ).update(quantity=F("quantity") - item.quantity)

        # Initial tracking
        OrderTracking.objects.create(order=new_order, status="pending",
                                     note="Reordered with current prices (no coupon applied)")

        serializer = OrderSerializer(new_order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
