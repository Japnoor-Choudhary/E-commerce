from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Role
from django.utils import timezone

User = get_user_model()


# ---------------- Permissions ----------------
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "name", "codename"]


# ---------------- Role ----------------
class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Permission.objects.all(),
        source="permissions"
    )

    store_name = serializers.CharField(source="store.name", read_only=True)

    class Meta:
        model = Role
        fields = ["id", "store", "store_name", "name", "permissions", "permission_ids"]


# ---------------- User ----------------
class UserSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "number",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "date_joined",
            "store",
            "store_name",
            "roles",
        ]


# ---------------- Register ----------------
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
            "store",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


# ---------------- JWT Token ----------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            "user": {
                "id": str(self.user.id),
                "email": self.user.email,
                "number": self.user.number,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "is_active": self.user.is_active,
                "is_staff": self.user.is_staff,
                "store": str(self.user.store.id) if self.user.store else None,
                "store_name": self.user.store.name if self.user.store else None,
                "date_joined": self.user.date_joined.isoformat(),
            }
        })
        return data
