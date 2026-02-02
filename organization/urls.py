from django.urls import path
from .views import (
    CompanyListCreateAPIView,
    CompanyRetrieveUpdateDestroyAPIView,
    StoreListCreateAPIView,
    StoreRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    # Company
    path('companies/', CompanyListCreateAPIView.as_view(), name='company-list-create'),
    path('companies/<uuid:id>/', CompanyRetrieveUpdateDestroyAPIView.as_view(), name='company-detail'),

    # Store
    path('stores/', StoreListCreateAPIView.as_view(), name='store-list-create'),
    path('stores/<uuid:id>/', StoreRetrieveUpdateDestroyAPIView.as_view(), name='store-detail'),
]
