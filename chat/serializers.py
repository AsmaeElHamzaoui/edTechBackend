from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = [
            "id",
            "role",
            "content",
            "created_at",
        ]


class ConversationSerializer(serializers.ModelSerializer):

    messages = MessageSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Conversation
        fields = [
            "id",
            "document",
            "title",
            "messages",
            "created_at",
            "updated_at",
        ]


class AskQuestionSerializer(serializers.Serializer):

    question = serializers.CharField(
        required=True,
        allow_blank=False
    )

    document_id = serializers.IntegerField(
        required=True
    )

    conversation_id = serializers.IntegerField(
        required=False,
        allow_null=True
    )