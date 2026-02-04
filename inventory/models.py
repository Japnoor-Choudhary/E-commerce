import uuid
from django.db import models
from products.models import Product, ProductVariant
from organization.models import Store


class Inventory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="inventories"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="inventory"
    )

    variation = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="inventory"
    )

    quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("store", "product", "variation")
        ordering = ["store", "product"]

    def __str__(self):
        if self.variation:
            return f"{self.product.name} ({self.variation.value}) - {self.quantity}"
        return f"{self.product.name} - {self.quantity}"
