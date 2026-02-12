import csv
# DRF generic views for CRUD operations
from rest_framework import generics, status, permissions
# Authentication permission
from rest_framework.permissions import IsAuthenticated,AllowAny
# Standard DRF response
from rest_framework.response import Response
# Parsers to handle JSON + file uploads
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
# Permission error
from rest_framework.exceptions import PermissionDenied
# Used for CSV export response
from django.http import HttpResponse
# Import all models from current app
from .models import(
    Product,
    ProductCategory,
    ProductVariant,
    ProductVariantOption,
    Attachment,
    Brand,
    Review
)
# Import serializers
from .serializers import *
# Custom permission class for model-level permissions
from .permissions import HasModelPermission
import uuid
from django.db.models import Q
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from .utils import get_descendant_category_ids

# -----------------------------
# Products
# -----------------------------
class ProductCRUDAPI(generics.ListCreateAPIView):
    """
    GET  -> List all products of logged-in user's store
    POST -> Create a new product for user's store (supports nested variants & options)
    """

    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), HasModelPermission()]

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True)
        if self.request.user.is_authenticated:
            return qs.filter(store=self.request.user.store)
        return qs

    def perform_create(self, serializer):
        # Automatically assign the store from the logged-in user
        serializer.save(store=self.request.user.store)

    def get_serializer_context(self):
        return {"request": self.request}



class ProductUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    -> Retrieve a single product
    PUT    -> Update product
    PATCH  -> Partial update
    DELETE -> Delete product
    """

    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), HasModelPermission()]

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True)

        if self.request.user.is_authenticated:
            return qs.filter(store=self.request.user.store)

        return qs


    def get_serializer_context(self):
        return {"request": self.request}



class RelatedProductListAPI(generics.ListAPIView):
    """
    Lists related products based on:
    - same category
    - same subcategories
    - excludes current product
    """

    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        product_id = self.kwargs["product_id"]

        # Ensure product exists and is active
        try:
            product = Product.objects.select_related(
                "primary_category", "store"
            ).get(
                id=product_id,
                is_active=True
            )
        except Product.DoesNotExist:
            return Product.objects.none()

        # Collect category + subcategories
        category_ids = [product.primary_category.id]
        subcategories = product.primary_category.subcategories.all()
        category_ids += [c.id for c in subcategories]

        # Fetch related products from SAME STORE
        qs = Product.objects.filter(
            store=product.store,
            is_active=True,
            primary_category__id__in=category_ids
        ).exclude(id=product.id)

        return qs.order_by("-avg_rating", "-created_at")[:8]




# -----------------------------
# Product Categories
# -----------------------------

class CategoryCRUDAPI(generics.ListCreateAPIView):
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), HasModelPermission()]

    def get_queryset(self):
        qs = ProductCategory.objects.filter(parent=None)

        if self.request.user.is_authenticated:
            return qs.filter(store=self.request.user.store)

        return qs

    def get_serializer_class(self):
        """
        Use different serializers for:
        - POST (create)
        - GET (response with nested data)
        """
        if self.request.method == "POST":
            return ProductCategoryCreateSerializer
        return ProductCategoryResponseSerializer


class CategoryUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), HasModelPermission()]

    def get_queryset(self):
        qs = ProductCategory.objects.all()

        if self.request.user.is_authenticated:
            return qs.filter(store=self.request.user.store)

        return qs

    def get_serializer_class(self):
        """
        Update uses update serializer,
        retrieve uses response serializer.
        """
        if self.request.method in ["PUT", "PATCH"]:
            return ProductCategoryUpdateSerializer
        return ProductCategoryResponseSerializer



# -----------------------------
# Product Variants (Single-Shot Creation)
# -----------------------------
class ProductVariantListCreateAPI(generics.ListCreateAPIView):
    """
    GET  -> Public + private variant listing
    POST -> Bulk create (auth only)
    """

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), HasModelPermission()]

    def get_queryset(self):
        qs = ProductVariant.objects.all()

        # 🔐 Store owner sees only their store data
        if self.request.user.is_authenticated:
            return qs.filter(product__store=self.request.user.store)

        # 🌍 Public sees all active variants
        return qs

    def get_serializer_class(self):
        # CREATE
        if self.request.method == "POST":
            return ProductVariantCreateSerializer

        # READ
        if self.request.user.is_authenticated:
            return ProductVariantPrivateSerializer

        return ProductVariantPublicSerializer

    def get_serializer_context(self):
        return {"request": self.request}


class ProductVariantRetrieveUpdateDeleteAPI(
    generics.RetrieveUpdateDestroyAPIView
):
    """
    GET    -> Public / Private retrieve
    PUT    -> Auth only
    DELETE -> Auth only
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), HasModelPermission()]

    def get_queryset(self):
        qs = ProductVariant.objects.all()

        if self.request.user.is_authenticated:
            return qs.filter(product__store=self.request.user.store)

        return qs

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProductVariantSerializer  # your existing update logic

        if self.request.user.is_authenticated:
            return ProductVariantPrivateSerializer

        return ProductVariantPublicSerializer

    def get_serializer_context(self):
        return {"request": self.request}
