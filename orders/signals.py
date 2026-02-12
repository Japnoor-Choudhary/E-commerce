from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.db.models import F

from .models import Order
from products.models import ProductVariant


# =====================================================
# STOCK MANAGEMENT
# =====================================================

@receiver(post_save, sender=Order)
def decrease_stock_on_confirm(sender, instance, **kwargs):
    """
    Deduct stock ONLY when order status changes → confirmed
    """
    previous_status = instance.tracker.previous("status")

    if previous_status == "confirmed":
        return

    if instance.status != "confirmed":
        return

    def deduct():
        for item in instance.items.select_related("variation"):
            variant = item.variation

            if variant.quantity < item.quantity:
                raise Exception(
                    f"Insufficient stock for {item.product.name}"
                )

            ProductVariant.objects.filter(
                id=variant.id
            ).update(quantity=F("quantity") - item.quantity)

    transaction.on_commit(deduct)


@receiver(post_save, sender=Order)
def restore_stock_on_cancel(sender, instance, **kwargs):
    """
    Restore stock ONLY when confirmed → cancelled/returned
    """
    previous_status = instance.tracker.previous("status")

    if previous_status != "confirmed":
        return

    if instance.status not in ["cancelled", "returned"]:
        return

    def restore():
        for item in instance.items.select_related("variation"):
            ProductVariant.objects.filter(
                id=item.variation.id
            ).update(quantity=F("quantity") + item.quantity)

    transaction.on_commit(restore)


# =====================================================
# EMAIL NOTIFICATIONS
# =====================================================

@receiver(post_save, sender=Order)
def order_confirmed_email(sender, instance, **kwargs):
    previous_status = instance.tracker.previous("status")

    if previous_status == "confirmed":
        return

    if instance.status != "confirmed":
        return

    user = instance.user
    if not user or not user.email:
        return

    def send():
        send_mail(
            subject="Your order has been placed successfully 🎉",
            message=(
                f"Hi {user.first_name or 'Customer'},\n\n"
                f"Your order {instance.id} has been confirmed.\n"
                f"We’ll notify you once it’s delivered.\n\n"
                f"Thank you for shopping with us ❤️"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

    transaction.on_commit(send)


@receiver(post_save, sender=Order)
def order_delivered_email(sender, instance, **kwargs):
    previous_status = instance.tracker.previous("status")

    if previous_status == "delivered":
        return

    if instance.status != "delivered":
        return

    user = instance.user
    if not user or not user.email:
        return

    def send():
        send_mail(
            subject="Your order has been delivered 📦",
            message=(
                f"Hi {user.first_name or 'Customer'},\n\n"
                f"Your order {instance.id} has been delivered.\n\n"
                f"We hope you loved your purchase ❤️"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

    transaction.on_commit(send)
