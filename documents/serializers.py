from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):

    uploaded_by = serializers.ReadOnlyField(
        source="uploaded_by.email"
    )

    class Meta:

        model = Document

        fields = [
            "id",
            "title",
            "status",
            "file",
            "uploaded_by",
            "uploaded_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "uploaded_by",
            "uploaded_at",
            "updated_at",
        ]