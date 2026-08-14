from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """
    Journal des modifications administratives.
    Chaque modification de rôle/quota est tracée ici.
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_actions_performed"
    )

    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="audit_actions_received"
    )

    action = models.CharField(max_length=100)

    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True, default="")
    new_value = models.TextField(blank=True, default="")

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.timestamp}] {self.author} → {self.action} on {self.target_user}"
