# coupons/services/coupon_calculator.py
from decimal import Decimal
from .coupon_policy import CouponPolicy


class CouponCalculator:

    @staticmethod
    def calculate(price, coupon):
        if coupon.discount_type == "percent":
            discount = price * (coupon.discount_value / Decimal("100"))
        else:
            discount = coupon.discount_value

        if coupon.max_discount_amount:
            discount = min(discount, coupon.max_discount_amount)

        return max(discount, Decimal("0.00"))
