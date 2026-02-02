from rest_framework import serializers
from .models import Company, Store


class StoreNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = (
            'id',
            'name',
            'slug',
            'email',
            'phone',
            'address',
            'is_primary',
            'is_active',
            'created_at',
            'updated_at',
        )

# serializers.py
from rest_framework import serializers
from .models import Company, Store


class CompanyNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = (
            'id',
            'name',
            'slug',
            'description',
            'address',
            'is_active',
            'created_at',
            'updated_at',
        )

# =====================================================
# Company Serializer
# =====================================================
class CompanySerializer(serializers.ModelSerializer):
    stores = StoreNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = (
            'id',
            'name',
            'slug',
            'description',
            'address',
            'is_active',
            'created_at',
            'updated_at',
            'stores',
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')



# =====================================================
# Store Serializer
# =====================================================
class StoreSerializer(serializers.ModelSerializer):
    # detailed company response (read-only)
    company_detail = CompanyNestedSerializer(source='company', read_only=True)

    class Meta:
        model = Store
        fields = (
            'id',
            'company',          # write by UUID
            'company_detail',   # read detailed company
            'name',
            'slug',
            'email',
            'phone',
            'address',
            'is_primary',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')


