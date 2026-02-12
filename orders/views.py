from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from collections import defaultdict
from django.shortcuts import get_object_or_404
from .services.pricing_engine import PricingEngine
from django.db import transaction
from django.db.models import F
from decimal import Decimal
from accounts.permissions import IsAdmin

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
    WishlistItemBulkCreateSerializer,
    CartApplyCouponSerializer,
    CouponSerializer
)


# ---------------------------
# Helper functions
# ---------------------------
def get_or_create_system_wishlist(user):
    wishlist, created = Wishlist.objects.get_or_create(
        user=user,
        is_system=True,
        defaults={"name": "Wishlist", "is_primary": True}
    )
    if created:
        Wishlist.objects.filter(user=user).exclude(id=wishlist.id).update(is_primary=False)
    return wishlist

def get_primary_wishlist(user):
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

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        items = []
        for item in serializer.validated_data:
            obj, _ = CartItem.objects.update_or_create(
                user=request.user,
                product=item["product"],
                variation=item.get("variation"),
                defaults={"quantity": item.get("quantity", 1)},
            )
            items.append(obj)

        return Response(CartItemSerializer(items, many=True).data, status=status.HTTP_201_CREATED)


class CartDeleteAPI(generics.DestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)


# ---------------------------
# Cart Coupon APIs
# ---------------------------
class CartApplyCouponAPI(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartApplyCouponSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        coupon_code = serializer.validated_data["coupon_code"]

        cart_items = (
            CartItem.objects
            .select_related("product", "variation")
            .filter(user=user)
        )

        if not cart_items.exists():
            return Response(
                {"detail": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            coupon = Coupon.objects.get(code=coupon_code, active=True)
        except Coupon.DoesNotExist:
            return Response(
                {"detail": "Invalid or inactive coupon"},
                status=status.HTTP_400_BAD_REQUEST
            )

        pricing = PricingEngine.apply(
            cart_items=cart_items,
            user_coupon=coupon
        )

        return Response({
            "coupon": coupon.code,
            "subtotal": pricing["subtotal"],
            "discount": pricing["discount"],
            "total": pricing["total"],
        }, status=status.HTTP_200_OK)



class CartRemoveCouponAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        # Remove applied coupon (if stored in DB, clear here)
        return Response({"detail": "Coupon removed"}, status=status.HTTP_200_OK)


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
        Wishlist.objects.filter(user=self.request.user).update(is_primary=False)
        serializer.save(user=self.request.user, is_primary=True, is_system=False)


class WishlistDeleteAPI(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)


class WishlistItemAPI(generics.CreateAPIView):
    serializer_class = WishlistItemBulkCreateSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        product_ids = serializer.validated_data["products"]
        wishlist_id = serializer.validated_data.get("wishlist")

        system_wishlist = get_or_create_system_wishlist(user)
        primary_wishlist = Wishlist.objects.filter(id=wishlist_id, user=user).first() if wishlist_id else get_primary_wishlist(user)

        created = []
        for product_id in product_ids:
            WishlistItem.objects.get_or_create(wishlist=system_wishlist, product_id=product_id)
            if primary_wishlist.id != system_wishlist.id:
                WishlistItem.objects.get_or_create(wishlist=primary_wishlist, product_id=product_id)
            created.append(product_id)

        return Response({
            "added_products": created,
            "system_wishlist": str(system_wishlist.id),
            "target_wishlist": str(primary_wishlist.id)
        }, status=status.HTTP_201_CREATED)


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
    serializer_class = WishlistItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WishlistItem.objects.filter(wishlist__user=self.request.user)

    def perform_destroy(self, instance):
        product = instance.product
        user = self.request.user

        all_items = WishlistItem.objects.filter(product=product, wishlist__user=user)
        system_item = all_items.filter(wishlist__is_system=True).first()
        custom_items = all_items.filter(wishlist__is_system=False)

        if instance.wishlist.is_system or (custom_items.count() == 1 and system_item):
            all_items.delete()
        else:
            instance.delete()


class WishlistProductGroupedAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = WishlistItem.objects.filter(wishlist__user=request.user).select_related("product", "wishlist")
        product_map = defaultdict(lambda: {"product_id": None, "product_name": None, "folders": []})

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


# =====================================================
# PLACE ORDER
# =====================================================

class PlaceOrderAPI(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user

        cart_items = (
            CartItem.objects
            .select_related("product", "variation")
            .filter(user=user)
        )

        if not cart_items.exists():
            return Response(
                {"detail": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------
        # Validate stock ONLY
        # ---------------------------
        for item in cart_items:
            if not item.variation:
                return Response(
                    {"detail": "Product variation is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if item.variation.quantity < item.quantity:
                return Response(
                    {"detail": f"Insufficient stock for {item.product.name}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # ---------------------------
        # Apply coupon
        # ---------------------------
        coupon = None
        coupon_code = request.data.get("coupon_code")

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, active=True)
            except Coupon.DoesNotExist:
                return Response(
                    {"detail": "Invalid or inactive coupon"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        pricing = PricingEngine.apply(
            cart_items=cart_items,
            user_coupon=coupon
        )

        # ---------------------------
        # Create order
        # ---------------------------
        order = Order.objects.create(
            user=user,
            subtotal=pricing["subtotal"],
            discount_amount=pricing["discount"],
            total_amount=pricing["total"],
            status="pending",
            coupon=coupon
        )

        # ---------------------------
        # Create order items
        # ---------------------------
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variation=item.variation,
                quantity=item.quantity,
                price=item.variation.price
            )

        # ---------------------------
        # Coupon usage
        # ---------------------------
        if coupon:
            usage, _ = CouponUsage.objects.select_for_update().get_or_create(
                coupon=coupon,
                user=user
            )
            usage.times_used += 1
            usage.save()

        # ---------------------------
        # Track order
        # ---------------------------
        OrderTracking.objects.create(
            order=order,
            status="pending",
            note="Order placed"
        )

        cart_items.delete()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

# =====================================================
# RE-ORDER API
# =====================================================

class ReOrderAPI(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, order_id):
        user = request.user

        # Fetch previous order
        old_order = get_object_or_404(
            Order.objects.prefetch_related("items__variation", "items__product"),
            id=order_id,
            user=user
        )

        if not old_order.items.exists():
            return Response(
                {"detail": "Nothing to reorder"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------
        # Validate stock & calculate subtotal
        # ---------------------------
        subtotal = Decimal("0.00")

        for item in old_order.items.all():
            variant = item.variation

            if not variant:
                return Response(
                    {"detail": f"Variation missing for {item.product.name}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if variant.quantity < item.quantity:
                return Response(
                    {"detail": f"Insufficient stock for {item.product.name}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subtotal += item.quantity * item.price

        # ---------------------------
        # Create new order
        # ---------------------------
        new_order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            discount_amount=Decimal("0.00"),
            total_amount=subtotal,
            status="pending",
            reordered_from=old_order
        )

        # ---------------------------
        # Create order items
        # ---------------------------
        for item in old_order.items.all():
            OrderItem.objects.create(
                order=new_order,
                product=item.product,
                variation=item.variation,
                quantity=item.quantity,
                price=item.price  # current stored price
            )

        # ---------------------------
        # Track reorder
        # ---------------------------
        OrderTracking.objects.create(
            order=new_order,
            status="pending",
            note="Reordered with current availability (no coupon applied)"
        )

        return Response(
            OrderSerializer(new_order).data,
            status=status.HTTP_201_CREATED
        )

# ---------------------------
# Coupon Admin APIs
# ---------------------------
class CouponListCreateAPI(generics.ListCreateAPIView):
    queryset = Coupon.objects.all().order_by("-created_at")
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class CouponRetrieveUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
