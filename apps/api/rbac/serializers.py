from rest_framework import serializers

from rbac.models import Permission, Role, RoleBinding


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "codename", "description"]
        read_only_fields = ["id"]


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all(), required=False
    )

    class Meta:
        model = Role
        fields = ["id", "name", "tenant", "permissions", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoleBindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleBinding
        fields = ["id", "user", "role", "tenant", "company", "store", "created_at"]
        read_only_fields = ["id", "created_at"]
