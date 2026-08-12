from django.db import models
from django.conf import settings
from documents.models import Document

class LearningSession(models.Model):
    """
    Trace le temps passé par un apprenant sur un document spécifique.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="learning_sessions")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="learning_sessions")
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_seconds = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calcule la durée automatiquement
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_seconds = int(delta.total_seconds())
        super().save(*args, **kwargs)

