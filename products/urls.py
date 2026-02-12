from django.urls import path
from .views import *

urlpatterns = [
    # -----------------------------
    # Products
    # -----------------------------
    path("products/data/", ProductCRUDAPI.as_view(), name="product-list-create"),
    path("products/data/<uuid:pk>/", ProductUpdateDeleteAPI.as_view(), name="product-detail"),
    path("related-product/<uuid:product_id>/",RelatedProductListAPI.as_view(),name="related-products"),


    # -----------------------------
    # Products
    # -----------------------------    
    path("variations/filter/",ProductVariantFilterAPI.as_view(),name="variant-filter"),

    # -----------------------------
    # Categories
    # -----------------------------
    path("categories/", CategoryCRUDAPI.as_view(), name="category-list-create"),
    path("categories/<uuid:pk>/", CategoryUpdateDeleteAPI.as_view(), name="category-detail"),

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
    
    # -----------------------------
    # Reviews
    # -----------------------------
    path("reviews/", ReviewCreateAPI.as_view()),
    path("product-reviews/<uuid:product_id>/", ProductReviewListAPI.as_view()),
    path("reviews/<uuid:pk>/", ReviewUpdateAPI.as_view()),
    path("delete-reviews/<uuid:pk>/", ReviewDeleteAPI.as_view()),
    path("reviews-helpful/<uuid:review_id>/", ReviewHelpfulVoteAPI.as_view()),
    
    # -----------------------------
    # Brands
    # -----------------------------
    path("brands/", BrandListCreateAPI.as_view(), name="brand-list-create"),
    path("brands/<uuid:pk>/", BrandRetrieveUpdateDeleteAPI.as_view(), name="brand-detail"),
    
    # -----------------------------
    # Product Import/Export
    # -----------------------------
    path("products-export/", ProductExportAPI.as_view()),
    path("products-import/", ProductImportAPI.as_view()),
]
