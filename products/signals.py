# products/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from inventory.models import Inventory
from .models import Product, ProductVariant


@receiver(post_save, sender=Product)
def create_product_inventory(sender, instance, created, **kwargs):
    if not created:
        return

    Inventory.objects.get_or_create(
        store=instance.store,
        product=instance,
        variation=None,
        defaults={"quantity": 0}
    )


@receiver(post_save, sender=ProductVariant)
def create_variant_inventory(sender, instance, created, **kwargs):
    if not created:
        return

    Inventory.objects.get_or_create(
        store=instance.product.store,
        product=instance.product,
        variation=instance,
        defaults={"quantity": 0}
    )
