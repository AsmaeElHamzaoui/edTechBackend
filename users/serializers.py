from django.contrib.auth import get_user_model
from rest_framework import serializers
from .audit_models import AuditLog


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User

        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
        ]

        read_only_fields = [
            "id",
        ]

    def create(self, validated_data):

        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            role=User.Role.APPRENANT,
            **validated_data
        )

        return user


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer complet du profil utilisateur."""

    documents_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "role", "max_documents", "max_storage_bytes",
            "used_storage_bytes", "documents_count",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_documents_count(self, obj):
        return obj.documents.count()


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer pour l'administration des utilisateurs."""

    documents_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "role", "max_documents", "max_storage_bytes",
            "used_storage_bytes", "documents_count",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "email", "used_storage_bytes",
            "documents_count", "created_at", "updated_at",
        ]

    def get_documents_count(self, obj):
        return obj.documents.count()


class AdminUserUpdateSerializer(serializers.Serializer):
    """Serializer pour modifier rôle et quotas d'un utilisateur."""
    role = serializers.ChoiceField(choices=User.Role.choices, required=False)
    max_documents = serializers.IntegerField(min_value=1, required=False)
    max_storage_bytes = serializers.IntegerField(min_value=1_000_000, required=False)
    is_active = serializers.BooleanField(required=False)


class AuditLogSerializer(serializers.ModelSerializer):
    author_email = serializers.CharField(source="author.email", read_only=True, default="")
    target_email = serializers.CharField(source="target_user.email", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "author_email", "target_email",
            "action", "field_name", "old_value", "new_value",
            "timestamp",
        ]
        read_only_fields = fields