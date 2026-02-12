# coupons/services/coupon_policy.py
from decimal import Decimal


MAX_DISCOUNT_PERCENT = Decimal("0.80")  # 80% global cap


class CouponPolicy:
    @staticmethod
    def get_priority(coupon):
        if coupon.is_pre_applied:
            return 10
        if coupon.discount_type == "percent":
            return 60
        return 40

    @staticmethod
    def is_stackable(coupon):
        if coupon.is_pre_applied:
            return False
        if coupon.discount_type == "percent":
            return False
        return True

    @staticmethod
    def allowed_with_pre_applied(coupon):
        return coupon.discount_type == "flat"

    @staticmethod
    def max_allowed_discount(price):
        return price * MAX_DISCOUNT_PERCENT
