from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import *
from .serializers import *
from .permissions import HasModelPermission

class ProductCRUDAPI(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]


class ProductUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]


from rest_framework.parsers import MultiPartParser, FormParser

class CategoryCRUDAPI(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductCategoryCreateSerializer
        return ProductCategoryResponseSerializer

class CategoryUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductCategory.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProductCategoryUpdateSerializer
        return ProductCategoryResponseSerializer



class ProductSpecificationAPI(generics.ListCreateAPIView):
    queryset = ProductSpecification.objects.all()
    serializer_class = ProductSpecificationSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]


class ProductSpecificationUpdateAPI(generics.RetrieveUpdateAPIView):
    queryset = ProductSpecification.objects.all()
    serializer_class = ProductSpecificationSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]


class ProductVariationAPI(generics.ListAPIView):
    queryset = ProductVariation.objects.all()
    serializer_class = ProductVariationSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    
class ProductVariationRetrieveDeleteAPI(generics.RetrieveDestroyAPIView):
    queryset = ProductVariation.objects.all()
    serializer_class = ProductVariationSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]


class AttachmentCRUDAPI(generics.ListCreateAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]


class AttachmentUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    
class AttachmentBulkUploadAPI(generics.CreateAPIView):
    serializer_class = AttachmentBulkUploadSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachments = serializer.save()

        return Response(
            {
                "message": "Attachments uploaded successfully",
                "count": len(attachments),
            },
            status=status.HTTP_201_CREATED
        )

class AttachmentByEntityAPI(generics.ListAPIView):
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        """
        Filter attachments by entity_type and optionally entity_id
        Example query params:
        /attachments/by-entity/?entity_type=product&entity_id=<uuid>
        """
        entity_type = self.request.query_params.get("entity_type")
        entity_id = self.request.query_params.get("entity_id")

        qs = Attachment.objects.all()

        if entity_type:
            qs = qs.filter(entity_type=entity_type)
        if entity_id:
            qs = qs.filter(entity_id=entity_id)

        return qs
    
class ProductDetailTypeListCreateAPI(generics.ListCreateAPIView):
    queryset = ProductDetailType.objects.all()
    serializer_class = ProductDetailTypeSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

class ProductDetailTypeRetrieveUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductDetailType.objects.all()
    serializer_class = ProductDetailTypeSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]



