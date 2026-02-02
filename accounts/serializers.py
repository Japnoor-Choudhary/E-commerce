from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Role,Address
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

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


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
    confirm_password = serializers.CharField(write_only=True, required=False)
    is_customer = serializers.BooleanField(default=False)
    is_guest_user = serializers.BooleanField(default=False)

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
            "is_customer",
            "is_guest_user",
        )
        extra_kwargs = {"password": {"write_only": True, "required": False}}

    def validate(self, attrs):
        is_customer = attrs.get("is_customer", False)
        is_guest = attrs.get("is_guest_user", False)

        # Customers must have password
        if is_customer and not attrs.get("password"):
            raise serializers.ValidationError("Password is required for customer registration")
        
        # Password confirmation check
        if attrs.get("password") and attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError("Passwords do not match")

        # Guest user must have at least email or number
        if is_guest and not (attrs.get("email") or attrs.get("number")):
            raise serializers.ValidationError("Email or phone number is required for guest users")

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        validated_data.pop("confirm_password", None)
        is_customer = validated_data.pop("is_customer", False)
        is_guest = validated_data.pop("is_guest_user", False)

        # Create user
        user = User.objects.create_user(**validated_data)

        if password:
            user.set_password(password)
            user.save()

        # Assign default role for guest/customer
        if is_guest or is_customer:
            default_role = Role.objects.filter(name="Customer").first()
            if default_role:
                user.roles.add(default_role)
                user.save()

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
