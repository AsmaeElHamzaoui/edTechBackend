from rest_framework import serializers
from .models import LearningSession

class LearningSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningSession
        fields = ["id", "document", "start_time", "end_time", "duration_seconds", "created_at"]
        read_only_fields = ["id", "duration_seconds", "created_at"]
