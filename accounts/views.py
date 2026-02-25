from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response

from .permissions import IsCustomerOrGuest, IsAdmin
from .models import Role, User, Address
from .serializers import (
    RoleSerializer,
    UserSerializer,
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    AddressSerializer,
)


# ---------------- Register ----------------
class RegisterAPI(generics.CreateAPIView):
    serializer_class = RegisterSerializer


# ---------------- Role CRUD ----------------
class RoleCRUDAPI(generics.ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class RoleUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


# ---------------- User List ----------------
class UserListAPI(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


# ---------------- JWT Login ----------------
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class AddressListCreateAPI(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated:
            return Address.objects.filter(user=self.request.user)
        return Address.objects.none()

    def create(self, request, *args, **kwargs):
        if request.user and request.user.is_authenticated:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(
            {"message": "enter ur detail first"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


# ---------------- Address Retrieve + Update + Delete ----------------
class AddressRetrieveUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated, IsCustomerOrGuest]

    def get_queryset(self):
        # Prevent accessing others' addresses
        return Address.objects.filter(user=self.request.user)
