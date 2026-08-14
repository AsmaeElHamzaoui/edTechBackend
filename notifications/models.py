from django.db import models
from django.conf import settings


class Notification(models.Model):

    class Type(models.TextChoices):
        DOCUMENT_READY  = "DOCUMENT_READY",  "Document prêt"
        DOCUMENT_FAILED = "DOCUMENT_FAILED", "Échec du traitement"
        QUIZ_RESULT     = "QUIZ_RESULT",     "Résultat de quiz"
        REVISION_REMINDER = "REVISION_REMINDER", "Rappel de révision"
        RECOMMENDATION  = "RECOMMENDATION",  "Recommandation"
        ADMIN_ACTION    = "ADMIN_ACTION",    "Action administrative"
        GENERIC         = "GENERIC",         "Notification générale"

    class Status(models.TextChoices):
        UNREAD = "UNREAD", "Non lue"
        READ   = "READ",   "Lue"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    notification_type = models.CharField(
        max_length=30,
        choices=Type.choices,
        default=Type.GENERIC
    )

    title   = models.CharField(max_length=255)
    message = models.TextField()

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.UNREAD
    )

    # Métadonnées optionnelles (ex: {"document_id": 5, "quiz_id": 3})
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.notification_type}] {self.title} → {self.user.email}"


class EmailLog(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        SENT    = "SENT",    "Envoyé"
        FAILED  = "FAILED",  "Échoué"

    recipient   = models.EmailField()
    subject     = models.CharField(max_length=255)
    body        = models.TextField()

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )

    error_message = models.TextField(blank=True, default="")

    sent_at    = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.status}] {self.subject} → {self.recipient}"
