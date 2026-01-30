from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Permission
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from .models import Role, User
from .serializers import (
    RoleSerializer,
    UserSerializer,
    RegisterSerializer,
    # ForgotPasswordSerializer, 
    # ResetPasswordSerializer
)
from .permissions import IsAdmin
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.response import Response

class RegisterAPI(generics.CreateAPIView):
    serializer_class = RegisterSerializer


class RoleCRUDAPI(generics.ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class RoleUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class UserListAPI(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# class ForgotPasswordAPI(generics.GenericAPIView):
#     serializer_class = ForgotPasswordSerializer

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         user = User.objects.get(email=serializer.validated_data["email"])

#         uid = urlsafe_base64_encode(force_bytes(user.pk))
#         token = PasswordResetTokenGenerator().make_token(user)

#         reset_link = f"{settings.FRONTEND_URL}/reset-password/?uid={uid}&token={token}"

#         send_mail(
#             subject="Reset your password",
#             message=f"Click the link to reset your password:\n{reset_link}",
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[user.email],
#         )

#         return Response(
#             {"message": "Password reset link sent to email"},
#             status=status.HTTP_200_OK
#         )


# class ResetPasswordAPI(generics.GenericAPIView):
#     serializer_class = ResetPasswordSerializer

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         user = serializer.validated_data["user"]
#         user.set_password(serializer.validated_data["new_password"])
#         user.save()

#         return Response(
#             {"message": "Password reset successful"},
#             status=status.HTTP_200_OK
#         )
