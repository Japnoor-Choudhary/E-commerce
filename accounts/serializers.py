from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Role
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str


User = get_user_model()

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "name", "codename"]

class RoleSerializer(serializers.ModelSerializer):
    # Accept IDs in request
    permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all()
    )

    class Meta:
        model = Role
        fields = ["id", "name", "permissions"]

    def to_representation(self, instance):
        """
        Convert permission IDs → full permission objects in response
        """
        data = super().to_representation(instance)
        data["permissions"] = [
            {
                "id": p.id,
                "name": p.name,
                "codename": p.codename
            }
            for p in instance.permissions.all()
        ]
        return data



class UserSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)  # if you have ManyToMany with Role

    class Meta:
        model = User
        fields = ["id", "email", "number", "first_name", "last_name", "is_active", "is_staff", "date_joined", "roles"]



class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "number",
            "first_name",
            "last_name",
            "password",
            "confirm_password",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        user = User.objects.create_user(**validated_data)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user details to the response
        data.update({
            "user": {
                "id": str(self.user.id),
                "email": self.user.email,
                "number": self.user.number,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "is_active": self.user.is_active,
                "is_staff": self.user.is_staff,
                "date_joined": self.user.date_joined.isoformat()
            }
        })
        return data


# User = get_user_model()


# class ForgotPasswordSerializer(serializers.Serializer):
#     email = serializers.EmailField()

#     def validate_email(self, value):
#         if not User.objects.filter(email=value).exists():
#             raise serializers.ValidationError("User with this email does not exist.")
#         return value


# class ResetPasswordSerializer(serializers.Serializer):
#     uid = serializers.CharField()
#     token = serializers.CharField()
#     new_password = serializers.CharField(min_length=8)

#     def validate(self, attrs):
#         try:
#             uid = force_str(urlsafe_base64_decode(attrs["uid"]))
#             user = User.objects.get(pk=uid)
#         except Exception:
#             raise serializers.ValidationError("Invalid UID")

#         if not PasswordResetTokenGenerator().check_token(user, attrs["token"]):
#             raise serializers.ValidationError("Invalid or expired token")

#         attrs["user"] = user
#         return attrs