# -----------------------------
# Varaiant Options
# -----------------------------

from rest_framework.permissions import AllowAny, IsAuthenticated

class ProductVariantOptionListAPI(generics.ListAPIView):
    """
    List variant options.
    Supports filtering by variant_id.
    """

    serializer_class = ProductVariantOptionSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), HasModelPermission()]

    def get_queryset(self):
        qs = ProductVariantOption.objects.all()

        # Auth users → restrict to their store
        if self.request.user.is_authenticated:
            qs = qs.filter(
                variant__product__store=self.request.user.store
            )

        # Optional filter by variant
        variant_id = self.request.query_params.get("variant_id")
        if variant_id:
            qs = qs.filter(variant_id=variant_id)

        return qs


class ProductVariantOptionUpdateDeleteAPI(
    generics.RetrieveUpdateDestroyAPIView
):
    """
    Retrieve / Update / Delete variant option.
    """

    serializer_class = ProductVariantOptionSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), HasModelPermission()]

    def get_queryset(self):
        qs = ProductVariantOption.objects.all()

        if self.request.user.is_authenticated:
            qs = qs.filter(
                variant__product__store=self.request.user.store
            )

        return qs



# -----------------------------
# Attachments
# -----------------------------
class AttachmentCRUDAPI(generics.ListCreateAPIView):
    """
    GET  -> Public + private attachment list
    POST -> Upload attachment (auth only)
    """

    serializer_class = AttachmentSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), HasModelPermission()]

    def get_queryset(self):
        qs = Attachment.objects.all()

        # 🔐 Store owner → only their attachments
        if self.request.user.is_authenticated:
            return qs.filter(store=self.request.user.store)

        # 🌍 Public → all attachments (read-only)
        return qs

    def perform_create(self, serializer):
        serializer.save(store=self.request.user.store)


class AttachmentUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    -> Public
    PUT    -> Auth only
    DELETE -> Auth only
    """

    serializer_class = AttachmentSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), HasModelPermission()]

    def get_queryset(self):
        qs = Attachment.objects.all()

        if self.request.user.is_authenticated:
            return qs.filter(store=self.request.user.store)

        return qs


class AttachmentBulkUploadAPI(generics.CreateAPIView):
    """
    Upload multiple attachments in one request.
    """

    serializer_class = AttachmentBulkUploadSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attachments = []

        for file in serializer.validated_data["files"]:
            attachments.append(
                Attachment.objects.create(
                    store=request.user.store,
                    entity_type=serializer.validated_data["entity_type"],
                    entity_id=serializer.validated_data["entity_id"],
                    file=file
                )
            )

        return Response(
            {
                "message": "Attachments uploaded successfully",
                "count": len(attachments)
            },
            status=status.HTTP_201_CREATED
        )



class AttachmentByEntityAPI(generics.ListAPIView):
    """
    Fetch attachments by entity_type and entity_id.
    """

    serializer_class = AttachmentSerializer

    def get_permissions(self):
        return [AllowAny()]

    def get_queryset(self):
        qs = Attachment.objects.all()

        entity_type = self.request.query_params.get("entity_type")
        entity_id = self.request.query_params.get("entity_id")

        if entity_type:
            qs = qs.filter(entity_type=entity_type)
        if entity_id:
            qs = qs.filter(entity_id=entity_id)

        return qs

# -----------------------------
# Product Detail Type
# -----------------------------
class ProductDetailTypeListCreateAPI(generics.ListCreateAPIView):
    """
    List & create product detail types.

    Product detail types define attribute categories for products
    such as Material, Fabric, Warranty, or Sleeve Type.
    These types are later used to attach specifications to products.
    """
    queryset = ProductDetailType.objects.all()
    serializer_class = ProductDetailTypeSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

class ProductDetailTypeRetrieveUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update & delete a product detail type.

    Allows admins to manage existing product detail types
    including editing their names or removing unused ones.
    """
    queryset = ProductDetailType.objects.all()
    serializer_class = ProductDetailTypeSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    
# =====================================================
# Reviews 
# =====================================================
    
class ReviewCreateAPI(generics.CreateAPIView):
    """
    Create a product review.
    """

    serializer_class = ReviewCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {"request": self.request}

    
class ProductReviewListAPI(generics.ListAPIView):
    """
    List visible reviews for a product.
    """

    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(
            product_id=self.kwargs["product_id"],
            is_deleted=False,
            is_hidden=False
        )


class ReviewUpdateAPI(generics.UpdateAPIView):
    """
    Update user's own review within allowed time.
    """

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(
            user=self.request.user,
            is_deleted=False
        )

    def perform_update(self, serializer):
        review = self.get_object()
        if not review.can_edit():
            raise PermissionDenied("Review edit time expired")
        serializer.save()


