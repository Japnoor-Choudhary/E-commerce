from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import *
from .serializers import *
from .permissions import HasModelPermission

class ProductCRUDAPI(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return Product.objects.filter(store=self.request.user.store)



class ProductUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return Product.objects.filter(store=self.request.user.store)



from rest_framework.parsers import MultiPartParser, FormParser

class CategoryCRUDAPI(generics.ListCreateAPIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return ProductCategory.objects.filter(store=self.request.user.store)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductCategoryCreateSerializer
        return ProductCategoryResponseSerializer


class CategoryUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, HasModelPermission]

    def get_queryset(self):
        return ProductCategory.objects.filter(store=self.request.user.store)

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
        qs = Attachment.objects.filter(store=self.request.user.store)

        entity_type = self.request.query_params.get("entity_type")
        entity_id = self.request.query_params.get("entity_id")

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



