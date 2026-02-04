from decimal import Decimal
from django.db import transaction
from orders.models import Coupon, CouponUsage


def validate_and_calculate_coupon(
    *,
    coupon_code: str,
    user,
    subtotal: Decimal
):
    """
    Validates coupon and returns discount amount + coupon object.
    Does NOT increment usage.
    """

    with transaction.atomic():

        try:
            coupon = Coupon.objects.select_for_update().get(
                code=coupon_code,
                active=True
            )
        except Coupon.DoesNotExist:
            raise ValueError("Invalid or inactive coupon")

        # Date validation
        if not coupon.is_within_date():
            coupon.deactivate()
            raise ValueError("Coupon expired")

        # Minimum order amount
        if subtotal < coupon.min_order_amount:
            raise ValueError("Order amount too low for this coupon")

        # Total User Limit
        if coupon.total_user_limit is not None:
            total_users_used = CouponUsage.objects.filter(
                coupon=coupon
            ).values("user").distinct().count()

            if total_users_used >= coupon.total_user_limit:
                coupon.deactivate()
                raise ValueError("Coupon usage limit reached")

        # Per-user usage limit
        usage, _ = CouponUsage.objects.get_or_create(
            coupon=coupon,
            user=user
        )

        if coupon.usage_limit_per_user and coupon.usage_limit_per_user > 0:
            if usage.times_used >= coupon.usage_limit_per_user:
                raise ValueError(
                    "You have already used this coupon maximum times"
                )

        # Discount calculation
        discount = (subtotal * coupon.discount_percent) / Decimal("100")

        if coupon.max_discount_amount:
            discount = min(discount, coupon.max_discount_amount)

        return discount, coupon