class ReviewDeleteAPI(generics.DestroyAPIView):
    """
    Soft delete a review.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()


class ReviewHelpfulVoteAPI(generics.CreateAPIView):
    """
    Mark a review as helpful.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, review_id):
        ReviewHelpfulVote.objects.get_or_create(
            review_id=review_id,
            user=request.user
        )
        return Response({"message": "Marked helpful"})



# =====================================================
# Brands 
# =====================================================

class BrandListCreateAPI(generics.ListCreateAPIView):
    """
    GET  -> Public + private brand list
    POST -> Create brand (auth only)
    """

    serializer_class = BrandSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Brand.objects.all()

        # 🔐 Store owner sees only their brands
        if self.request.user.is_authenticated:
            return qs.filter(store=self.request.user.store)

        # 🌍 Public sees all brands
        return qs

    def perform_create(self, serializer):
        serializer.save(store=self.request.user.store)



class BrandRetrieveUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    -> Public + private retrieve
    PUT    -> Auth only
    DELETE -> Auth only
    """

    serializer_class = BrandSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Brand.objects.all()

        # 🔐 Store owner restriction
        if self.request.user.is_authenticated:
            return qs.filter(store=self.request.user.store)

        # 🌍 Public can retrieve any brand
        return qs



# =====================================================
# Product Import / Export
# =====================================================
class ProductExportAPI(generics.GenericAPIView):
    """
    Export products as JSON or CSV.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get(self, request):
        store = request.user.store
        format_type = request.query_params.get("format", "json")

        products = Product.objects.filter(store=store)

        if format_type == "csv":
            return self.export_csv(products)

        serializer = self.get_serializer(
            products,
            many=True,
            context={"request": request}
        )
        return Response(serializer.data)


    def export_csv(self, products):
        """
        Export products as CSV file.
        """

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="products.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "name",
            "price",
            "is_active",
            "category",
            "brand"
        ])

        for product in products:
            writer.writerow([
                product.name,
                product.price,
                product.is_active,
                product.primary_category.name if product.primary_category else "",
                product.brand.name if product.brand else "",
            ])

        return response



class ProductImportAPI(generics.CreateAPIView):
    """
    Import products via JSON or CSV.
    """

    serializer_class = ProductImportSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser]

    def create(self, request, *args, **kwargs):

        # JSON import
        if isinstance(request.data, dict) and "products" in request.data:
            products = request.data["products"]

        # CSV import
        elif "file" in request.FILES:
            file = request.FILES["file"]
            reader = csv.DictReader(
                file.read().decode("utf-8").splitlines()
            )
            products = list(reader)

        else:
            return Response(
                {"detail": "Invalid import format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        created = 0
        errors = []

        for index, product_data in enumerate(products):
            serializer = self.get_serializer(
                data=product_data,
                context={"request": request}
            )

            if serializer.is_valid():
                serializer.save()
                created += 1
            else:
                errors.append({
                    "row": index + 1,
                    "errors": serializer.errors
                })

        return Response(
            {
                "created": created,
                "errors": errors
            },
            status=status.HTTP_201_CREATED
        )



class ProductVariantFilterAPI(generics.ListAPIView):
    """
    Fetch product variations with filters:
    - category
    - brand
    - color
    - price range
    - rating
    """

    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = ProductVariant.objects.select_related(
            "product", "product__primary_category"
        )

        # -------------------------
        # Category filter (recursive)
        # -------------------------
        category_id = self.request.query_params.get("category_id")
        if category_id:
            category_id = category_id.rstrip("/")

            try:
                category_uuid = uuid.UUID(category_id)
            except (ValueError, TypeError):
                return qs.none()

            category = ProductCategory.objects.filter(
                id=category_uuid
            ).first()

            if not category:
                return qs.none()

            category_ids = get_descendant_category_ids(category)

            qs = qs.filter(
                product__primary_category_id__in=category_ids
            )

        # -------------------------
        # Brand filter
        # -------------------------
        brand_id = self.request.query_params.get("brand_id")
        if brand_id:
            qs = qs.filter(product__brand_id=brand_id)

        # -------------------------
        # Color filter (variant option)
        # -------------------------
        color_ids = self.request.query_params.get("color")  # 👈 match URL

        if color_ids:
            try:
                color_uuid_list = [
                    uuid.UUID(cid.strip())
                    for cid in color_ids.split(",")
                ]
            except ValueError:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"color": "Invalid UUID"})

            qs = qs.filter(
                options__id__in=color_uuid_list,
                options__key="color"   # 🔥 VERY IMPORTANT
            )

        return qs.distinct()

        # -------------------------
        # Price filter
        # -------------------------
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")

        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)

        # -------------------------
        # Rating filter
        # -------------------------
        min_rating = self.request.query_params.get("min_rating")
        if min_rating:
            qs = qs.filter(product__avg_rating__gte=min_rating)

        return qs.distinct().order_by("-product__avg_rating", "-created_at")

    def get_serializer_class(self):
        # Logged-in store owner
        if self.request.user.is_authenticated:
            return ProductVariantPrivateSerializer

        # Public
        return ProductVariantPublicSerializer

    def get_serializer_context(self):
        return {"request": self.request}
