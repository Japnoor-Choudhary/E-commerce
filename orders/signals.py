from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction

from inventory.models import Inventory
from .models import Order


# ---------------------------
# Order status email
# ---------------------------
@receiver(post_save, sender=Order)
def order_status_email(sender, instance, created, **kwargs):
    if created:
        return

    user = instance.user
    if not user or not user.email:
        return

    if instance.status == "confirmed":
        send_mail(
            subject="Your order has been confirmed 🎉",
            message=(
                f"Hi {user.first_name or 'Customer'},\n\n"
                f"Your order {instance.id} has been confirmed.\n"
                f"We are preparing it for shipment.\n\n"
                f"Thank you for shopping with us!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

    elif instance.status == "delivered":
        send_mail(
            subject="Your order has been delivered 📦",
            message=(
                f"Hi {user.first_name or 'Customer'},\n\n"
                f"Your order {instance.id} has been successfully delivered.\n\n"
                f"We hope you love your purchase ❤️"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )


# ---------------------------
# AUTO DECREASE inventory on CONFIRM
# ---------------------------
@receiver(post_save, sender=Order)
@transaction.atomic
def decrease_inventory_on_confirm(sender, instance, **kwargs):
    previous_status = instance.tracker.previous("status")

    # Only run once: pending → confirmed
    if previous_status == "confirmed":
        return

    if instance.status != "confirmed":
        return

    for item in instance.items.select_related("product", "variation"):
        inventory = Inventory.get_inventory(
            store=item.product.store,
            product=item.product,
            variation=item.variation,
            lock=True
        )

        if not inventory or inventory.quantity < item.quantity:
            raise Exception(
                f"Insufficient stock for {item.product.name}"
            )

        inventory.quantity -= item.quantity
        inventory.save(update_fields=["quantity", "updated_at"])


# ---------------------------
# AUTO RESTORE inventory on CANCEL / RETURN
# ---------------------------
@receiver(post_save, sender=Order)
@transaction.atomic
def restore_inventory_on_cancel(sender, instance, **kwargs):
    previous_status = instance.tracker.previous("status")

    # Restore only if it was confirmed before
    if previous_status != "confirmed":
        return

    if instance.status not in ["cancelled", "returned"]:
        return

    for item in instance.items.select_related("product", "variation"):
        inventory = Inventory.get_inventory(
            store=item.product.store,
            product=item.product,
            variation=item.variation,
            lock=True
        )

        if inventory:
            inventory.quantity += item.quantity
            inventory.save(update_fields=["quantity", "updated_at"])
