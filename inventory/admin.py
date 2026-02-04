from django.contrib import admin
from .models import Inventory


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "store",
        "product",
        "variation",
        "quantity",
        "updated_at",
    )
    list_filter = (
        "store",
        "product",
        "variation",
    )
    search_fields = (
        "product__name",
        "variation__value",
        "store__name",
    )
    ordering = ("store", "product")
    autocomplete_fields = ("product", "variation", "store")
