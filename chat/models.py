from django.db import models
from django.conf import settings
from documents.models import Document


class Conversation(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations"
    )

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="conversations",
        null=True,
        blank=True
    )

    title = models.CharField(
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title or f"Conversation {self.id}"

class Message(models.Model):

    ROLE_CHOICES = [
        ("USER", "User"),
        ("ASSISTANT", "Assistant"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.role} - Conversation {self.conversation_id}"