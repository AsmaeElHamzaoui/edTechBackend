from rest_framework import serializers
from .models import Notification, EmailLog


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "notification_type", "title", "message", "status", "metadata", "created_at"]
        read_only_fields = fields


class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = ["id", "recipient", "subject", "status", "error_message", "sent_at", "created_at"]
        read_only_fields = fields
