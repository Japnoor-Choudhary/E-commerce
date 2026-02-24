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
    Review,
)
# Import serializers
from .serializers import *
# Custom permission class for model-level permissions
from .permissions import HasModelPermission
import uuid
from django.db.models import Q

# -----------------------------
# Products
# -----------------------------

class ProductCRUDAPI(generics.ListCreateAPIView):
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), HasModelPermission()]

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True)
        if self.request.user.is_authenticated:
            qs = qs.filter(store=self.request.user.store)
        return qs

    def get_serializer_context(self):
        return {"request": self.request}

class ProductUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), HasModelPermission()]

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True)
        if self.request.user.is_authenticated:
            qs = qs.filter(store=self.request.user.store)
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

        try:
            product = Product.objects.select_related(
                "category", "store"
            ).get(
                id=product_id,
                is_active=True
            )
        except Product.DoesNotExist:
            return Product.objects.none()

        return (
            Product.objects.filter(
                category=product.category,
                store=product.store,
                is_active=True
            )
            .exclude(id=product.id)
            .distinct()
            .order_by("-avg_rating", "-created_at")[:8]
        )

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
        qs = ProductCategory.objects.all()
        if self.request.user.is_authenticated:
            qs = qs.filter(store=self.request.user.store)
        return qs

    def get_serializer_class(self):
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
        if self.request.method in ["PUT", "PATCH"]:
            return ProductCategoryUpdateSerializer
        return ProductCategoryResponseSerializer
    
class CategoryHierarchyAPI(generics.ListAPIView):
    serializer_class = ProductCategoryNestedSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = ProductCategory.objects.filter(parent__isnull=True)

        if self.request.user.is_authenticated:
            qs = qs.filter(store=self.request.user.store)

        return qs

# -----------------------------
# Product Variants (Single-Shot Creation)
# -----------------------------
class ProductVariantListCreateAPI(generics.ListCreateAPIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

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
        if self.request.method == "POST":
            return ProductVariantCreateSerializer
        if self.request.user.is_authenticated:
            return ProductVariantPrivateSerializer
        return ProductVariantPublicSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        variants = serializer.save()

        return Response(
            ProductVariantPrivateSerializer(
                variants,
                many=True,
                context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED
        )

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
    serializer_class = AttachmentSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), HasModelPermission()]

    def get_queryset(self):
        qs = Attachment.objects.all()
        if self.request.user.is_authenticated:
            qs = qs.filter(store=self.request.user.store)
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
    permission_classes = [AllowAny]
    def get_queryset(self):
        return Review.objects.filter(
            product_id=self.kwargs["product_id"],
            is_deleted=False,
            is_hidden=False
        ).select_related("user", "product")


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
                product.variants.first().price if product.variants.exists() else "",
                product.is_active,
                ", ".join(product.categories.values_list("name", flat=True)),
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
    permission_classes = [AllowAny]
    serializer_class = ProductVariantPublicSerializer

    def get_queryset(self):
        qs = ProductVariant.objects.select_related(
            "product",
            "product__brand"
        ).prefetch_related(
            "options",
            "product__categories"
        ).filter(product__is_active=True)

        # CATEGORY filter (OR logic)
        category_ids = self.request.query_params.get("category")
        if category_ids:
            q_cat = Q()
            for cid in category_ids.split(","):
                q_cat |= Q(product__categories__id=cid)
            qs = qs.filter(q_cat)

        # BRAND filter (OR logic)
        brand_ids = self.request.query_params.get("brand")
        if brand_ids:
            qs = qs.filter(product__brand_id__in=brand_ids.split(","))

        # PRICE
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)

        # VARIANT OPTIONS (size/color) – OR logic, case-insensitive
        for key in ["color", "size"]:
            values = self.request.query_params.get(key)
            if values:
                q_opt = Q()
                for v in values.split(","):
                    q_opt |= Q(options__key__iexact=key, options__value__iexact=v.strip())
                qs = qs.filter(q_opt)

        return qs.distinct()



