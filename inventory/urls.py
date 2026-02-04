from django.urls import path
from .views import InventoryReportAPI

urlpatterns = [
    path(
        "inventory/report/",
        InventoryReportAPI.as_view(),
        name="inventory-report",
    ),
]
