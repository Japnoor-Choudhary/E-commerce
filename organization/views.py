from rest_framework import generics
from .models import Company, Store
from .serializers import CompanySerializer, StoreSerializer


# =====================================================
# Company APIs
# =====================================================

class CompanyListCreateAPIView(generics.ListCreateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer


class CompanyRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Company.objects.prefetch_related('stores')
    serializer_class = CompanySerializer
    lookup_field = 'id'



# =====================================================
# Store APIs
# =====================================================

class StoreListCreateAPIView(generics.ListCreateAPIView):
    queryset = Store.objects.select_related('company')
    serializer_class = StoreSerializer


class StoreRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Store.objects.select_related('company')
    serializer_class = StoreSerializer
    lookup_field = 'id'

