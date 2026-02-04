from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Inventory
from .serializers import InventoryReportSerializer


class InventoryReportAPI(generics.ListAPIView):
    serializer_class = InventoryReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Staff/Admin: only inventory for their store
        if hasattr(user, "store") and user.store:
            return Inventory.objects.filter(store=user.store).select_related("product", "variation")
        # Superuser / no store: all inventory
        return Inventory.objects.select_related("product", "variation").all()
