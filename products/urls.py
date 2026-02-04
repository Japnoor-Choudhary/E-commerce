from django.urls import path
from .views import *

urlpatterns = [
    # -----------------------------
    # Products
    # -----------------------------
    path("products/data/", ProductCRUDAPI.as_view(), name="product-list-create"),
    path("products/data/<uuid:pk>/", ProductUpdateDeleteAPI.as_view(), name="product-detail"),

    # -----------------------------
    # Categories
    # -----------------------------
    path("categories/", CategoryCRUDAPI.as_view(), name="category-list-create"),
    path("categories/<uuid:pk>/", CategoryUpdateDeleteAPI.as_view(), name="category-detail"),

    # -----------------------------
    # Specifications
    # -----------------------------
    path("specifications/", ProductSpecificationAPI.as_view(), name="specification-list-create"),
    path("specifications/<uuid:pk>/", ProductSpecificationUpdateAPI.as_view(), name="specification-update"),

    # -----------------------------
    # Variants (Single-Shot Create + List)
    # -----------------------------
    path("variations/", ProductVariantListCreateAPI.as_view(), name="variant-list-create"),
    path("variations/<uuid:pk>/", ProductVariantRetrieveUpdateDeleteAPI.as_view(), name="variant-detail"),

# -----------------------------
# Variant Options
# -----------------------------
    path("variant-options/",ProductVariantOptionListAPI.as_view(),name="variant-option-list"),
    path("variant-options/<uuid:pk>/",ProductVariantOptionUpdateDeleteAPI.as_view(),name="variant-option-detail"),

    # -----------------------------
    # Attachments
    # -----------------------------
    path("attachments/", AttachmentCRUDAPI.as_view(), name="attachment-list-create"),
    path("attachments/<uuid:pk>/", AttachmentUpdateDeleteAPI.as_view(), name="attachment-detail"),
    path("attachments/bulk/", AttachmentBulkUploadAPI.as_view(), name="attachment-bulk-upload"),
    path("attachments/by-entity/", AttachmentByEntityAPI.as_view(), name="attachment-by-entity"),

    # -----------------------------
    # Detail Types
    # -----------------------------
    path("detail-types/", ProductDetailTypeListCreateAPI.as_view(), name="detail-type-list-create"),
    path("detail-types/<uuid:pk>/", ProductDetailTypeRetrieveUpdateDeleteAPI.as_view(), name="detail-type-detail"),
]
