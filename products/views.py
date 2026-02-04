from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import *
from .serializers import *
from .permissions import HasModelPermission

# -----------------------------
# Products
# -----------------------------
class ProductCRUDAPI(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return Product.objects.filter(store=self.request.user.store)

    def perform_create(self, serializer):
        serializer.save(store=self.request.user.store)

class ProductUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return Product.objects.filter(store=self.request.user.store)

# -----------------------------
# Product Categories
# -----------------------------
class CategoryCRUDAPI(generics.ListCreateAPIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return ProductCategory.objects.filter(store=self.request.user.store)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductCategoryCreateSerializer
        return ProductCategoryResponseSerializer

    def perform_create(self, serializer):
        serializer.save(store=self.request.user.store)

class CategoryUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return ProductCategory.objects.filter(store=self.request.user.store)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProductCategoryUpdateSerializer
        return ProductCategoryResponseSerializer

# -----------------------------
# Product Specifications
# -----------------------------
class ProductSpecificationAPI(generics.ListCreateAPIView):
    serializer_class = ProductSpecificationSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return ProductSpecification.objects.filter(product__store=self.request.user.store)

    def perform_create(self, serializer):
        serializer.save()

class ProductSpecificationUpdateAPI(generics.RetrieveUpdateAPIView):
    serializer_class = ProductSpecificationSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return ProductSpecification.objects.filter(product__store=self.request.user.store)

# -----------------------------
# Product Variants (Single-Shot Creation)
# -----------------------------
class ProductVariantListCreateAPI(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return ProductVariant.objects.filter(
            product__store=self.request.user.store
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductVariantCreateSerializer
        return ProductVariantSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variants = serializer.save()  # ← list of ProductVariant

        return Response(
            {
                "message": "Variants created successfully",
                "count": len(variants),
                "variant_ids": [v.id for v in variants],
            },
            status=status.HTTP_201_CREATED,
        )

class ProductVariantRetrieveUpdateDeleteAPI(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return ProductVariant.objects.filter(
            product__store=self.request.user.store
        )

# -----------------------------
# Varaiant Options
# -----------------------------

class ProductVariantOptionListAPI(generics.ListAPIView):
    serializer_class = ProductVariantOptionSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        qs = ProductVariantOption.objects.filter(
            variant__product__store=self.request.user.store
        )

        variant_id = self.request.query_params.get("variant_id")
        if variant_id:
            qs = qs.filter(variant_id=variant_id)

        return qs

class ProductVariantOptionUpdateDeleteAPI(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = ProductVariantOptionSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return ProductVariantOption.objects.filter(
            variant__product__store=self.request.user.store
        )

# -----------------------------
# Attachments
# -----------------------------
class AttachmentCRUDAPI(generics.ListCreateAPIView):
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return Attachment.objects.filter(store=self.request.user.store)

    def perform_create(self, serializer):
        serializer.save(store=self.request.user.store)

class AttachmentUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return Attachment.objects.filter(store=self.request.user.store)

class AttachmentBulkUploadAPI(generics.CreateAPIView):
    serializer_class = AttachmentBulkUploadSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachments = []
        for file in serializer.validated_data["files"]:
            attachments.append(Attachment.objects.create(
                store=request.user.store,
                entity_type=serializer.validated_data["entity_type"],
                entity_id=serializer.validated_data["entity_id"],
                file=file
            ))
        return Response({
            "message": "Attachments uploaded successfully",
            "count": len(attachments)
        }, status=status.HTTP_201_CREATED)

class AttachmentByEntityAPI(generics.ListAPIView):
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        qs = Attachment.objects.filter(store=self.request.user.store)
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
    queryset = ProductDetailType.objects.all()
    serializer_class = ProductDetailTypeSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

class ProductDetailTypeRetrieveUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductDetailType.objects.all()
    serializer_class = ProductDetailTypeSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
