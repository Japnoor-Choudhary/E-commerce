from django.urls import path
from .views import (
    ProductCRUDAPI,ProductUpdateDeleteAPI,
    CategoryCRUDAPI,CategoryUpdateDeleteAPI,
    ProductSpecificationAPI,ProductSpecificationUpdateAPI,
    ProductVariationAPI,ProductVariationRetrieveDeleteAPI,
    AttachmentCRUDAPI,AttachmentUpdateDeleteAPI,AttachmentBulkUploadAPI,AttachmentByEntityAPI,
    ProductDetailTypeListCreateAPI,ProductDetailTypeRetrieveUpdateDeleteAPI
)

urlpatterns = [
    # Products
    path("products/data/", ProductCRUDAPI.as_view()),
    path("products/data/<uuid:pk>/", ProductUpdateDeleteAPI.as_view()),

    # Categories
    path("categories/", CategoryCRUDAPI.as_view()),
    path("categories/<uuid:pk>/", CategoryUpdateDeleteAPI.as_view()),

    # Specifications
    path("specifications/", ProductSpecificationAPI.as_view()),
    path("specifications/<uuid:pk>/", ProductSpecificationUpdateAPI.as_view()),

    # Variations
    path("variations/", ProductVariationAPI.as_view()),
    path("variations/<uuid:pk>/", ProductVariationRetrieveDeleteAPI.as_view()),

    # Attachments
    path("attachments/", AttachmentCRUDAPI.as_view()),
    path("attachments/<uuid:pk>/", AttachmentUpdateDeleteAPI.as_view()),
    path("attachments/bulk/", AttachmentBulkUploadAPI.as_view()),
    path("attachments/by-entity/", AttachmentByEntityAPI.as_view()),

    
    path("detail-types/", ProductDetailTypeListCreateAPI.as_view()),
    path("detail-types/<uuid:pk>/", ProductDetailTypeRetrieveUpdateDeleteAPI.as_view()),
]
