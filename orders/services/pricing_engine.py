# cart/services/pricing_engine.py
from decimal import Decimal
from .coupon_calculator import CouponCalculator
from .coupon_policy import CouponPolicy
from orders.models import Coupon


class PricingEngine:

    @staticmethod
    def apply(cart_items, user_coupon=None):
        product_prices = {}
        applied_discounts = {}
        total_discount = Decimal("0.00")

        for item in cart_items:
            price = item.variation.price if item.variation else item.product.price
            product_prices[item] = price * item.quantity
            applied_discounts[item] = Decimal("0.00")

        coupons = []

        # 1️⃣ Pre-applied coupons
        pre_applied = Coupon.objects.filter(
            active=True,
            is_pre_applied=True
        )

        coupons.extend(pre_applied)

        # 2️⃣ Manually applied coupon
        if user_coupon:
            coupons.append(user_coupon)

        coupons = sorted(
            coupons,
            key=lambda c: CouponPolicy.get_priority(c)
        )

        for coupon in coupons:
            for item, base_price in product_prices.items():

                if coupon.scope == "product" and item.product not in coupon.applicable_products.all():
                    continue

                if coupon.scope == "category" and item.product.primary_category not in coupon.applicable_categories.all():
                    continue

                remaining_price = base_price - applied_discounts[item]
                if remaining_price <= 0:
                    continue

                discount = CouponCalculator.calculate(remaining_price, coupon)

                max_allowed = CouponPolicy.max_allowed_discount(base_price)
                allowed = max_allowed - applied_discounts[item]

                discount = min(discount, allowed)
                if discount <= 0:
                    continue

                applied_discounts[item] += discount
                total_discount += discount

        total = sum(product_prices.values()) - total_discount

        return {
            "subtotal": sum(product_prices.values()),
            "discount": total_discount,
            "total": max(total, Decimal("0.00")),
        }
